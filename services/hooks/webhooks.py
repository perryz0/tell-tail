"""
Webhook integration for TellTail events.
This module allows sending event notifications to external services.
"""

import json
import os
from typing import Dict, Any, List, Optional
from services.logging import logger

# Environment variables for webhook configuration
WEBHOOKS_ENABLED = os.getenv("WEBHOOKS_ENABLED", "false").lower() in ("true", "1", "yes")
WEBHOOK_URLS = {}  # Will be populated from config in the future

# Define event types that can be triggered
VALID_EVENT_TYPES = [
    "acl.user.added",
    "acl.user.removed",
    "acl.user.updated",
    "acl.user.expired",
    "device.joined",
    "device.left",
    "device.status_changed"
]

def trigger_webhook(event_type: str, payload: Dict[str, Any]) -> bool:
    """
    Trigger a webhook for the specified event type.
    
    Args:
        event_type: The type of event that occurred (e.g., 'acl.user.added')
        payload: Dictionary containing event data
        
    Returns:
        bool: True if the webhook was triggered successfully, False otherwise
    """
    try:
        # Validate event type
        if event_type not in VALID_EVENT_TYPES:
            logger.warning(f"Invalid event type for webhook: {event_type}")
            return False
            
        # Log the webhook event and payload
        logger.info(f"Webhook event triggered: {event_type}")
        logger.debug(f"Webhook payload: {json.dumps(payload)}")
        
        # If webhooks are not enabled, just log and return
        if not WEBHOOKS_ENABLED:
            logger.debug(f"Webhooks are disabled. Not sending {event_type} event.")
            return True
            
        # TODO: Implement actual webhook sending logic using requests
        # This is a stub for future implementation
        
        # Example of how this would be implemented:
        # if event_type in WEBHOOK_URLS:
        #     for url in WEBHOOK_URLS[event_type]:
        #         response = requests.post(
        #             url,
        #             json={
        #                 "event_type": event_type,
        #                 "payload": payload
        #             },
        #             headers={"Content-Type": "application/json"}
        #         )
        #         logger.debug(f"Webhook response: {response.status_code}")
        
        logger.info(f"Webhook for {event_type} processed successfully (stub)")
        return True
        
    except Exception as e:
        logger.error(f"Error triggering webhook for {event_type}: {str(e)}")
        return False


def register_webhook(event_type: str, url: str) -> bool:
    """
    Register a webhook URL for a specific event type.
    This is a stub for future implementation.
    
    Args:
        event_type: The type of event to subscribe to
        url: The webhook URL to call when the event occurs
        
    Returns:
        bool: True if the webhook was registered successfully, False otherwise
    """
    try:
        # Validate event type
        if event_type not in VALID_EVENT_TYPES:
            logger.warning(f"Cannot register webhook for invalid event type: {event_type}")
            return False
            
        # Initialize the list for this event type if it doesn't exist
        if event_type not in WEBHOOK_URLS:
            WEBHOOK_URLS[event_type] = []
            
        # Add the URL if it's not already registered
        if url not in WEBHOOK_URLS[event_type]:
            WEBHOOK_URLS[event_type].append(url)
            logger.info(f"Registered webhook for {event_type}: {url}")
            
        return True
        
    except Exception as e:
        logger.error(f"Error registering webhook: {str(e)}")
        return False 