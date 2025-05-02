"""
Command audit logging for ACL management commands.
Uses standard file I/O to append to logs/command_audit.log.
"""
import os
import datetime
from pathlib import Path
from typing import List, Optional, Any
from services.logging import logger

# Ensure logs directory exists
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

AUDIT_LOG_FILE = os.path.join(logs_dir, "command_audit.log")

def log_command_audit(author_name, command_name, *args):
    """
    Append an audit log entry to the command audit log file.
    
    Args:
        author_name (str): Name of the user who issued the command
        command_name (str): Name of the command that was executed
        *args: Arguments passed to the command
    """
    try:
        # Format the timestamp
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Format the arguments as a space-separated string
        args_str = " ".join(str(arg) for arg in args)
        
        # Create the log entry
        log_entry = f"{timestamp} | {author_name} | {command_name} | {args_str}\n"
        
        # Append to the log file
        with open(AUDIT_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_entry)
            
    except Exception as e:
        # Log the error using our centralized logger, but don't raise it
        logger.error(f"Failed to write to command audit log: {e}")

def log_command(ctx, command_name: str, args: List[Any]) -> None:
    """
    Log a command execution to the command audit log
    
    Args:
        ctx: The Discord command context
        command_name: The name of the command that was executed
        args: List of argument values passed to the command
    """
    try:
        # Get timestamp in ISO format with Z for UTC
        timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # Get user info, handling potential missing attributes gracefully
        user_id = "unknown"
        try:
            if ctx and hasattr(ctx, 'author') and ctx.author:
                if hasattr(ctx.author, 'name') and ctx.author.name:
                    if hasattr(ctx.author, 'discriminator') and ctx.author.discriminator and ctx.author.discriminator != '0':
                        user_id = f"{ctx.author.name}#{ctx.author.discriminator}"
                    else:
                        user_id = ctx.author.name
                elif hasattr(ctx.author, 'id'):
                    user_id = f"user_{ctx.author.id}"
        except Exception as e:
            logger.warning(f"Error getting user info for audit log: {str(e)}")

        # Format command with arguments
        args_str = " ".join([str(arg) for arg in args if arg is not None])
        command_str = f"!{command_name} {args_str}".strip()
        
        # Format the log line
        log_line = f"[{timestamp}] {user_id} ran {command_str}\n"
        
        # Append to the log file
        with open(AUDIT_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_line)
            
    except Exception as e:
        # Log errors but don't break command execution
        logger.error(f"Failed to write to command audit log: {str(e)}")

def read_last_n_lines(n: int = 10) -> List[str]:
    """
    Read the last n lines from the audit log file.
    
    Args:
        n: Number of lines to read from the end of the file
        
    Returns:
        List of strings containing the last n lines of the audit log
    """
    try:
        # Check if the file exists
        if not os.path.exists(AUDIT_LOG_FILE):
            logger.warning(f"Audit log file does not exist: {AUDIT_LOG_FILE}")
            return []
            
        # Read the file and get the last n lines
        with open(AUDIT_LOG_FILE, "r", encoding="utf-8") as f:
            # Read all lines (this could be optimized for very large files)
            all_lines = f.readlines()
            
        # Get the last n lines or all lines if there are fewer than n
        return all_lines[-n:] if len(all_lines) >= n else all_lines
        
    except Exception as e:
        logger.error(f"Error reading audit log: {str(e)}")
        return [] 