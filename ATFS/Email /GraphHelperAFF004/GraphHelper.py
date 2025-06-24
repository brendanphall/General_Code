# graph_helper.py
# Basic helper for Microsoft Graph using MSAL (app-only auth)

import os
import msal
import requests

class GraphHelper:
    def __init__(self):
        self.client_id = os.getenv("CLIENT_ID")
        self.client_secret = os.getenv("CLIENT_SECRET")
        self.tenant_id = os.getenv("TENANT_ID")
        self.scope = ["https://graph.microsoft.com/.default"]  # For app-only auth
        self.token = None
        self.graph_endpoint = "https://graph.microsoft.com/v1.0"

        self._authenticate()

    def _authenticate(self):
        authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        app = msal.ConfidentialClientApplication(
            self.client_id,
            authority=authority,
            client_credential=self.client_secret
        )
        result = app.acquire_token_silent(self.scope, account=None)
        if not result:
            result = app.acquire_token_for_client(scopes=self.scope)

        if "access_token" in result:
            self.token = result["access_token"]
        else:
            raise Exception(f"Auth failed: {result.get('error_description')}")

    def get(self, path):
        url = f"{self.graph_endpoint}{path}"
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()

# Example usage:
# helper = GraphHelper()
# messages = helper.get("/users/youruser@domain.com/mailFolders/inbox/messages?$top=5")
# print(messages)
