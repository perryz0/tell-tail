"""
API endpoints for TellTail bot.
Provides HTTP access to Tailscale devices and ACL management.
"""

import json
from flask import Blueprint, jsonify, request, current_app
from services.api.TailscaleAPI import TailscaleAPI
from services.tasks.acl_manager import ACLManager
from services.logging import logger
from typing import Dict, Any, Optional, List, Union

# Create a Flask blueprint for API routes
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Initialize services
acl_manager = ACLManager()

# Helper function to handle API responses
def api_response(success: bool, message: str = "", data: Any = None, status_code: int = 200) -> tuple:
    """
    Create a standardized API response.
    
    Args:
        success: Whether the operation was successful
        message: Optional message to include in the response
        data: Optional data to include in the response
        status_code: HTTP status code to return
        
    Returns:
        Tuple of (response_json, status_code)
    """
    response = {
        "success": success,
    }
    
    if message:
        response["message"] = message
        
    if data is not None:
        response["data"] = data
        
    return jsonify(response), status_code


@api_bp.route('/devices', methods=['GET'])
def get_devices():
    """
    Get all devices in the Tailnet.
    
    Returns:
        JSON list of devices
    """
    try:
        # Get the TailscaleAPI instance
        ts = current_app.config.get('ts_api')
        if not ts:
            logger.error("TailscaleAPI not available in current_app config")
            return api_response(False, "Internal server error", status_code=500)
        
        # Get the tailnet name
        tailnet = current_app.config.get('tailnet')
        if not tailnet:
            logger.error("Tailnet name not available in current_app config")
            return api_response(False, "Internal server error", status_code=500)
            
        # Get devices from Tailscale API
        devices_response = ts.list_devices(tailnet)
        
        if not devices_response or "devices" not in devices_response:
            return api_response(False, "Failed to retrieve devices", status_code=400)
            
        # Return the device list as JSON
        return api_response(True, "Devices retrieved successfully", devices_response["devices"])
        
    except Exception as e:
        logger.error(f"Error getting devices: {str(e)}")
        return api_response(False, "Failed to retrieve devices", status_code=500)


@api_bp.route('/acls', methods=['GET'])
def get_acls():
    """
    Get all ACLs in the Tailnet.
    
    Returns:
        JSON representation of ACLs
    """
    try:
        # Get ACLs from ACL manager
        acls = acl_manager.get_acls()
        
        if not acls:
            return api_response(False, "Failed to retrieve ACLs", status_code=400)
            
        # Return the ACLs as JSON
        return api_response(True, "ACLs retrieved successfully", acls)
        
    except Exception as e:
        logger.error(f"Error getting ACLs: {str(e)}")
        return api_response(False, "Failed to retrieve ACLs", status_code=500)


@api_bp.route('/acl/add', methods=['POST'])
def add_user_to_acl():
    """
    Add a user to the ACL.
    
    Expected JSON body:
    {
        "username": "string",
        "ports": "string" or ["string"],
        "ttl_hours": integer (optional)
    }
    
    Returns:
        JSON response indicating success or failure
    """
    try:
        # Get and validate request data
        data = request.get_json()
        
        if not data:
            return api_response(False, "Invalid request: Missing JSON body", status_code=400)
            
        # Validate required fields
        username = data.get('username')
        if not username or not isinstance(username, str):
            return api_response(False, "Invalid username", status_code=400)
            
        # Get optional fields with defaults
        ports = data.get('ports', "22/tcp")
        ttl_hours = data.get('ttl_hours')
        
        # Validate ttl_hours if provided
        if ttl_hours is not None:
            try:
                ttl_hours = int(ttl_hours)
                if ttl_hours <= 0:
                    return api_response(False, "TTL hours must be a positive integer", status_code=400)
            except (ValueError, TypeError):
                return api_response(False, "TTL hours must be a positive integer", status_code=400)
        
        # Call ACL manager to add the user
        result = acl_manager.add_user_to_acl(username, ports, ttl_hours)
        
        # Check result for common error messages
        if isinstance(result, str) and "Error" in result:
            return api_response(False, result, status_code=400)
            
        return api_response(True, f"User {username} added to ACL", status_code=201)
        
    except Exception as e:
        logger.error(f"Error adding user to ACL: {str(e)}")
        return api_response(False, "Failed to add user to ACL", status_code=500)


@api_bp.route('/acl/remove', methods=['POST'])
def remove_user_from_acl():
    """
    Remove a user from the ACL.
    
    Expected JSON body:
    {
        "username": "string"
    }
    
    Returns:
        JSON response indicating success or failure
    """
    try:
        # Get and validate request data
        data = request.get_json()
        
        if not data:
            return api_response(False, "Invalid request: Missing JSON body", status_code=400)
            
        # Validate required fields
        username = data.get('username')
        if not username or not isinstance(username, str):
            return api_response(False, "Invalid username", status_code=400)
        
        # Call ACL manager to remove the user
        result = acl_manager.remove_user_from_acl(username)
        
        # Check result for common error messages
        if isinstance(result, str) and "Error" in result:
            return api_response(False, result, status_code=400)
            
        return api_response(True, f"User {username} removed from ACL")
        
    except Exception as e:
        logger.error(f"Error removing user from ACL: {str(e)}")
        return api_response(False, "Failed to remove user from ACL", status_code=500) 