"""
Test script to verify webhook integration and ACL diff logging.
This script simulates ACL operations and ensures webhooks are triggered.
"""
import os
from services.tasks.acl_manager import ACLManager
from services.hooks.webhooks import trigger_webhook
from services.logging import logger

def simulate_acl_operations():
    """Test ACL operations with webhook integration."""
    # Set up test user
    test_username = "test_device"
    
    # Initialize ACL manager
    acl_manager = ACLManager()
    
    # Directly test webhook trigger
    logger.info("Testing direct webhook trigger...")
    test_payload = {
        "operation": "test",
        "username": test_username,
        "tailnet": os.getenv("TAILNET_NAME"),
        "ports": ["22/tcp", "443/tcp"],
        "success": True
    }
    trigger_webhook("acl.test", test_payload)
    
    # Run through a full cycle of ACL operations if a test user is in the tailnet
    tailnet_users = acl_manager.list_tailnet_users()
    if test_username in tailnet_users:
        logger.info(f"Test user '{test_username}' found in tailnet. Testing ACL operations...")
        
        # Test adding user
        logger.info(f"Testing add_user_to_acl for {test_username}...")
        result = acl_manager.add_user_to_acl(test_username, ["22/tcp", "80/tcp"])
        logger.info(f"Add user result: {result}")
        
        # Test updating user
        logger.info(f"Testing update_user_acl for {test_username}...")
        result = acl_manager.update_user_acl(test_username, ["443/tcp", "8080/tcp"])
        logger.info(f"Update user result: {result}")
        
        # Test removing user
        logger.info(f"Testing remove_user_from_acl for {test_username}...")
        result = acl_manager.remove_user_from_acl(test_username)
        logger.info(f"Remove user result: {result}")
    else:
        logger.warning(f"Test user '{test_username}' not found in tailnet. Skipping ACL operations tests.")
        logger.info("To test with a real user, make sure a device named 'test_device' exists in your tailnet.")
        logger.info("You can also change the test_username variable in this script to match an existing device.")
    
    logger.info("Webhook integration test completed.")

if __name__ == "__main__":
    simulate_acl_operations() 