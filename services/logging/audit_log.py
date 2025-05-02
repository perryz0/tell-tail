"""
Centralized command audit logger for tracking command usage
"""
import os
import datetime
from typing import List, Optional
from services.logging import logger

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

# Path to the audit log file
AUDIT_LOG_PATH = "logs/command_audit.log"

def log_command(ctx, command_name: str, args: List[str]) -> None:
    """
    Log a command execution to the command audit log
    
    Args:
        ctx: The Discord command context
        command_name: The name of the command that was executed
        args: List of argument strings passed to the command
    """
    try:
        # Get timestamp in ISO format with Z for UTC
        timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # Get user info, handling potential missing attributes gracefully
        user_id = "unknown"
        try:
            if ctx and hasattr(ctx, 'author') and ctx.author:
                if hasattr(ctx.author, 'name') and ctx.author.name:
                    if hasattr(ctx.author, 'discriminator') and ctx.author.discriminator:
                        user_id = f"{ctx.author.name}#{ctx.author.discriminator}"
                    else:
                        user_id = ctx.author.name
                elif hasattr(ctx.author, 'id'):
                    user_id = f"user_{ctx.author.id}"
        except Exception as e:
            logger.warning(f"Error getting user info for audit log: {str(e)}")

        # Format command with arguments
        command_str = f"!{command_name}"
        if args:
            args_str = " ".join([str(arg) for arg in args])
            command_str = f"{command_str} {args_str}"
        
        # Format the log line
        log_line = f"[{timestamp}] {user_id} ran {command_str}\n"
        
        # Append to the log file
        with open(AUDIT_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(log_line)
            
    except Exception as e:
        # Log errors but don't break command execution
        logger.error(f"Failed to write to command audit log: {str(e)}") 