# tailscale-alert
Discord bot for tailscale-based team workflows.

# TellTail - Tailscale ACL Management Bot

A Discord bot for managing Tailscale network ACLs.

## Audit Logging

TellTail includes comprehensive audit logging for all ACL management commands. This provides accountability and helps track changes to your Tailscale network.

### Command Audit Logs

All ACL management commands (add, remove, update) are logged to `logs/command_audit.log` with the following information:
- Timestamp
- User who issued the command
- Command name
- Arguments passed

### Admin Access to Audit Logs

To view audit logs directly in Discord, use the `!auditlog [lines]` command:

```
!auditlog 15  # Shows the last 15 lines of the audit log
```

This command is restricted to administrators only. To configure admin access:

1. Get the Discord user IDs of your administrators
2. Add them to your `.env` file as a comma-separated list:

```
AUDIT_ADMINS=123456789012345678,234567890123456789
```

Only users with IDs in this list will be able to access the audit logs via Discord.
