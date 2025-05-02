"""
Command audit logging for ACL management commands.
Uses standard file I/O to append to logs/command_audit.log.
"""
import os
import datetime
from pathlib import Path
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