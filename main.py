from typing import Final

import discord
from discord.ext import commands, tasks
import os
from dotenv import load_dotenv
from services.api.TailscaleAPI import TailscaleAPI
from services import acl_commands
from settings.bot_context import BotContext
from services.logging import logger
import asyncio


# Load .env variables
load_dotenv()
DISCORD_TOKEN: Final[str] = os.getenv('DISCORD_BOT_TOKEN')
TAILNET_NAME = os.getenv("TAILNET_NAME")

# API and BOT setup
TAILSCALE_TOKEN: Final[str] = os.getenv('TAILSCALE_API_TOKEN')
ts = TailscaleAPI(api_token=TAILSCALE_TOKEN)
intents = discord.Intents.all()
intents.message_content = True

client = commands.Bot(command_prefix="!", intents=intents)
context: BotContext = BotContext()


# Basic event handlers
@client.event
async def on_ready():
    logger.info(f"Logged in as {client.user}")
    logger.info("Connected guilds:")
    for guild in client.guilds:
        logger.info(f"- {guild.name} (ID: {guild.id})")
    # Start background tasks
    monitor_tailnet_changes.start()


@client.command(name="ping", help="Check if the bot is running")
async def ping(ctx):
    await ctx.send("Pong! The bot is running.")

# Command: List Devices
@client.command(name="list_devices", help="List all devices on the Tailscale network")
async def list_devices(ctx):
    try:
        devices_response = ts.list_devices(context.tailnet)
        
        # Check if res is None or not properly structured
        if not devices_response or "devices" not in devices_response:
            await ctx.send("No devices found on the Tailscale network.")
            return
        
        devices = devices_response["devices"]

        device_list = "\n".join([f"- {device['hostname']} ({device['addresses'][0]})" for device in devices])
        await ctx.send(f"Devices on Tailscale:\n{device_list}")
    except Exception as e:
        logger.error(f"Error listing devices: {e}")
        await ctx.send("Failed to retrieve device list.")


# Background Task: Monitor Tailnet Changes
@tasks.loop(minutes=1)
async def monitor_tailnet_changes():
    """
    Periodically check for changes in the Tailscale network and detect device joins/leaves.
    """
    try:
        # Get current devices from Tailscale API
        devices_response = ts.list_devices(context.tailnet)
        if not devices_response or "devices" not in devices_response:
            logger.warning("No devices found in tailnet or API response error")
            return
            
        current_devices = devices_response["devices"]
        current_device_map = {device['id']: device for device in current_devices}
        
        # Initialize devices_cache on first run
        if not context.devices_cache:
            logger.info(f"Initializing device cache with {len(current_devices)} devices")
            context.devices_cache = current_device_map
            return
        
        # Get notification channel if configured
        notification_channel = None
        if context.notification_channel_id:
            try:
                notification_channel = client.get_channel(int(context.notification_channel_id))
                if not notification_channel:
                    logger.warning(f"Could not find notification channel with ID {context.notification_channel_id}")
            except ValueError:
                logger.error(f"Invalid notification channel ID: {context.notification_channel_id}")
            
        # Check for new devices (joined)
        for device_id, device in current_device_map.items():
            if device_id not in context.devices_cache:
                hostname = device.get('hostname', 'Unknown')
                addresses = device.get('addresses', ['No IP'])
                message = f"🟢 Device joined tailnet: {hostname} ({addresses[0]})"
                logger.info(message)
                
                # Send notification to Discord if channel exists
                if notification_channel:
                    try:
                        await notification_channel.send(message)
                    except Exception as e:
                        logger.error(f"Failed to send join notification to Discord: {e}")
        
        # Check for devices that left
        for device_id, device in context.devices_cache.items():
            if device_id not in current_device_map:
                hostname = device.get('hostname', 'Unknown')
                addresses = device.get('addresses', ['No IP'])
                message = f"🔴 Device left tailnet: {hostname} ({addresses[0]})"
                logger.info(message)
                
                # Send notification to Discord if channel exists
                if notification_channel:
                    try:
                        await notification_channel.send(message)
                    except Exception as e:
                        logger.error(f"Failed to send leave notification to Discord: {e}")
        
        # Update the cache with current devices
        context.devices_cache = current_device_map
        
    except Exception as e:
        logger.error(f"Error monitoring Tailnet: {e}")

# Error Handling: Command Errors
@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Unknown command. Use `!help` to see available commands.")
    else:
        logger.error(f"Error occurred: {error}")
        await ctx.send("An unexpected error occurred. Please check the logs.")


# Tailscale ACL Handling for privilege separation and access control
@client.command(name="adduser", help="Add a user to the ACL")
async def adduser(ctx, username: str, ports: str = "22/tcp"):
    await acl_commands.add_user(ctx, username, ports)

@client.command(name="removeuser", help="Remove a user from the ACL")
async def removeuser(ctx, username: str):
    await acl_commands.remove_user(ctx, username)

@client.command(name="listusers", help=f"List all current users in `{TAILNET_NAME}`")
async def listusers(ctx):
    await acl_commands.list_tailnet_users(ctx)

# TODO: fine-grained ACL display coming soon...
@client.command(name="listroles", help="List all current user roles in `{TAILNET_NAME}` with SSH access")
async def listroles(ctx):
    await acl_commands.list_acl_roles(ctx)

@client.command(name="updateuser", help="Update user ACL ports")
async def updateuser(ctx, username: str, ports: str):
    await acl_commands.update_user(ctx, username, ports)

@client.command(name="set_notification_channel", help="Set the current channel for device notifications")
async def set_notification_channel(ctx):
    """Set the current channel as the notification channel for device changes."""
    try:
        # Update the context with the current channel ID
        context.notification_channel_id = str(ctx.channel.id)
        
        # Save to environment variable (won't persist after restart)
        os.environ["NOTIFICATION_CHANNEL_ID"] = str(ctx.channel.id)
        
        logger.info(f"Notification channel set to #{ctx.channel.name} ({ctx.channel.id})")
        await ctx.send(f"✅ This channel (#{ctx.channel.name}) will now receive device connection notifications.")
    except Exception as e:
        logger.error(f"Error setting notification channel: {e}")
        await ctx.send("❌ Failed to set notification channel.")

@client.command(name="monitor_status", help="Show monitoring status and tracked devices")
async def monitor_status(ctx):
    """Display the current monitoring status and devices being tracked."""
    try:
        if not context.devices_cache:
            await ctx.send("⚠️ Device monitoring is not yet initialized. It will start on the next monitoring cycle.")
            return
        
        # Get notification channel info
        notification_info = "Notifications: Disabled"
        if context.notification_channel_id:
            channel = client.get_channel(int(context.notification_channel_id))
            if channel:
                notification_info = f"Notifications: Enabled in #{channel.name}"
            else:
                notification_info = f"Notifications: Configured but channel not found (ID: {context.notification_channel_id})"
        
        # Count and list devices
        device_count = len(context.devices_cache)
        device_list = "\n".join(
            [f"- {device.get('hostname', 'Unknown')} ({device.get('addresses', ['No IP'])[0]})" 
             for device in context.devices_cache.values()]
        )
        
        # Create and send the status message
        status_message = f"""📊 **Tailnet Monitoring Status**
Tailnet: `{context.tailnet}`
{notification_info}
Tracking {device_count} devices:
{device_list}
"""
        await ctx.send(status_message)
    except Exception as e:
        logger.error(f"Error showing monitor status: {e}")
        await ctx.send("❌ Failed to show monitoring status.")

@client.command(name="device_status", help="Check if a specific device is currently online")
async def device_status(ctx, device_name: str):
    """Check if a specific device is online in the tailnet."""
    try:
        if not context.devices_cache:
            await ctx.send("⚠️ Device monitoring is not yet initialized. Please try again in a moment.")
            return
        
        # Search for the device by hostname (case-insensitive)
        device_name_lower = device_name.lower()
        found_devices = [
            device for device in context.devices_cache.values() 
            if device.get('hostname', '').lower() == device_name_lower
        ]
        
        if not found_devices:
            # Try partial match if no exact match found
            found_devices = [
                device for device in context.devices_cache.values() 
                if device_name_lower in device.get('hostname', '').lower()
            ]
            
            if not found_devices:
                await ctx.send(f"❌ No device found with name '{device_name}'")
                return
            elif len(found_devices) > 1:
                # Multiple matches found
                device_list = "\n".join([f"- {device.get('hostname', 'Unknown')}" for device in found_devices])
                await ctx.send(f"ℹ️ Multiple devices found matching '{device_name}':\n{device_list}")
                return
        
        # Get the device details
        device = found_devices[0]
        hostname = device.get('hostname', 'Unknown')
        ip_address = device.get('addresses', ['No IP'])[0]
        is_online = device.get('online', False)
        last_seen = device.get('lastSeen', 'Unknown')
        
        status_emoji = "🟢" if is_online else "🔴"
        status_text = "Online" if is_online else "Offline"
        
        # Send the status message
        status_message = f"""**Device Status: {hostname}**
{status_emoji} Status: {status_text}
📍 IP: {ip_address}
🕒 Last Seen: {last_seen}
"""
        await ctx.send(status_message)
    except Exception as e:
        logger.error(f"Error checking device status: {e}")
        await ctx.send("❌ Failed to check device status.")

@client.command(name="audit_log", help="View recent command audit logs")
async def audit_log(ctx, lines: int = 10):
    """Show recent command audit log entries."""
    try:
        # Check if the log file exists
        from services.logging.audit import AUDIT_LOG_FILE
        import os
        
        if not os.path.exists(AUDIT_LOG_FILE):
            await ctx.send("📝 No audit log entries found. The log file hasn't been created yet.")
            return
        
        # Limit the number of lines for safety
        max_lines = 50
        if lines > max_lines:
            lines = max_lines
            await ctx.send(f"⚠️ Limiting output to {max_lines} lines for safety.")
        
        # Read the last N lines of the file
        entries = []
        with open(AUDIT_LOG_FILE, "r", encoding="utf-8") as f:
            # Simple approach to get last N lines
            all_lines = f.readlines()
            entries = all_lines[-lines:] if lines < len(all_lines) else all_lines
        
        if not entries:
            await ctx.send("📝 No audit log entries found.")
            return
        
        # Format and send the log entries
        log_content = "".join(entries)
        
        # For long logs, split into multiple messages (Discord has a 2000 char limit)
        if len(log_content) > 1900:
            chunks = []
            current_chunk = "📝 **Command Audit Log**\n```"
            
            for entry in entries:
                if len(current_chunk) + len(entry) > 1900:
                    current_chunk += "```"
                    chunks.append(current_chunk)
                    current_chunk = "```"
                
                current_chunk += entry
            
            if current_chunk:
                current_chunk += "```"
                chunks.append(current_chunk)
            
            for chunk in chunks:
                await ctx.send(chunk)
        else:
            await ctx.send(f"📝 **Command Audit Log**\n```{log_content}```")
        
    except Exception as e:
        logger.error(f"Error reading audit log: {e}")
        await ctx.send(f"❌ Failed to read audit log: {str(e)}")

# Run the bot
if __name__ == "__main__":
    client.run(DISCORD_TOKEN)
