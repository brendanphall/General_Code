# graph_helper.py
# Replacement for GraphHelper.php in PHP
# Uses Microsoft MSAL for app-only authentication

import os
import msal
import requests

class GraphHelper:
    """
    GraphHelper handles token acquisition and authenticated requests
    using Microsoft Graph API with app-only credentials.
    """

    # Static class variables for token and Graph endpoint
    token = None
    graph_endpoint = "https://graph.microsoft.com/v1.0"

    @staticmethod
    def initialize_graph_for_user_auth():
        """
        Authenticate using client credentials and acquire a token.
        Equivalent to GraphHelper::initializeGraphForUserAuth() in PHP.
        """
        client_id = os.getenv("CLIENT_ID")
        client_secret = os.getenv("CLIENT_SECRET")
        tenant_id = os.getenv("TENANT_ID")

        if not all([client_id, client_secret, tenant_id]):
            raise ValueError("Missing one or more required environment variables.")

        authority = f"https://login.microsoftonline.com/{tenant_id}"
        app = msal.ConfidentialClientApplication(
            client_id=client_id,
            client_credential=client_secret,
            authority=authority
        )

        # Acquire token for app
        result = app.acquire_token_silent(scopes=["https://graph.microsoft.com/.default"], account=None)
        if not result:
            result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])

        if "access_token" not in result:
            raise Exception(f"Could not acquire token: {result.get('error_description')}")

        GraphHelper.token = result["access_token"]

    @staticmethod
    def get_user():
        """
        Equivalent to GraphHelper::getUser() in PHP.
        Fetches information about the service principal's identity.
        """
        if GraphHelper.token is None:
            raise Exception("Graph not initialized. Call initialize_graph_for_user_auth first.")

        headers = {
            "Authorization": f"Bearer {GraphHelper.token}"
        }

        # This endpoint only works for delegated auth — app-only accounts may not have a user object.
        response = requests.get(f"{GraphHelper.graph_endpoint}/me", headers=headers)

        if response.status_code != 200:
            raise Exception(f"Graph API call failed: {response.text}")

        return response.json()

    @staticmethod
    def get(path: str):
        """
        Perform a GET request to any Microsoft Graph endpoint path.
        E.g., /users/{user}/mailFolders/inbox/messages
        """
        if GraphHelper.token is None:
            raise Exception("Graph not initialized. Call initialize_graph_for_user_auth first.")

        url = f"{GraphHelper.graph_endpoint}{path}"
        headers = {
            "Authorization": f"Bearer {GraphHelper.token}"
        }

        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
