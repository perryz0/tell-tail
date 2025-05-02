"""
Test script to check audit log admin access configuration.
This helps confirm that the AUDIT_ADMINS environment variable is set up correctly.
"""
import os
from dotenv import load_dotenv
from services.logging import logger
from services.logging.audit import log_command_audit, AUDIT_LOG_FILE

def test_audit_admin_access():
    """Test the audit log access configuration."""
    # Load environment variables
    load_dotenv()
    
    # Check if AUDIT_ADMINS is configured
    audit_admins = os.getenv("AUDIT_ADMINS", "")
    
    # For testing, if no AUDIT_ADMINS is set, create a test one
    if not audit_admins and len(os.sys.argv) > 1 and os.sys.argv[1] == "--test":
        test_admin_id = "123456789012345678"
        os.environ["AUDIT_ADMINS"] = test_admin_id
        audit_admins = test_admin_id
        print("⚠️ Using a test admin ID for demonstration purposes only.")
    
    print("\n== Audit Log Admin Access Test ==\n")
    
    if not audit_admins:
        print("❌ AUDIT_ADMINS environment variable is not set.")
        print("No users will be able to access the audit log via Discord.")
        print("\nTo enable access, add this to your .env file:")
        print("AUDIT_ADMINS=123456789012345678,234567890123456789")
        print("\nReplace the numbers with the Discord user IDs of your administrators.")
        print("\nRun this script with --test to see a demonstration with a test admin ID:")
        print("python test_auditlog_access.py --test")
    else:
        admin_ids = [admin_id.strip() for admin_id in audit_admins.split(",") if admin_id.strip()]
        print(f"✅ AUDIT_ADMINS is configured with {len(admin_ids)} admin user(s):")
        for i, admin_id in enumerate(admin_ids, 1):
            print(f"  {i}. {admin_id}")
    
    # Check if audit log file exists
    print("\n== Audit Log File Status ==\n")
    
    if os.path.exists(AUDIT_LOG_FILE):
        # Count lines in file
        with open(AUDIT_LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
            line_count = len(lines)
        
        print(f"✅ Audit log file exists at: {AUDIT_LOG_FILE}")
        print(f"   Contains {line_count} log entries")
        
        # Show the last 3 entries if available
        if line_count > 0:
            print("\nLast few entries:")
            for line in lines[-3:]:
                print(f"   {line.strip()}")
    else:
        print(f"❌ Audit log file not found at: {AUDIT_LOG_FILE}")
        print("   The file will be created when the first audited command is executed.")
        
        # Create a test entry
        print("\nCreating a test audit log entry...")
        log_command_audit("test_script", "test_command", "arg1", "arg2")
        
        if os.path.exists(AUDIT_LOG_FILE):
            print("✅ Test entry created successfully!")
        else:
            print("❌ Failed to create test entry.")
    
    print("\n== How to Use the Audit Log Command ==\n")
    print("In Discord, administrators can use:")
    print("!auditlog [lines]")
    print("\nExample: !auditlog 20")
    print("This will show the last 20 entries in the audit log.")
    
    # Simulate audit log command behavior for testing
    if audit_admins and len(os.sys.argv) > 1 and os.sys.argv[1] == "--test":
        print("\n== Simulating Audit Log Command Behavior ==\n")
        print("When an admin uses the !auditlog command in Discord:")
        
        # Get last 5 log entries for demonstration
        if os.path.exists(AUDIT_LOG_FILE):
            with open(AUDIT_LOG_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()
                entries = lines[-5:] if lines else []
            
            if entries:
                print("\n🔒 **ADMIN: Command Audit Log**")
                print("```")
                for entry in entries:
                    print(entry.strip())
                print("```")
            else:
                print("📝 No audit log entries found.")
        else:
            print("📝 No audit log file found.")
        
        print("\nWhen a non-admin tries to use the command:")
        print("❌ You do not have permission to use this command.")

if __name__ == "__main__":
    test_audit_admin_access() 