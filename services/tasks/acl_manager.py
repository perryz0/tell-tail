import requests
import os
import json
import difflib
from dotenv import load_dotenv
from services.logging import logger
from services.hooks.webhooks import trigger_webhook

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

    def _log_acl_diff(self, original_acl, updated_acl, operation, username):
        """
        Log the diff between original and updated ACLs after a successful change.
        
        Args:
            original_acl: The original ACL configuration
            updated_acl: The updated ACL configuration
            operation: The operation performed (add, remove, update)
            username: The username that was modified
        """
        try:
            # Convert to pretty-printed JSON strings for comparison
            original_json = json.dumps(original_acl, indent=2, sort_keys=True)
            updated_json = json.dumps(updated_acl, indent=2, sort_keys=True)
            
            # Create a unified diff
            diff = list(difflib.unified_diff(
                original_json.splitlines(),
                updated_json.splitlines(),
                fromfile='Original ACL',
                tofile='Updated ACL',
                lineterm=''
            ))
            
            # Log the changes
            if diff:
                logger.info(f"ACL DIFF ({operation} {username}):")
                for line in diff[:20]:  # Limit to first 20 lines for brevity
                    logger.info(f"  {line}")
                
                if len(diff) > 20:
                    logger.info(f"  ... and {len(diff) - 20} more lines")
            else:
                logger.info(f"No changes detected in ACL ({operation} {username})")
                
        except Exception as e:
            logger.error(f"Error generating ACL diff: {e}")

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

        # Store the original ACL for diff comparison
        original_acl = dict(existing_acls)
        
        # Update the ACL by adding a new user entry
        new_entry = {
            "users": [f"user:{username}"],
            "ports": ports
        }

        updated_acls = existing_acls.get("acls", [])
        updated_acls.append(new_entry)
        data = {"acls": updated_acls}

        logger.info(f"Updating ACL with new entry for user {username}")
        result = self._make_request("POST", "/acl", data)
        
        # Log the diff and trigger webhook if the update was successful
        if result:
            # Get the updated ACLs to compare with the original
            updated_acl = self.get_acls()
            if updated_acl:
                self._log_acl_diff(original_acl, updated_acl, "add", username)
                
                # Trigger webhook
                webhook_payload = {
                    "operation": "add",
                    "username": username,
                    "ports": ports,
                    "tailnet": TAILNET_NAME,
                    "success": True
                }
                trigger_webhook("acl.user.added", webhook_payload)
        
        return result

    def remove_user_from_acl(self, username):
        """Remove a user from the ACL."""
        logger.info(f"Removing user {username} from ACL")
        existing_acls = self.get_acls()
        if not existing_acls:
            logger.error("Failed to fetch current ACLs")
            return "Error fetching current ACLs."

        # Store the original ACL for diff comparison
        original_acl = dict(existing_acls)
        
        # Find user's current ports for webhook payload
        current_ports = []
        for entry in existing_acls.get("acls", []):
            if f"user:{username}" in entry.get("users", []):
                current_ports = entry.get("ports", [])
                break
        
        # Filter out user from existing ACLs
        updated_acls = [
            entry for entry in existing_acls.get("acls", [])
            if f"user:{username}" not in entry.get("users", [])
        ]

        data = {"acls": updated_acls}
        logger.info(f"Updating ACL after removing user {username}")
        result = self._make_request("POST", "/acl", data)
        
        # Log the diff and trigger webhook if the update was successful
        if result:
            # Get the updated ACLs to compare with the original
            updated_acl = self.get_acls()
            if updated_acl:
                self._log_acl_diff(original_acl, updated_acl, "remove", username)
                
                # Trigger webhook
                webhook_payload = {
                    "operation": "remove",
                    "username": username,
                    "ports": current_ports,
                    "tailnet": TAILNET_NAME,
                    "success": True
                }
                trigger_webhook("acl.user.removed", webhook_payload)
        
        return result

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

        # Store the original ACL for diff comparison
        original_acl = dict(existing_acls)
        
        # Find old ports for webhook payload
        old_ports = []
        for entry in existing_acls.get("acls", []):
            if f"user:{username}" in entry.get("users", []):
                old_ports = entry.get("ports", [])
                entry["ports"] = new_ports
                break

        data = {"acls": existing_acls["acls"]}
        logger.info(f"Updating ACL with new ports for user {username}")
        result = self._make_request("POST", "/acl", data)
        
        # Log the diff and trigger webhook if the update was successful
        if result:
            # Get the updated ACLs to compare with the original
            updated_acl = self.get_acls()
            if updated_acl:
                self._log_acl_diff(original_acl, updated_acl, "update", username)
                
                # Trigger webhook
                webhook_payload = {
                    "operation": "update",
                    "username": username,
                    "old_ports": old_ports,
                    "new_ports": new_ports,
                    "tailnet": TAILNET_NAME,
                    "success": True
                }
                trigger_webhook("acl.user.updated", webhook_payload)
        
        return result
