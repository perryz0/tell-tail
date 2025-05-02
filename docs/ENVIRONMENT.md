# TellTail Environment Configuration

This document outlines all environment variables used by the TellTail bot and explains how to configure them.

## Core Configuration

These variables are required for basic functionality:

| Variable | Description | Example |
|----------|-------------|---------|
| `DISCORD_BOT_TOKEN` | Discord API token for your bot | `abcdefg123456789` |
| `TAILSCALE_API_TOKEN` | Tailscale API key for accessing your tailnet | `tskey-api-abcdef123456` |
| `TAILNET_NAME` | Your Tailscale tailnet name | `company.github` |

## Admin Configuration

These variables control admin access to sensitive commands:

| Variable | Description | Example |
|----------|-------------|---------|
| `AUDIT_ADMINS` | Comma-separated list of Discord user IDs allowed to access audit logs | `123456789012345678,234567890123456789` |

## Feature Configuration

These variables enable or configure specific features:

| Variable | Description | Example |
|----------|-------------|---------|
| `NOTIFICATION_CHANNEL_ID` | Discord channel ID to receive device notifications | `123456789012345678` |
| `TELLTAIL_WEBHOOK_URL` | URL for webhook integration (optional) | `https://hooks.example.com/webhook` |

## How to Find Discord IDs

To find a Discord user ID:

1. Enable Developer Mode in Discord (User Settings → Advanced → Developer Mode)
2. Right-click on a user and select "Copy ID"

To find a Discord channel ID:

1. Enable Developer Mode in Discord
2. Right-click on a channel and select "Copy ID"

## Sample .env File

```
# Core Configuration
DISCORD_BOT_TOKEN=your_discord_bot_token
TAILSCALE_API_TOKEN=your_tailscale_api_token
TAILNET_NAME=your_tailnet_name

# Admin Configuration
AUDIT_ADMINS=123456789012345678,234567890123456789

# Feature Configuration
NOTIFICATION_CHANNEL_ID=123456789012345678
TELLTAIL_WEBHOOK_URL=https://hooks.example.com/webhook 