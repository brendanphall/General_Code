import msal
import requests
import os
import json
from datetime import datetime
import time
import sys

# === CONFIGURATION (Your Azure App Credentials) ===
CLIENT_ID = '94fac862-ac02-434a-b77c-13b75d5f45f4'
CLIENT_SECRET = 'tAw8Q~~QiGku_ZIuMOMeggZBu6WDU_iQ1YlA-az~'  # Your actual secret
TENANT_ID = '31c26211-2687-4fb9-94dd-8dcb92e5320d'
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"

# Target mailbox for testing
TARGET_MAILBOX = "testmailbox@sewall.com"

# Token cache file
TOKEN_CACHE_FILE = "token_cache.json"


# === METHOD 1: APP-ONLY ACCESS (Recommended for automation) ===
class AppOnlyGraphHelper:
    """Use app-only authentication to access specific mailbox"""

    def __init__(self):
        self.app = msal.ConfidentialClientApplication(
            client_id=CLIENT_ID,
            client_credential=CLIENT_SECRET,
            authority=AUTHORITY
        )

    def get_app_token(self):
        """Get app-only access token"""
        print("🔐 Getting app-only access token...")

        # Application permissions scope
        scopes = ["https://graph.microsoft.com/.default"]

        result = self.app.acquire_token_for_client(scopes=scopes)

        if "access_token" in result:
            print("✅ App-only authentication successful!")
            return result["access_token"]
        else:
            error_desc = result.get('error_description', 'Unknown error')
            print(f"❌ App-only authentication failed: {error_desc}")
            raise Exception(f"Auth failed: {error_desc}")

    def access_mailbox(self, mailbox_email):
        """Access specific user's mailbox with app permissions"""
        token = self.get_app_token()
        headers = {"Authorization": f"Bearer {token}"}

        # Get user info
        print(f"👤 Accessing mailbox: {mailbox_email}")
        user_url = f"https://graph.microsoft.com/v1.0/users/{mailbox_email}"
        user_response = requests.get(user_url, headers=headers)

        if user_response.status_code == 200:
            user_info = user_response.json()
            print(f"✅ Connected to: {user_info.get('displayName', 'Unknown')}")

            # Get messages
            messages_url = f"https://graph.microsoft.com/v1.0/users/{mailbox_email}/mailFolders/inbox/messages"
            params = {'$top': 10, '$orderby': 'receivedDateTime desc'}

            messages_response = requests.get(messages_url, headers=headers, params=params)

            if messages_response.status_code == 200:
                messages = messages_response.json()
                return messages
            else:
                print(f"❌ Error getting messages: {messages_response.status_code}")
                print(f"❌ Response: {messages_response.text}")
                return None
        else:
            print(f"❌ Error accessing user: {user_response.status_code}")
            print(f"❌ Response: {user_response.text}")
            return None


# === METHOD 2: DELEGATED ACCESS (Your existing approach) ===
class DelegatedGraphHelper:
    """Use delegated authentication with testmailbox credentials"""

    def __init__(self):
        self.token_cache = self._load_cache()
        self.app = msal.PublicClientApplication(
            client_id=CLIENT_ID,
            authority=AUTHORITY,
            token_cache=self.token_cache
        )

    def _load_cache(self):
        """Load token cache"""
        cache = msal.SerializableTokenCache()
        if os.path.exists(TOKEN_CACHE_FILE):
            try:
                with open(TOKEN_CACHE_FILE, 'r') as f:
                    cache.deserialize(f.read())
                print("📁 Loaded token cache")
            except Exception as e:
                print(f"⚠️ Could not load cache: {e}")
        return cache

    def _save_cache(self):
        """Save token cache"""
        if self.token_cache.has_state_changed:
            try:
                with open(TOKEN_CACHE_FILE, 'w') as f:
                    f.write(self.token_cache.serialize())
                print("💾 Token cache saved")
            except Exception as e:
                print(f"⚠️ Could not save cache: {e}")

    def get_delegated_token(self):
        """Get delegated access token using testmailbox credentials"""
        # Try silent first
        accounts = self.app.get_accounts()
        if accounts:
            print("🔄 Trying silent token acquisition...")
            result = self.app.acquire_token_silent(
                scopes=["https://graph.microsoft.com/Mail.Read"],
                account=accounts[0]
            )
            if result and "access_token" in result:
                print("✅ Got token silently")
                self._save_cache()
                return result["access_token"]

        # Fall back to username/password
        testmailbox_password = os.environ.get('TESTMAILBOX_PASSWORD', 'Elephant_Matchstick_99')

        print(f"🔐 Authenticating as {TARGET_MAILBOX}...")
        result = self.app.acquire_token_by_username_password(
            username=TARGET_MAILBOX,
            password=testmailbox_password,
            scopes=["https://graph.microsoft.com/Mail.Read"]
        )

        if "access_token" in result:
            print("✅ Delegated authentication successful!")
            self._save_cache()
            return result["access_token"]
        else:
            error_desc = result.get('error_description', 'Unknown error')
            print(f"❌ Delegated authentication failed: {error_desc}")
            raise Exception(f"Auth failed: {error_desc}")

    def access_my_mailbox(self):
        """Access authenticated user's own mailbox"""
        token = self.get_delegated_token()
        headers = {"Authorization": f"Bearer {token}"}

        # Get user info
        user_response = requests.get("https://graph.microsoft.com/v1.0/me", headers=headers)
        if user_response.status_code == 200:
            user_info = user_response.json()
            print(f"✅ Authenticated as: {user_info.get('userPrincipalName')}")

        # Get messages
        messages_response = requests.get(
            "https://graph.microsoft.com/v1.0/me/messages",
            headers=headers,
            params={'$top': 10, '$orderby': 'receivedDateTime desc'}
        )

        if messages_response.status_code == 200:
            return messages_response.json()
        else:
            print(f"❌ Error getting messages: {messages_response.status_code}")
            return None


# === MAIN TESTING FUNCTION ===
def test_both_methods():
    """Test both app-only and delegated access methods"""

    print("=" * 60)
    print("TESTING MAILBOX ACCESS WITH YOUR AZURE CREDENTIALS")
    print("=" * 60)

    print(f"🎯 Target Mailbox: {TARGET_MAILBOX}")
    print(f"🔑 Client ID: {CLIENT_ID}")
    print(f"🔑 Client Secret: {CLIENT_SECRET[:10]}...")
    print(f"🏢 Tenant ID: {TENANT_ID}")

    # === TEST METHOD 1: APP-ONLY ACCESS ===
    print("\n" + "=" * 50)
    print("METHOD 1: APP-ONLY ACCESS")
    print("=" * 50)
    print("💡 This uses application permissions to access any mailbox")
    print("💡 Requires admin consent for Mail.Read application permission")

    try:
        app_helper = AppOnlyGraphHelper()
        app_messages = app_helper.access_mailbox(TARGET_MAILBOX)

        if app_messages:
            message_count = len(app_messages.get('value', []))
            print(f"📬 Found {message_count} messages via app-only access")

            # Show first few messages
            for i, msg in enumerate(app_messages.get('value', [])[:3], 1):
                subject = msg.get('subject', 'No Subject')
                sender = msg.get('from', {}).get('emailAddress', {}).get('address', 'Unknown')
                print(f"{i}. 📨 {subject} (from {sender})")
        else:
            print("❌ App-only access failed")

    except Exception as e:
        print(f"❌ App-only method failed: {e}")
        print("💡 This might require admin consent for application permissions")

    # === TEST METHOD 2: DELEGATED ACCESS ===
    print("\n" + "=" * 50)
    print("METHOD 2: DELEGATED ACCESS")
    print("=" * 50)
    print("💡 This uses your existing testmailbox credentials")
    print("💡 Should work with your current setup")

    try:
        delegated_helper = DelegatedGraphHelper()
        delegated_messages = delegated_helper.access_my_mailbox()

        if delegated_messages:
            message_count = len(delegated_messages.get('value', []))
            print(f"📬 Found {message_count} messages via delegated access")

            # Show first few messages
            for i, msg in enumerate(delegated_messages.get('value', [])[:3], 1):
                subject = msg.get('subject', 'No Subject')
                sender = msg.get('from', {}).get('emailAddress', {}).get('address', 'Unknown')
                print(f"{i}. 📨 {subject} (from {sender})")
        else:
            print("❌ Delegated access failed")

    except Exception as e:
        print(f"❌ Delegated method failed: {e}")

    print("\n" + "=" * 50)
    print("RECOMMENDATION")
    print("=" * 50)
    print("✅ Use METHOD 2 (delegated) for testing with testmailbox")
    print("✅ Use METHOD 1 (app-only) for production with aff_004 mailbox")
    print("💡 Both use your Azure app credentials, just different permission types")


# === FOCUSED TESTMAILBOX ACCESS ===
def access_testmailbox():
    """Simple function to access testmailbox with your credentials"""

    print("🎯 Accessing testmailbox@sewall.com with your Azure app...")

    try:
        helper = DelegatedGraphHelper()
        messages = helper.access_my_mailbox()

        if messages:
            message_list = messages.get('value', [])
            print(f"✅ Successfully accessed mailbox!")
            print(f"📬 Found {len(message_list)} messages")

            if message_list:
                print("\n📋 Recent Messages:")
                for i, msg in enumerate(message_list[:5], 1):
                    subject = msg.get('subject', 'No Subject')
                    sender = msg.get('from', {}).get('emailAddress', {}).get('address', 'Unknown')
                    received = msg.get('receivedDateTime', 'Unknown')
                    is_read = msg.get('isRead', False)

                    print(f"{i}. {'📖' if is_read else '📩'} {subject}")
                    print(f"   👤 From: {sender}")
                    print(f"   📅 {received}")
            else:
                print("📭 No messages found")
        else:
            print("❌ Failed to access messages")

    except Exception as e:
        print(f"💥 Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test-both":
        test_both_methods()
    else:
        access_testmailbox()