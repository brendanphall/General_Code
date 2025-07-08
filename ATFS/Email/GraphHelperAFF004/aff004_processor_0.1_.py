import msal
import requests
import os
import json
import re
from datetime import datetime
import time
import sys

# === CONFIGURATION ===
CLIENT_ID = '94fac862-ac02-434a-b77c-13b75d5f45f4'
CLIENT_SECRET = 'tAw8Q~~QiGku_ZIuMOMeggZBu6WDU_iQ1YlA-az~'
TENANT_ID = '31c26211-2687-4fb9-94dd-8dcb92e5320d'
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"

# === CHOOSE AUTHENTICATION METHOD ===
# Switch between these two by commenting/uncommenting

# TESTING: Delegated authentication with testmailbox (CURRENT - WORKING)
USE_DELEGATED_AUTH = True
TARGET_MAILBOX = "testmailbox@sewall.com"
TOKEN_CACHE_FILE = "token_cache.json"

# PRODUCTION: App-only authentication like PHP (COMMENTED OUT)
# USE_DELEGATED_AUTH = False
# TARGET_MAILBOX = "aff_004@sewall.com"  # Or any mailbox
# TOKEN_CACHE_FILE = "token.json"  # Match PHP filename

# All 50 states + DC (from PHP)
STATES_LIST = [
    "AK", "AL", "AR", "AZ", "CA", "CO", "CT", "DC", "DE", "FL", "GA", "HI",
    "IA", "ID", "IL", "IN", "KS", "KY", "LA", "MA", "MD", "ME", "MI", "MN",
    "MO", "MS", "MT", "NC", "ND", "NE", "NH", "NJ", "NM", "NV", "NY", "OH",
    "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VA", "VI", "VT",
    "WA", "WI", "WV", "WY"
]


# ========================================================================
# AUTHENTICATION METHOD 1: DELEGATED (Current Working Method)
# ========================================================================
class DelegatedGraphHelper:
    """
    DELEGATED AUTHENTICATION - Current Working Method
    - Uses user credentials (testmailbox@sewall.com)
    - Delegated permissions (Mail.ReadWrite on behalf of user)
    - Accesses user's own mailbox
    - Requires user password
    """

    def __init__(self):
        print("🔐 Using DELEGATED authentication (testmailbox user)")
        self.token_cache = self._load_cache()
        self.app = msal.PublicClientApplication(
            client_id=CLIENT_ID,
            authority=AUTHORITY,
            token_cache=self.token_cache
        )

    def _load_cache(self):
        cache = msal.SerializableTokenCache()
        if os.path.exists(TOKEN_CACHE_FILE):
            try:
                with open(TOKEN_CACHE_FILE, 'r') as f:
                    cache.deserialize(f.read())
                print("📁 Loaded delegated token cache")
            except Exception as e:
                print(f"⚠️ Could not load cache: {e}")
        return cache

    def _save_cache(self):
        if self.token_cache.has_state_changed:
            try:
                with open(TOKEN_CACHE_FILE, 'w') as f:
                    f.write(self.token_cache.serialize())
                print("💾 Delegated token cache saved")
            except Exception as e:
                print(f"⚠️ Could not save cache: {e}")

    def get_token(self):
        # Try silent first
        accounts = self.app.get_accounts()
        if accounts:
            result = self.app.acquire_token_silent(
                scopes=["https://graph.microsoft.com/Mail.ReadWrite"],
                account=accounts[0]
            )
            if result and "access_token" in result:
                self._save_cache()
                return result["access_token"]

        # Fallback to username/password
        testmailbox_password = os.environ.get('TESTMAILBOX_PASSWORD', 'Elephant_Matchstick_99')
        result = self.app.acquire_token_by_username_password(
            username=TARGET_MAILBOX,
            password=testmailbox_password,
            scopes=["https://graph.microsoft.com/Mail.ReadWrite"]
        )

        if "access_token" in result:
            self._save_cache()
            return result["access_token"]
        else:
            raise Exception(f"Delegated auth failed: {result.get('error_description')}")

    def get_inbox_messages(self, token, count=100):
        """Get inbox messages for authenticated user"""
        headers = {"Authorization": f"Bearer {token}"}
        url = "https://graph.microsoft.com/v1.0/me/messages"  # User's own mailbox
        params = {
            '$top': count,
            '$orderby': 'receivedDateTime desc',
            '$select': 'id,subject,from,receivedDateTime,hasAttachments,isRead,body'
        }

        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error getting messages: {response.status_code} - {response.text}")

    def get_user_info(self, token):
        """Get authenticated user info"""
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get("https://graph.microsoft.com/v1.0/me", headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error getting user info: {response.status_code}")


# ========================================================================
# AUTHENTICATION METHOD 2: APP-ONLY (PHP Method - Identical to PHP)
# ========================================================================
class AppOnlyGraphHelper:
    """
    APP-ONLY AUTHENTICATION - Matches PHP Method Exactly
    - Uses client credentials (CLIENT_ID + CLIENT_SECRET)
    - Application permissions (Mail.Read at application level)
    - Can access any mailbox in the organization
    - No user credentials required
    - Exactly matches PHP processAFF004Email.php authentication
    """

    def __init__(self):
        print("🔐 Using APP-ONLY authentication (matching PHP method)")
        self.token_cache = self._load_cache()

        # Check for FAILED file (matching PHP logic)
        if os.path.exists('FAILED'):
            print("❌ FAILED file exists - previous authentication error")
            raise Exception("FAILED file detected - remove to retry")

        # Confidential client app (matching PHP GraphHelper)
        self.app = msal.ConfidentialClientApplication(
            client_id=CLIENT_ID,
            client_credential=CLIENT_SECRET,
            authority=AUTHORITY,
            token_cache=self.token_cache
        )

    def _load_cache(self):
        """Load token cache (replicates PHP readToken())"""
        cache = msal.SerializableTokenCache()
        if os.path.exists(TOKEN_CACHE_FILE):
            try:
                with open(TOKEN_CACHE_FILE, 'r') as f:
                    token_data = f.read()
                    if token_data.strip():
                        cache.deserialize(token_data)
                        print("📁 Loaded app-only token cache (matching PHP)")
                    else:
                        print("📁 Token cache file empty")
            except Exception as e:
                print(f"⚠️ Could not load token cache: {e}")
        return cache

    def _save_cache(self):
        """Save token cache (replicates PHP updateToken())"""
        if self.token_cache.has_state_changed:
            try:
                with open(TOKEN_CACHE_FILE, 'w') as f:
                    f.write(self.token_cache.serialize())
                print("💾 App-only token cache saved (matching PHP)")
            except Exception as e:
                print(f"⚠️ Could not save token cache: {e}")

    def get_token(self):
        """Get app-only access token (replicates PHP getUserToken())"""
        print("🔐 Acquiring app-only access token...")

        # Application permissions scope (matching PHP)
        scopes = ["https://graph.microsoft.com/.default"]

        try:
            result = self.app.acquire_token_for_client(scopes=scopes)

            if "access_token" in result:
                print("✅ App-only authentication successful! (matching PHP)")
                self._save_cache()
                return result["access_token"]
            else:
                error_desc = result.get('error_description', 'Unknown error')
                print(f"❌ App-only authentication failed: {error_desc}")

                # Create FAILED file (matching PHP behavior)
                error_msg = f"{datetime.now().isoformat()} Error getting app token: {error_desc}"
                with open('FAILED', 'w') as f:
                    f.write(error_msg)

                # Send notification email (would match PHP email logic)
                self._send_error_notification(error_desc)

                raise Exception(f"App auth failed: {error_desc}")

        except Exception as e:
            # Create FAILED file on any exception
            error_msg = f"{datetime.now().isoformat()} Exception in app auth: {str(e)}"
            with open('FAILED', 'w') as f:
                f.write(error_msg)
            raise e

    def get_inbox_messages(self, token, count=100):
        """Get inbox messages for specific mailbox (matching PHP getInbox())"""
        headers = {"Authorization": f"Bearer {token}"}

        # Access specific mailbox (matching PHP approach)
        url = f"https://graph.microsoft.com/v1.0/users/{TARGET_MAILBOX}/mailFolders/inbox/messages"
        params = {
            '$top': count,
            '$orderby': 'receivedDateTime desc',
            '$select': 'id,subject,from,receivedDateTime,hasAttachments,isRead,body'
        }

        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            error_msg = f"Error getting messages from {TARGET_MAILBOX}: {response.status_code} - {response.text}"
            print(f"❌ {error_msg}")

            # Create FAILED file (matching PHP)
            with open('FAILED', 'w') as f:
                f.write(f"{datetime.now().isoformat()} {error_msg}")

            raise Exception(error_msg)

    def get_user_info(self, token):
        """Get target user info (replicates PHP getUser())"""
        headers = {"Authorization": f"Bearer {token}"}

        # Access specific user (matching PHP)
        url = f"https://graph.microsoft.com/v1.0/users/{TARGET_MAILBOX}"
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            return response.json()
        else:
            error_msg = f"Error getting user {TARGET_MAILBOX}: {response.status_code} - {response.text}"
            print(f"❌ {error_msg}")

            # Create FAILED file and send notification (matching PHP)
            with open('FAILED', 'w') as f:
                f.write(f"{datetime.now().isoformat()} {error_msg}")

            self._send_error_notification(error_msg)
            raise Exception(error_msg)

    def _send_error_notification(self, error_msg):
        """Send error notification (placeholder for PHP email functionality)"""
        print(f"🚨 Would send error email to support@jws.com: {error_msg}")
        print("💡 In production, this would match PHP send_email() function")


# ========================================================================
# EMAIL PROCESSING FUNCTIONS (Identical for Both Methods)
# ========================================================================

def check_aff004_subject(subject):
    """Check if subject matches AFF 004 patterns (replicates PHP regex)"""
    if not subject:
        return False

    subject_lower = subject.lower()

    # PHP regex: "/upload\s?004|upload\s?04|004\s?upload|submit\s?004|submit\s?04|upload\s?2021|upload\s?021|upload\s?21|021\s?upload|21\s?upload|submit\s?021|submit\s?21/i"
    patterns = [
        r'upload\s?004', r'upload\s?04', r'004\s?upload',
        r'submit\s?004', r'submit\s?04',
        r'upload\s?2021', r'upload\s?021', r'upload\s?21',
        r'021\s?upload', r'21\s?upload',
        r'submit\s?021', r'submit\s?21'
    ]

    for pattern in patterns:
        if re.search(pattern, subject_lower):
            return True

    return False


def get_message_attachments(token, message_id, target_mailbox=None):
    """Get message attachments"""
    headers = {"Authorization": f"Bearer {token}"}

    if USE_DELEGATED_AUTH:
        # Delegated: access user's own messages
        url = f"https://graph.microsoft.com/v1.0/me/messages/{message_id}/attachments"
    else:
        # App-only: access specific user's messages
        url = f"https://graph.microsoft.com/v1.0/users/{TARGET_MAILBOX}/messages/{message_id}/attachments"

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ Error getting attachments: {response.status_code}")
        return None


def download_attachment(token, message_id, attachment_id, filename):
    """Download attachment content"""
    headers = {"Authorization": f"Bearer {token}"}

    if USE_DELEGATED_AUTH:
        # Delegated: access user's own messages
        url = f"https://graph.microsoft.com/v1.0/me/messages/{message_id}/attachments/{attachment_id}"
    else:
        # App-only: access specific user's messages
        url = f"https://graph.microsoft.com/v1.0/users/{TARGET_MAILBOX}/messages/{message_id}/attachments/{attachment_id}"

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        attachment_data = response.json()

        if attachment_data.get('@odata.type') == '#microsoft.graph.fileAttachment':
            import base64
            content_bytes = base64.b64decode(attachment_data['contentBytes'])

            with open(filename, 'wb') as f:
                f.write(content_bytes)
            return True
        else:
            print(f"⚠️ Unsupported attachment type: {attachment_data.get('@odata.type')}")
            return False
    else:
        print(f"❌ Error downloading attachment: {response.status_code}")
        return False


def create_folder_if_not_exists(token, folder_name):
    """Create mail folder if it doesn't exist"""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    if USE_DELEGATED_AUTH:
        # Delegated: access user's own folders
        folders_url = "https://graph.microsoft.com/v1.0/me/mailFolders"
    else:
        # App-only: access specific user's folders
        folders_url = f"https://graph.microsoft.com/v1.0/users/{TARGET_MAILBOX}/mailFolders"

    folders_response = requests.get(folders_url, headers=headers)

    if folders_response.status_code != 200:
        print(f"❌ Error getting folders: {folders_response.status_code}")
        return None

    folders = folders_response.json()

    # Look for existing folder
    for folder in folders.get('value', []):
        if folder.get('displayName', '').lower() == folder_name.lower():
            return folder['id']

    # Create folder if not found
    print(f"📁 Creating folder: {folder_name}")
    create_data = {"displayName": folder_name}

    create_response = requests.post(folders_url, headers=headers, json=create_data)
    if create_response.status_code == 201:
        new_folder = create_response.json()
        print(f"✅ Created folder: {folder_name}")
        return new_folder['id']
    else:
        print(f"❌ Error creating folder: {create_response.status_code}")
        return None


def move_message_to_folder(token, message_id, folder_name):
    """Move message to a specific folder"""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # Get or create the destination folder
    destination_folder_id = create_folder_if_not_exists(token, folder_name)

    if not destination_folder_id:
        print(f"⚠️ Could not get/create folder '{folder_name}'. Message will stay in inbox.")
        return False

    if USE_DELEGATED_AUTH:
        # Delegated: move user's own message
        move_url = f"https://graph.microsoft.com/v1.0/me/messages/{message_id}/move"
    else:
        # App-only: move specific user's message
        move_url = f"https://graph.microsoft.com/v1.0/users/{TARGET_MAILBOX}/messages/{message_id}/move"

    move_data = {"destinationId": destination_folder_id}

    response = requests.post(move_url, headers=headers, json=move_data)
    if response.status_code == 201:
        print(f"✅ Message moved to '{folder_name}' folder")
        return True
    else:
        print(f"❌ Error moving message: {response.status_code} - {response.text}")
        return False


def send_email_response(to_email, subject, body_html, body_text):
    """Send email response (placeholder - implement your email service)"""
    print(f"📧 SEND EMAIL TO: {to_email}")
    print(f"📋 SUBJECT: {subject}")
    print(f"📄 BODY: {body_text[:100]}...")
    print("💡 Email sending logic would go here (matching PHP send_email function)")


# ========================================================================
# MAIN PROCESSING FUNCTION (Identical for Both Authentication Methods)
# ========================================================================

def process_aff004_emails():
    """Main AFF 004 email processing function (works with both auth methods)"""

    print("🚀 Starting AFF 004 email processing...")
    print(f"⏰ Current time: {datetime.now()}")
    print(f"🎯 Target mailbox: {TARGET_MAILBOX}")
    print(f"🔐 Authentication method: {'DELEGATED' if USE_DELEGATED_AUTH else 'APP-ONLY (PHP method)'}")

    try:
        # Initialize the appropriate graph helper
        if USE_DELEGATED_AUTH:
            graph_helper = DelegatedGraphHelper()
        else:
            graph_helper = AppOnlyGraphHelper()

        # Get authentication token
        token = graph_helper.get_token()
        print("✅ Authentication successful")

        # Get user info to confirm access
        user_info = graph_helper.get_user_info(token)
        print(f"👤 Connected as: {user_info.get('userPrincipalName', user_info.get('displayName', 'Unknown'))}")

        # Get all inbox messages
        messages_result = graph_helper.get_inbox_messages(token, count=50)
        all_messages = messages_result.get('value', [])

        print(f"📬 Found {len(all_messages)} total messages in inbox")

        # Process each message (identical logic for both auth methods)
        aff004_count = 0
        other_count = 0

        for message in all_messages:
            message_id = message['id']
            subject = message.get('subject', 'No Subject')
            sender_info = message.get('from', {}).get('emailAddress', {})
            sender_email = sender_info.get('address', 'Unknown')
            sender_name = sender_info.get('name', sender_email)
            received_datetime = message.get('receivedDateTime', 'Unknown')
            has_attachments = message.get('hasAttachments', False)

            print(f"\n📨 Processing: {subject}")
            print(f"   👤 From: {sender_name} ({sender_email})")
            print(f"   📅 Received: {received_datetime}")
            print(f"   📎 Attachments: {'Yes' if has_attachments else 'No'}")

            # Check if this is an AFF 004 message (matching PHP regex)
            if check_aff004_subject(subject):
                print("   ✅ MATCHES AFF 004 pattern!")
                aff004_count += 1

                # Process AFF 004 message
                process_single_aff004_message(token, message, sender_email, sender_name, subject, received_datetime)

                # Move to Processed folder (matching PHP)
                move_message_to_folder(token, message_id, "Processed")

            else:
                print("   ⏭️ Not an AFF 004 message")
                other_count += 1

                # Move to NotUpload004 folder (matching PHP)
                move_message_to_folder(token, message_id, "NotUpload004")

        print(f"\n📊 PROCESSING SUMMARY:")
        print(f"   🎯 AFF 004 messages: {aff004_count}")
        print(f"   📁 Other messages: {other_count}")
        print(f"   📅 Completed at: {datetime.now()}")

    except Exception as e:
        print(f"💥 Error in AFF 004 processing: {e}")
        import traceback
        traceback.print_exc()


def process_single_aff004_message(token, message, sender_email, sender_name, subject, received_datetime):
    """Process a single AFF 004 message (identical for both auth methods)"""

    message_id = message['id']
    has_attachments = message.get('hasAttachments', False)

    print(f"   🔄 Processing AFF 004 message from {sender_email}")

    if not has_attachments:
        print("   ❌ No PDF file attached")
        send_email_response(
            sender_email,
            "Inspection PDF Form - No pdf file attachment found",
            '<html><body><b>No Inspection PDF Form file attachment was found.</b><br><br>'
            'We received your email with the correct subject line keyword, however we did not find a PDF file attachment.</body></html>',
            "No Inspection PDF Form file attachment was found.\n\nWe received your email with the correct subject line keyword, however we did not find a PDF file attachment."
        )
        return

    # Get attachments
    attachments_result = get_message_attachments(token, message_id)
    if not attachments_result:
        print("   ❌ Could not retrieve attachments")
        return

    attachments = attachments_result.get('value', [])
    pdf_found = False

    for attachment in attachments:
        attachment_name = attachment.get('name', '')
        content_type = attachment.get('contentType', '')
        attachment_id = attachment.get('id', '')

        print(f"   📎 Attachment: {attachment_name} ({content_type})")

        # Check if this is a PDF (matching PHP logic)
        if (content_type.lower() in ['application/pdf', 'application/octet-stream'] and
                attachment_name.lower().endswith('.pdf')):

            print(f"   ✅ PDF found: {attachment_name}")
            pdf_found = True

            # Generate timestamped filename (matching PHP)
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            local_filename = f"{timestamp}.pdf"

            # Download PDF for processing
            if download_attachment(token, message_id, attachment_id, local_filename):
                print(f"   📥 Downloaded: {local_filename}")

                # Here you would add the PDF processing logic:
                # - Parse PDF fields (state, tree farm number)
                # - Validate against database
                # - Generate responses
                # - Process inspection data

                print(f"   🔍 PDF processing would happen here...")
                print(f"   💡 Next: Parse PDF, validate data, update database")

                # Clean up downloaded file
                try:
                    os.remove(local_filename)
                    print(f"   🗑️ Cleaned up temporary file")
                except:
                    pass
            else:
                print(f"   ❌ Failed to download attachment")

    if not pdf_found:
        print("   ❌ No PDF attachments found")
        send_email_response(
            sender_email,
            "Inspection PDF Form - No pdf file attachment found",
            '<html><body><b>No Inspection PDF Form file attachment was found.</b></body></html>',
            "No Inspection PDF Form file attachment was found."
        )


# ========================================================================
# COMMAND LINE INTERFACE
# ========================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("AFF 004 EMAIL PROCESSOR - DUAL AUTHENTICATION")
    print("=" * 70)

    if USE_DELEGATED_AUTH:
        print("🔐 CURRENT MODE: DELEGATED AUTHENTICATION")
        print("   • Uses testmailbox user credentials")
        print("   • Perfect for testing and development")
        print("   • Matches your current working setup")
    else:
        print("🔐 CURRENT MODE: APP-ONLY AUTHENTICATION")
        print("   • Uses client credentials (matches PHP exactly)")
        print("   • Perfect for production deployment")
        print("   • Requires application permissions")

    print(f"🎯 Target Mailbox: {TARGET_MAILBOX}")
    print(f"📁 Token File: {TOKEN_CACHE_FILE}")
    print("=" * 70)

    if len(sys.argv) > 1:
        if sys.argv[1] == "--help":
            print("Usage:")
            print("  python dual_auth_processor.py           # Process AFF 004 emails")
            print("  python dual_auth_processor.py --help    # Show this help")
            print("")
            print("To switch authentication methods:")
            print("  Edit the script and change USE_DELEGATED_AUTH = True/False")
        else:
            print(f"Unknown argument: {sys.argv[1]}")
    else:
        try:
            process_aff004_emails()
        except Exception as e:
            print(f"💥 Processing failed: {e}")
            import traceback

            traceback.print_exc()