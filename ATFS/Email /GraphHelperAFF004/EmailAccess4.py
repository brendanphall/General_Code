import msal
import requests
import os
import json
from datetime import datetime
import time
import sys

# === CONFIGURATION ===
CLIENT_ID = '94fac862-ac02-434a-b77c-13b75d5f45f4'
TENANT_ID = '31c26211-2687-4fb9-94dd-8dcb92e5320d'
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"

# testmailbox credentials
TESTMAILBOX_EMAIL = "testmailbox@sewall.com"

# For PyCharm development - you can temporarily hardcode for testing
# TODO: Remove this before production deployment!
TESTMAILBOX_PASSWORD = os.environ.get('TESTMAILBOX_PASSWORD', 'Elephant_Matchstick_99')

if not TESTMAILBOX_PASSWORD:
    print("❌ ERROR: TESTMAILBOX_PASSWORD not available!")
    sys.exit(1)

# Delegated permissions (user context)
# Start with read-only to avoid consent issues
SCOPES = ["https://graph.microsoft.com/Mail.Read", "https://graph.microsoft.com/User.Read"]

# Token cache file for refresh tokens
TOKEN_CACHE_FILE = "token_cache.json"


# === TOKEN MANAGEMENT ===
class TokenManager:
    def __init__(self):
        self.app = msal.PublicClientApplication(
            client_id=CLIENT_ID,
            authority=AUTHORITY,
            token_cache=self._load_cache()
        )

    def _load_cache(self):
        """Load token cache from file"""
        cache = msal.SerializableTokenCache()
        if os.path.exists(TOKEN_CACHE_FILE):
            try:
                with open(TOKEN_CACHE_FILE, 'r') as f:
                    cache.deserialize(f.read())
                print("📁 Loaded token cache from file")
            except Exception as e:
                print(f"⚠️ Could not load token cache: {e}")
        return cache

    def _save_cache(self):
        """Save token cache to file"""
        if self.app.token_cache.has_state_changed:
            try:
                with open(TOKEN_CACHE_FILE, 'w') as f:
                    f.write(self.app.token_cache.serialize())
                print("💾 Token cache saved")
            except Exception as e:
                print(f"⚠️ Could not save token cache: {e}")

    def get_token(self):
        """Get access token (tries silent first, then username/password)"""
        # Try to get token silently first (using refresh token)
        accounts = self.app.get_accounts()
        if accounts:
            print("🔄 Attempting silent token acquisition...")
            result = self.app.acquire_token_silent(SCOPES, account=accounts[0])
            if result and "access_token" in result:
                print("✅ Got token silently (using refresh token)")
                self._save_cache()
                return result["access_token"]

        # If silent fails, use username/password
        print(f"🔐 Authenticating with username/password for {TESTMAILBOX_EMAIL}")
        result = self.app.acquire_token_by_username_password(
            username=TESTMAILBOX_EMAIL,
            password=TESTMAILBOX_PASSWORD,
            scopes=SCOPES
        )

        if "access_token" in result:
            print("✅ Username/password authentication successful!")
            self._save_cache()
            return result["access_token"]
        else:
            print("❌ Authentication failed!")
            print(f"Error: {result.get('error')}")
            print(f"Description: {result.get('error_description')}")
            raise Exception(f"Auth failed: {result.get('error_description')}")


# === GRAPH API HELPER ===
def graph_request(endpoint, token, method='GET', data=None):
    """Make Graph API requests with error handling"""
    url = f"https://graph.microsoft.com/v1.0{endpoint}"
    headers = {"Authorization": f"Bearer {token}"}

    if method == 'GET':
        response = requests.get(url, headers=headers)
    elif method == 'PATCH':
        headers["Content-Type"] = "application/json"
        response = requests.patch(url, headers=headers, json=data)
    elif method == 'POST':
        headers["Content-Type"] = "application/json"
        response = requests.post(url, headers=headers, json=data)

    if response.status_code not in [200, 201, 202, 204]:
        print(f"❌ API Error: {response.status_code}")
        print(f"❌ Response: {response.text}")
        response.raise_for_status()

    try:
        return response.json()
    except:
        return {"status": "success"}


# === EMAIL MONITORING FUNCTIONS ===
def get_unread_messages(token, count=50):
    """Get unread messages from the mailbox"""
    endpoint = f"/me/mailFolders/inbox/messages?$filter=isRead eq false&$top={count}&$orderby=receivedDateTime desc"
    return graph_request(endpoint, token)


def get_all_recent_messages(token, count=20):
    """Get recent messages (read and unread)"""
    endpoint = f"/me/mailFolders/inbox/messages?$top={count}&$orderby=receivedDateTime desc"
    return graph_request(endpoint, token)


def get_message_details(token, message_id):
    """Get full message details including body"""
    endpoint = f"/me/messages/{message_id}"
    return graph_request(endpoint, token)


# === AUTOMATION LOGIC ===
def process_messages(token, messages):
    """Process a list of messages"""
    processed_count = 0

    for message in messages:
        message_id = message['id']
        subject = message.get('subject', 'No Subject')
        sender = message.get('from', {}).get('emailAddress', {}).get('address', 'Unknown')
        received = message.get('receivedDateTime', 'Unknown')
        is_read = message.get('isRead', False)

        print(f"\n📨 Processing: {subject}")
        print(f"   👤 From: {sender}")
        print(f"   📅 Received: {received}")
        print(f"   👁️ Read: {'Yes' if is_read else 'No'}")

        # Get full message details if needed
        try:
            full_message = get_message_details(token, message_id)
            body_preview = full_message.get('bodyPreview', 'No preview')[:100]
            body_content = full_message.get('body', {}).get('content', 'No content')[:200]
            print(f"   📄 Preview: {body_preview}...")
            print(f"   📝 Content excerpt: {body_content}...")
        except Exception as e:
            print(f"   ⚠️ Could not get message details: {e}")

        # Read-only processing - log the message
        print(f"   📊 Message logged for processing")

        # Add your custom processing logic here:
        # Example 1: Extract specific information
        if "urgent" in subject.lower() or "important" in subject.lower():
            print(f"   🚨 URGENT MESSAGE DETECTED!")

        # Example 2: Check for specific senders
        if "@sewall.com" not in sender.lower():
            print(f"   🔍 External sender detected")

        # Example 3: Time-based processing
        try:
            from datetime import datetime, timezone
            received_dt = datetime.fromisoformat(received.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            hours_old = (now - received_dt).total_seconds() / 3600
            print(f"   ⏰ Message is {hours_old:.1f} hours old")
        except:
            pass

        processed_count += 1

    return processed_count


def run_mailbox_automation():
    """Main automation function"""
    try:
        print("🤖 Starting testmailbox automation...")
        print(f"⏰ Current time: {datetime.now()}")

        # Get authentication token
        token_manager = TokenManager()
        token = token_manager.get_token()

        # Get user info to confirm authentication
        user_info = graph_request("/me", token)
        print(f"👤 Authenticated as: {user_info.get('userPrincipalName')}")

        # Check for unread messages
        print("\n🔍 Checking for unread messages...")
        unread_result = get_unread_messages(token)
        unread_messages = unread_result.get('value', [])

        if unread_messages:
            print(f"📬 Found {len(unread_messages)} unread messages")
            processed = process_messages(token, unread_messages)
            print(f"\n✅ Processed {processed} messages")
        else:
            print("📭 No unread messages found")

            # Optionally check recent messages anyway
            print("\n🔍 Checking recent messages...")
            recent_result = get_all_recent_messages(token, 5)
            recent_messages = recent_result.get('value', [])

            if recent_messages:
                print(f"📬 Found {len(recent_messages)} recent messages")
                for i, msg in enumerate(recent_messages, 1):
                    subject = msg.get('subject', 'No Subject')
                    sender = msg.get('from', {}).get('emailAddress', {}).get('address', 'Unknown')
                    is_read = msg.get('isRead', False)
                    print(f"{i}. {'📖' if is_read else '📩'} {subject} (from {sender})")

        print(f"\n🎉 Automation complete at {datetime.now()}")

    except Exception as e:
        print(f"💥 Automation error: {e}")
        import traceback
        traceback.print_exc()


def run_continuous_monitoring(check_interval_minutes=5):
    """Run continuous monitoring with specified interval"""
    print(f"🔄 Starting continuous monitoring (checking every {check_interval_minutes} minutes)")
    print("Press Ctrl+C to stop")

    try:
        while True:
            run_mailbox_automation()
            print(f"\n⏳ Waiting {check_interval_minutes} minutes until next check...")
            time.sleep(check_interval_minutes * 60)
    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped by user")


def reset_consent():
    """Reset consent and clear cache"""
    print("🔄 Resetting consent and clearing cache...")
    if os.path.exists(TOKEN_CACHE_FILE):
        os.remove(TOKEN_CACHE_FILE)
        print("✅ Token cache cleared")

    # Force interactive consent for new permissions
    app = msal.PublicClientApplication(
        client_id=CLIENT_ID,
        authority=AUTHORITY
    )

    print("🌐 Starting interactive consent for updated permissions...")
    result = app.acquire_token_interactive(scopes=SCOPES)

    if "access_token" in result:
        print("✅ Interactive consent successful!")
        print("💡 Now you can run the automation normally")
    else:
        print("❌ Interactive consent failed!")
        print(f"Error: {result.get('error_description')}")


if __name__ == "__main__":
    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--reset-consent":
            reset_consent()
        elif sys.argv[1] == "--monitor":
            interval = int(sys.argv[2]) if len(sys.argv) > 2 else 5
            run_continuous_monitoring(check_interval_minutes=interval)
        elif sys.argv[1] == "--help":
            print("Usage:")
            print("  python script.py                    # Single run")
            print("  python script.py --reset-consent    # Reset permissions")
            print("  python script.py --monitor [mins]   # Continuous monitoring")
            print("  python script.py --help            # Show this help")
        else:
            print(f"Unknown argument: {sys.argv[1]}")
            print("Use --help for usage information")
    else:
        # Single run
        run_mailbox_automation()