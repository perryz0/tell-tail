import requests
import os
from dotenv import load_dotenv
from services.logging import logger

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
        logger.info(f"ACLManager initialized for tailnet: {TAILNET_NAME}")

    def _make_request(self, method, endpoint, data=None):
        try:
            url = f"{self.base_url}{endpoint}"
            logger.debug(f"Making {method} request to {url}")
            response = requests.request(method, url, headers=self.headers, json=data)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error in API request: {e}")
            return None

    def get_acls(self):
        """Fetch the current ACL configuration."""
        logger.info("Fetching current ACL configuration")
        return self._make_request("GET", "/acl")

    def list_acl_roles(self):
        """List all user roles in the current ACL."""
        logger.info("Listing all user roles in current ACL")
        acls = self.get_acls()
        if acls:
            users = [entry['users'] for entry in acls.get('acls', [])]
            return [user for sublist in users for user in sublist]
        return []
    
    def list_tailnet_users(self):
        """List all active users on the Tailnet."""
        logger.info("Listing all active users on the Tailnet")
        endpoint = "/devices"
        response = self._make_request("GET", endpoint)
        if not response or "devices" not in response:
            logger.warning("No devices found in Tailnet response")
            return []

        # Extract unique usernames from device data
        active_users = {device.get("hostname") for device in response["devices"]}
        logger.info(f"Found {len(active_users)} active users")
        return list(active_users)

    def add_user_to_acl(self, username, ports=None):
        """Add or update a user in the ACL with specified ports."""
        if ports is None:
            ports = ["22/tcp"]  # Defaulting to SSH port 22 for now

        logger.info(f"Adding user {username} to ACL with ports: {ports}")

        # First check if user is an EXISTING member of the Tailnet
        active_users = self.list_tailnet_users()
        if username not in active_users:
            logger.warning(f"User {username} is not an active member of the Tailnet")
            return f"Error: {username} is not an active member of the Tailnet."

        existing_acls = self.get_acls()
        if not existing_acls:
            logger.error("Failed to fetch current ACLs")
            return "Error fetching current ACLs."

        # Check if user already exists in the ACL
        if f"user:{username}" in self.list_acl_roles():
            logger.warning(f"User {username} already exists in ACL")
            return f"User {username} already exists in ACL."

        # Update the ACL by adding a new user entry
        new_entry = {
            "users": [f"user:{username}"],
            "ports": ports
        }

        updated_acls = existing_acls.get("acls", [])
        updated_acls.append(new_entry)
        data = {"acls": updated_acls}

        logger.info(f"Updating ACL with new entry for user {username}")
        return self._make_request("POST", "/acl", data)

    def remove_user_from_acl(self, username):
        """Remove a user from the ACL."""
        logger.info(f"Removing user {username} from ACL")
        existing_acls = self.get_acls()
        if not existing_acls:
            logger.error("Failed to fetch current ACLs")
            return "Error fetching current ACLs."

        # Filter out user from existing ACLs
        updated_acls = [
            entry for entry in existing_acls.get("acls", [])
            if f"user:{username}" not in entry.get("users", [])
        ]

        data = {"acls": updated_acls}
        logger.info(f"Updating ACL after removing user {username}")
        return self._make_request("POST", "/acl", data)

    def update_user_acl(self, username, new_ports):
        """Update the ports for an existing user."""
        logger.info(f"Updating ports for user {username} to {new_ports}")
        if f"user:{username}" not in self.list_acl_roles():
            logger.warning(f"User {username} not found in ACL")
            return f"User {username} not found in ACL."

        existing_acls = self.get_acls()
        if not existing_acls:
            logger.error("Failed to fetch current ACLs")
            return "Error fetching current ACLs."

        # Update ports for given user
        for entry in existing_acls.get("acls", []):
            if f"user:{username}" in entry.get("users", []):
                entry["ports"] = new_ports

        data = {"acls": existing_acls["acls"]}
        logger.info(f"Updating ACL with new ports for user {username}")
        return self._make_request("POST", "/acl", data)
