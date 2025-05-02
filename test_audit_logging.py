"""
Test script to verify command audit logging functionality.
"""
from services.logging.audit import log_command_audit
import os
from pathlib import Path

def test_audit_logging():
    """Test the audit logging functionality by writing sample entries."""
    # Create some sample audit entries
    log_command_audit("test_user1", "adduser", "someuser", "22/tcp,80/tcp")
    log_command_audit("test_user2", "removeuser", "olduser")
    log_command_audit("test_user1", "updateuser", "someuser", "443/tcp,8080/tcp")
    
    # Check if the file was created
    from services.logging.audit import AUDIT_LOG_FILE
    
    if os.path.exists(AUDIT_LOG_FILE):
        print(f"✅ Audit log file created at: {AUDIT_LOG_FILE}")
        
        # Read and print the contents
        with open(AUDIT_LOG_FILE, "r", encoding="utf-8") as f:
            content = f.read()
            print("\nLog contents:")
            print("-------------")
            print(content)
    else:
        print(f"❌ Audit log file was not created at: {AUDIT_LOG_FILE}")

if __name__ == "__main__":
    test_audit_logging() 