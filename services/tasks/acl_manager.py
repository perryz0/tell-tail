import requests
import os
from dotenv import load_dotenv

load_dotenv()

TAILSCALE_API_TOKEN = os.getenv("TAILSCALE_API_TOKEN")
TAILNET_NAME = os.getenv("TAILNET_NAME")
# print(f"Loaded the TAILNET NAME: {TAILNET_NAME}")

class ACLManager:
    def __init__(self):
        self.base_url = f"https://api.tailscale.com/api/v2/tailnet/{TAILNET_NAME}"
        self.headers = {
            "Authorization": f"Bearer {TAILSCALE_API_TOKEN}",
            "Content-Type": "application/json"
        }

    def _make_request(self, method, endpoint, data=None):
        try:
            url = f"{self.base_url}{endpoint}"
            response = requests.request(method, url, headers=self.headers, json=data)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error: {e}")
            return None

    def get_acls(self):
        """Fetch the current ACL configuration."""
        return self._make_request("GET", "/acl")

    def list_users(self):
        """List all users in the current ACL."""
        acls = self.get_acls()
        if acls:
            users = [entry['users'] for entry in acls.get('acls', [])]
            return [user for sublist in users for user in sublist]
        return []

    def add_user_to_acl(self, username, ports=None):
        """Add or update a user in the ACL with specified ports."""
        if ports is None:
            ports = ["22/tcp"]  # Defaulting to SSH port 22 for now

        existing_acls = self.get_acls()
        if not existing_acls:
            return "Error fetching current ACLs."

        # Check if user already exists
        if f"user:{username}" in self.list_users():
            return f"User {username} already exists in ACL."

        # Update the ACL by adding a new user entry
        new_entry = {
            "users": [f"user:{username}"],
            "ports": ports
        }

        updated_acls = existing_acls.get("acls", [])
        updated_acls.append(new_entry)
        data = {"acls": updated_acls}

        return self._make_request("POST", "/acl", data)

    def remove_user_from_acl(self, username):
        """Remove a user from the ACL."""
        existing_acls = self.get_acls()
        if not existing_acls:
            return "Error fetching current ACLs."

        # Filter out user from existing ACLs
        updated_acls = [
            entry for entry in existing_acls.get("acls", [])
            if f"user:{username}" not in entry.get("users", [])
        ]

        data = {"acls": updated_acls}

        return self._make_request("POST", "/acl", data)

    def update_user_acl(self, username, new_ports):
        """Update the ports for an existing user."""
        if f"user:{username}" not in self.list_users():
            return f"User {username} not found in ACL."

        existing_acls = self.get_acls()
        if not existing_acls:
            return "Error fetching current ACLs."

        # Update ports for given user
        for entry in existing_acls.get("acls", []):
            if f"user:{username}" in entry.get("users", []):
                entry["ports"] = new_ports

        data = {"acls": existing_acls["acls"]}

        return self._make_request("POST", "/acl", data)
