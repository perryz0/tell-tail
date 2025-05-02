# tailscale-alert
Discord bot for tailscale-based team workflows.

# TellTail - Tailscale Network Manager

TellTail is a web and Discord bot interface for managing Tailscale networks, allowing you to control device access, monitor connections, and manage ACLs through both Discord commands and a web dashboard.

## Features

- Discord bot for Tailscale network management
- Web dashboard with Discord OAuth authentication
- ACL management (add/remove users, set expiration times)
- Device monitoring with status updates
- Secure API with authentication

## Docker Setup

### Prerequisites

- Docker and Docker Compose installed
- A Tailscale network with API access
- A Discord application with OAuth2 configured

### Quick Start

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/tell-tail.git
   cd tell-tail
   ```

2. Create a `.env` file from the template:
   ```
   cp .env.example .env
   ```

3. Edit the `.env` file with your credentials:
   - Tailscale API token
   - Discord bot token
   - Discord OAuth client ID and secret
   - Other configuration options

4. Start the application with Docker Compose:
   ```
   chmod +x docker_start.sh
   ./docker_start.sh
   ```
   
   Or manually with:
   ```
   docker-compose up -d
   ```

5. Access the web dashboard at http://localhost:5000

## Web Dashboard

The web dashboard provides a user-friendly interface for managing your Tailscale network:

- View all devices in your tailnet
- Monitor device online/offline status
- Add and remove users from ACLs
- Set time-limited access for temporary users

## Configuration Options

Configuration is handled through environment variables in the `.env` file:

| Variable | Description |
|----------|-------------|
| `TAILSCALE_API_TOKEN` | Your Tailscale API token |
| `TAILNET_NAME` | Your Tailscale network name |
| `DISCORD_BOT_TOKEN` | Your Discord bot token |
| `DISCORD_CLIENT_ID` | Discord OAuth application client ID |
| `DISCORD_CLIENT_SECRET` | Discord OAuth application client secret |
| `ALLOWED_DISCORD_IDS` | Comma-separated list of authorized Discord user IDs |
| `ALLOWED_ORIGINS` | Comma-separated list of allowed CORS origins |

## Development

For local development without Docker:

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Run the Flask development server:
   ```
   python -m web.server
   ```

## Security Notes

- Only users with Discord IDs in the `ALLOWED_DISCORD_IDS` list can access the API
- API endpoints are protected with OAuth authentication
- CORS is configured to allow only specified origins

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
