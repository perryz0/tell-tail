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
from services.tasks.expiry_checker import ExpiryChecker


# Load .env variables
load_dotenv()
DISCORD_TOKEN: Final[str] = os.getenv('DISCORD_BOT_TOKEN')
TAILNET_NAME = os.getenv("TAILNET_NAME")

# API and BOT setup
TAILSCALE_TOKEN: Final[str] = os.getenv('TAILSCALE_API_TOKEN')
ts = TailscaleAPI(api_token=TAILSCALE_TOKEN)
intents = discord.Intents.all()
intents.message_content = True

# Define command categories for help command organization
class TelltailHelpCommand(commands.HelpCommand):
    """Custom help command with categorized commands"""
    
    def __init__(self):
        super().__init__()
        # Define command categories and their descriptions
        self.command_categories = {
            "ACL Management": "Commands for managing Tailscale ACLs and users",
            "Monitoring": "Commands for monitoring devices on your Tailnet",
            "Utilities": "Utility commands for bot settings and diagnostics",
            "Admin": "Administrative commands (restricted access)"
        }
        # Assign each command to a category
        self.command_attrs = {
            # ACL Management
            "adduser": "ACL Management",
            "addroleuser": "ACL Management",
            "removeuser": "ACL Management",
            "updateuser": "ACL Management",
            "listusers": "ACL Management",
            "listroles": "ACL Management",
            "listpresets": "ACL Management",
            "acldetails": "ACL Management",
            
            # Monitoring
            "list_devices": "Monitoring",
            "device_status": "Monitoring",
            "monitor_status": "Monitoring",
            "set_notification_channel": "Monitoring",
            
            # Utilities
            "ping": "Utilities",
            
            # Admin
            "audit_log": "Admin",
            "auditlog": "Admin"
        }
    
    async def send_bot_help(self, mapping):
        """Send help for all commands, organized by category"""
        ctx = self.context
        
        # Create embed
        embed = discord.Embed(
            title="TellTail Command Help",
            description=f"Bot prefix: `{ctx.bot.command_prefix}`",
            color=discord.Color.blue()
        )
        
        # Get all commands
        all_commands = list(ctx.bot.commands)
        
        # Create a dictionary to store commands by category
        categorized_commands = {}
        for category in self.command_categories:
            categorized_commands[category] = []
        
        # Categorize each command
        for command in all_commands:
            category = self.command_attrs.get(command.name, "Utilities")
            categorized_commands[category].append(command)
        
        # Add each category as a field in the embed
        for category, commands_list in categorized_commands.items():
            if commands_list:
                # Sort commands alphabetically within each category
                commands_list.sort(key=lambda x: x.name)
                
                # Format command list
                value = "\n".join([
                    f"`{ctx.bot.command_prefix}{cmd.name}` - {cmd.help}" 
                    for cmd in commands_list
                ])
                
                embed.add_field(
                    name=f"{category} ({len(commands_list)})",
                    value=value,
                    inline=False
                )
        
        # Add footer with details about detailed help
        embed.set_footer(text=f"Type {ctx.bot.command_prefix}help <command> for detailed information on a command.")
        
        await ctx.send(embed=embed)
    
    async def send_command_help(self, command):
        """Send detailed help for a specific command"""
        ctx = self.context
        
        # Create embed
        embed = discord.Embed(
            title=f"Command: {ctx.bot.command_prefix}{command.name}",
            description=command.help,
            color=discord.Color.blue()
        )
        
        # Add usage information
        usage = f"{ctx.bot.command_prefix}{command.name}"
        if command.signature:
            usage += f" {command.signature}"
        embed.add_field(name="Usage", value=f"`{usage}`", inline=False)
        
        # Add category
        category = self.command_attrs.get(command.name, "Utilities")
        embed.add_field(name="Category", value=category, inline=True)
        
        # Add any aliases if they exist
        if command.aliases:
            aliases = ", ".join([f"{ctx.bot.command_prefix}{alias}" for alias in command.aliases])
            embed.add_field(name="Aliases", value=aliases, inline=True)
        
        await ctx.send(embed=embed)

# Create the bot with custom help command
client = commands.Bot(
    command_prefix="!", 
    intents=intents, 
    help_command=TelltailHelpCommand()
)
context: BotContext = BotContext()
expiry_checker = ExpiryChecker(client)


# Basic event handlers
@client.event
async def on_ready():
    """Called when the bot has successfully connected to Discord"""
    logger.info(f"Logged in as {client.user}")
    logger.info("Connected guilds:")
    for guild in client.guilds:
        logger.info(f"- {guild.name} (ID: {guild.id})")
    # Start background tasks
    monitor_tailnet_changes.start()
    # Start ACL expiry checker
    asyncio.create_task(expiry_checker.start_periodic_check())
    logger.info("Started periodic ACL expiry checker")


@client.command(name="ping", help="Check if the bot is running")
async def ping(ctx):
    """Simple command to check if the bot is up and responding to commands"""
    await ctx.send("Pong! The bot is running.")


# === MONITORING COMMANDS ===

@client.command(name="list_devices", help="List all devices on the Tailscale network")
async def list_devices(ctx):
    """
    List all devices currently connected to your Tailscale network.
    Displays the hostname and IP address of each device.
    """
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


@client.command(name="device_status", help="Check if a specific device is currently online")
async def device_status(ctx, device_name: str):
    """
    Check the connection status of a specific device on your Tailnet.
    
    Parameters:
    - device_name: The name of the device to check
    """
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


@device_status.error
async def device_status_error(ctx, error):
    """Error handler for the device_status command"""
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Error: Missing device name. Usage: `!device_status <device_name>`")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("❌ Error: Invalid argument. Usage: `!device_status <device_name>`")
    else:
        logger.error(f"Error in device_status command: {error}")
        await ctx.send("❌ An unexpected error occurred.")


@client.command(name="monitor_status", help="Show monitoring status and tracked devices")
async def monitor_status(ctx):
    """
    Display the current monitoring status of the Tailnet.
    Shows monitored devices and notification settings.
    """
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
        online_devices = sum(1 for device in context.devices_cache.values() if device.get('online', False))
        
        # Create and send an embed with status information
        embed = discord.Embed(
            title="📊 Tailnet Monitoring Status",
            description=f"Monitoring status for `{context.tailnet}`",
            color=discord.Color.blue()
        )
        
        # Add basic information fields
        embed.add_field(name="Tailnet", value=context.tailnet, inline=True)
        embed.add_field(name=notification_info, value="\u200b", inline=True)  # Invisible character for spacing
        embed.add_field(name="Update Frequency", value="Every minute", inline=True)
        
        # Add device statistics
        embed.add_field(name="Device Statistics", value=
            f"Total Devices: {device_count}\n"
            f"Online Devices: {online_devices}\n"
            f"Offline Devices: {device_count - online_devices}", 
            inline=False
        )
        
        # Add monitoring features
        features = [
            "✅ Device joins/leaves",
            "✅ Online/offline status changes",
            "✅ Detailed device information"
        ]
        embed.add_field(name="Monitoring Features", value="\n".join(features), inline=False)
        
        # Add the most recent device changes
        recently_changed = []
        for device in sorted(context.devices_cache.values(), 
                            key=lambda d: d.get('lastSeen', ''), reverse=True)[:5]:
            hostname = device.get('hostname', 'Unknown')
            status = "🟢 Online" if device.get('online', False) else "🔴 Offline"
            last_seen = device.get('lastSeen', 'Unknown')
            
            recently_changed.append(f"{hostname}: {status} (Last seen: {last_seen})")
        
        if recently_changed:
            embed.add_field(name="Recent Device Activity", value="\n".join(recently_changed), inline=False)
        
        await ctx.send(embed=embed)
    except Exception as e:
        logger.error(f"Error showing monitor status: {e}")
        await ctx.send("❌ Failed to show monitoring status.")


@client.command(name="set_notification_channel", help="Set the current channel for device notifications")
async def set_notification_channel(ctx):
    """
    Configure the bot to send device connection/disconnection notifications to the current channel.
    Must be run in the channel where you want to receive notifications.
    """
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


# Background Task: Monitor Tailnet Changes
@tasks.loop(minutes=1)
async def monitor_tailnet_changes():
    """
    Periodically check for changes in the Tailscale network and detect device joins/leaves.
    Tracks devices between runs to detect and report changes.
    """
    try:
        # Get current devices from Tailscale API
        devices_response = ts.list_devices(context.tailnet)
        if not devices_response or "devices" not in devices_response:
            logger.warning("No devices found in tailnet or API response error")
            return
            
        current_devices = devices_response["devices"]
        current_device_map = {device['id']: device for device in current_devices}
        current_device_ids = set(current_device_map.keys())
        
        # Initialize on first run
        if not context.devices_cache:
            logger.info(f"Initializing device cache with {len(current_devices)} devices")
            context.devices_cache = current_device_map
            context.last_devices = current_device_ids
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
        
        # Find added devices (not in last run but in current run)
        added_devices = current_device_ids - context.last_devices
        if added_devices:
            logger.info(f"Detected {len(added_devices)} new device(s) since last check")
            
            for device_id in added_devices:
                device = current_device_map[device_id]
                hostname = device.get('hostname', 'Unknown')
                addresses = device.get('addresses', ['No IP'])
                user = device.get('user', 'Unknown')
                created = device.get('created', 'Unknown time')
                
                # Create detailed message
                message = (
                    f"🟢 **Device joined tailnet**: {hostname}\n"
                    f"📍 IP: {addresses[0]}\n"
                    f"👤 User: {user}\n"
                    f"🕒 Created: {created}"
                )
                logger.info(f"New device: {hostname} ({addresses[0]})")
                
                # Send notification to Discord if channel exists
                if notification_channel:
                    try:
                        await notification_channel.send(message)
                    except Exception as e:
                        logger.error(f"Failed to send join notification to Discord: {e}")
        
        # Find removed devices (in last run but not in current run)
        removed_devices = context.last_devices - current_device_ids
        if removed_devices:
            logger.info(f"Detected {len(removed_devices)} device(s) removed since last check")
            
            for device_id in removed_devices:
                # Get the device info from the previous cache
                if device_id in context.devices_cache:
                    device = context.devices_cache[device_id]
                    hostname = device.get('hostname', 'Unknown')
                    addresses = device.get('addresses', ['No IP'])
                    user = device.get('user', 'Unknown')
                    last_seen = device.get('lastSeen', 'Unknown time')
                    
                    # Create detailed message
                    message = (
                        f"🔴 **Device left tailnet**: {hostname}\n"
                        f"📍 IP: {addresses[0]}\n"
                        f"👤 User: {user}\n"
                        f"🕒 Last seen: {last_seen}"
                    )
                    logger.info(f"Removed device: {hostname} ({addresses[0]})")
                    
                    # Send notification to Discord if channel exists
                    if notification_channel:
                        try:
                            await notification_channel.send(message)
                        except Exception as e:
                            logger.error(f"Failed to send leave notification to Discord: {e}")
        
        # Check for status changes in existing devices
        for device_id in current_device_ids.intersection(context.last_devices):
            # If the device was in both runs, check if its online status changed
            if device_id in context.devices_cache:
                old_device = context.devices_cache[device_id]
                new_device = current_device_map[device_id]
                
                old_online = old_device.get('online', False)
                new_online = new_device.get('online', False)
                
                if old_online != new_online:
                    hostname = new_device.get('hostname', 'Unknown')
                    addresses = new_device.get('addresses', ['No IP'])
                    
                    if new_online:
                        # Device came online
                        status_message = (
                            f"🟢 **Device came online**: {hostname}\n"
                            f"📍 IP: {addresses[0]}"
                        )
                        logger.info(f"Device came online: {hostname} ({addresses[0]})")
                    else:
                        # Device went offline
                        status_message = (
                            f"🔴 **Device went offline**: {hostname}\n"
                            f"📍 IP: {addresses[0]}"
                        )
                        logger.info(f"Device went offline: {hostname} ({addresses[0]})")
                    
                    # Send notification to Discord if channel exists and if configured to notify about status changes
                    if notification_channel:
                        try:
                            await notification_channel.send(status_message)
                        except Exception as e:
                            logger.error(f"Failed to send status change notification to Discord: {e}")
        
        # Update the device cache and last_devices for the next run
        context.devices_cache = current_device_map
        context.last_devices = current_device_ids
        
    except Exception as e:
        logger.error(f"Error monitoring Tailnet: {e}")


# === ACL MANAGEMENT COMMANDS ===

@client.command(name="adduser", help="Add a user to the ACL")
async def adduser(ctx, username: str, ports: str = "22/tcp", ttl_hours: int = None):
    """
    Add a user to the ACL with optional time-limited access.
    
    Parameters:
    - username: The username to add to the ACL
    - ports: Comma-separated list of ports to allow (default: 22/tcp)
    - ttl_hours: Optional time-to-live in hours for temporary access
    """
    await acl_commands.add_user(ctx, username, ports, ttl_hours)


@adduser.error
async def adduser_error(ctx, error):
    """Handle errors in the adduser command"""
    if isinstance(error, commands.MissingRequiredArgument):
        if error.param.name == 'username':
            await ctx.send("❌ Error: Missing username parameter.\n"
                         "Usage: `!adduser <username> [ports] [ttl_hours]`\n"
                         "Example: `!adduser alice 22/tcp,80/tcp 24`")
    else:
        await ctx.send(f"❌ Error: {str(error)}")


@client.command(name="removeuser", help="Remove a user from the ACL")
async def removeuser(ctx, username: str):
    """
    Remove a user from the Tailscale ACL.
    
    Parameters:
    - username: The Tailscale username to remove
    
    Example: !removeuser devicename
    """
    await acl_commands.remove_user(ctx, username)


@removeuser.error
async def removeuser_error(ctx, error):
    """Error handler for the removeuser command"""
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Error: Missing username. Usage: `!removeuser <username>`")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("❌ Error: Invalid argument. Usage: `!removeuser <username>`")
    else:
        logger.error(f"Error in removeuser command: {error}")
        await ctx.send("❌ An unexpected error occurred.")


@client.command(name="listusers", help=f"List all current users in `{TAILNET_NAME}`")
async def listusers(ctx):
    """
    List all users currently registered in your Tailnet.
    Shows all devices regardless of their ACL status.
    """
    await acl_commands.list_tailnet_users(ctx)


@client.command(name="listroles", help="List all user roles with access permissions")
async def listroles(ctx):
    """List all user roles defined in the ACL."""
    await acl_commands.list_acl_roles(ctx)


@client.command(name="acldetails", help="Show detailed ACL information including expiration times")
async def acldetails(ctx):
    """
    Show detailed information about ACL entries including expiration times for temporary access.
    Lists all current access control entries with their ports and expiration times if applicable.
    """
    await acl_commands.list_acl_details(ctx)


@client.command(name="updateuser", help="Update user ACL ports")
async def updateuser(ctx, username: str, ports: str):
    """
    Update the port access permissions for an existing user in the ACL.
    
    Parameters:
    - username: The Tailscale username to update
    - ports: New comma-separated list of ports to allow
    
    Example: !updateuser devicename 22/tcp,443/tcp,8080/tcp
    """
    await acl_commands.update_user(ctx, username, ports)


@updateuser.error
async def updateuser_error(ctx, error):
    """Error handler for the updateuser command"""
    if isinstance(error, commands.MissingRequiredArgument):
        if 'username' in str(error):
            await ctx.send("❌ Error: Missing username. Usage: `!updateuser <username> <ports>`")
        else:
            await ctx.send("❌ Error: Missing ports. Usage: `!updateuser <username> <ports>`")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("❌ Error: Invalid argument. Usage: `!updateuser <username> <ports>`")
    else:
        logger.error(f"Error in updateuser command: {error}")
        await ctx.send("❌ An unexpected error occurred.")


@client.command(name="addroleuser", help="Add a user to the ACL with a predefined role")
async def addroleuser(ctx, username: str, role: str, ttl_hours: int = None):
    """
    Add a user to the ACL with a predefined role preset.
    
    Parameters:
    - username: The Tailscale username to add
    - role: The role preset name (dev, frontend, infra, etc.)
    - ttl_hours: Optional time-to-live in hours for temporary access
    
    Example: !addroleuser devicename dev 24
    """
    await acl_commands.add_role_user(ctx, username, role, ttl_hours)


@addroleuser.error
async def addroleuser_error(ctx, error):
    """Handle errors in the addroleuser command"""
    if isinstance(error, commands.MissingRequiredArgument):
        if error.param.name == 'username':
            await ctx.send("❌ Error: Missing username parameter.\n"
                         "Usage: `!addroleuser <username> <role> [ttl_hours]`\n"
                         "Example: `!addroleuser alice dev 24`")
        elif error.param.name == 'role':
            await ctx.send("❌ Error: Missing role parameter.\n"
                         "Usage: `!addroleuser <username> <role> [ttl_hours]`\n"
                         "Example: `!addroleuser alice dev 24`")
    else:
        await ctx.send(f"❌ Error: {str(error)}")


@client.command(name="listpresets", help="List all available role presets")
async def listpresets(ctx):
    """
    List all available role presets and their port configurations.
    Shows the predefined roles that can be used with the addroleuser command.
    """
    await acl_commands.list_role_presets(ctx)


# === ADMIN COMMANDS ===

@client.command(name="audit_log", help="View recent command audit logs")
async def audit_log(ctx, lines: int = 10):
    """
    View the recent command audit log entries.
    
    Parameters:
    - lines: Number of recent log entries to show (default: 10, max: 50)
    """
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


@audit_log.error
async def audit_log_error(ctx, error):
    """Error handler for the audit_log command"""
    if isinstance(error, commands.BadArgument):
        await ctx.send("❌ Error: Lines parameter must be a number. Usage: `!audit_log [lines]`")
    else:
        logger.error(f"Error in audit_log command: {error}")
        await ctx.send("❌ An unexpected error occurred.")


@client.command(name="auditlog", help="Admin only: View the command audit log")
async def auditlog(ctx, lines: int = 10):
    """
    Admin-only command to view the command audit log.
    Only users with IDs in AUDIT_ADMINS environment variable can use this.
    
    Parameters:
    - lines: Number of recent log entries to show (default: 10, max: 50)
    """
    try:
        # Check if the user is authorized to access the audit log
        admin_ids = os.getenv("AUDIT_ADMINS", "").split(",")
        admin_ids = [admin_id.strip() for admin_id in admin_ids if admin_id.strip()]
        
        if not admin_ids:
            logger.warning("AUDIT_ADMINS environment variable is not set or is empty")
            await ctx.send("❌ This command is disabled because no admin users are configured.")
            return
        
        # Convert user ID to string for comparison
        user_id_str = str(ctx.author.id)
        
        if user_id_str not in admin_ids:
            logger.warning(f"Unauthorized access attempt to auditlog by {ctx.author.name} (ID: {user_id_str})")
            await ctx.send("❌ You do not have permission to use this command.")
            return
        
        # Check if the log file exists
        from services.logging.audit import AUDIT_LOG_FILE
        
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
            current_chunk = "🔒 **ADMIN: Command Audit Log**\n```"
            
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
            await ctx.send(f"🔒 **ADMIN: Command Audit Log**\n```{log_content}```")
        
        # Log this access to the audit log itself
        from services.logging.audit import log_command_audit
        log_command_audit(ctx.author.name, "auditlog", str(lines))
        
    except Exception as e:
        logger.error(f"Error reading audit log: {e}")
        await ctx.send(f"❌ Failed to read audit log: {str(e)}")


@auditlog.error
async def auditlog_error(ctx, error):
    """Error handler for the auditlog command"""
    if isinstance(error, commands.BadArgument):
        await ctx.send("❌ Error: Lines parameter must be a number. Usage: `!auditlog [lines]`")
    else:
        logger.error(f"Error in auditlog command: {error}")
        await ctx.send("❌ An unexpected error occurred.")


# === GLOBAL ERROR HANDLING ===

@client.event
async def on_command_error(ctx, error):
    """Global error handler for all commands"""
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❓ Unknown command. Use `!help` to see available commands.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Missing required argument: {error.param.name}. Use `!help {ctx.command}` for proper usage.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send(f"❌ Invalid argument provided. Use `!help {ctx.command}` for proper usage.")
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏱️ Command on cooldown. Try again in {error.retry_after:.2f} seconds.")
    else:
        # For errors not caught by specific error handlers
        logger.error(f"Error occurred: {error}")
        await ctx.send("❌ An unexpected error occurred. Please check the logs.")


# Run the bot
if __name__ == "__main__":
    client.run(DISCORD_TOKEN)
