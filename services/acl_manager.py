import requests
import os

TAILSCALE_API_TOKEN = os.getenv("TAILSCALE_API_TOKEN")
TAILNET_NAME = os.getenv("TAILNET_NAME")

class ACLManager:
    def __init__(self):
        self.base_url = f"https://api.tailscale.com/api/v2/tailnet/{TAILNET_NAME}"
        self.headers = {
            "Authorization": f"Bearer {TAILSCALE_API_TOKEN}",
            "Content-Type": "application/json"
        }

    def add_user_to_acl(self, username):
        # TODO: Grant SSH access to the authenticated user
        data = {
            "acls": [
                {
                    "users": [f"user:{username}"],
                    "ports": ["22/tcp"]
                }
            ]
        }
        url = f"{self.base_url}/acl"
        response = requests.post(url, json=data, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def remove_user_from_acl(self, username):
        # TODO: Revoke SSH access
        data = {
            "acls": []
        }
        url = f"{self.base_url}/acl"
        response = requests.post(url, json=data, headers=self.headers)
        response.raise_for_status()
        return response.json()
