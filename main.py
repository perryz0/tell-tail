from typing import Final

import discord
from discord.ext import commands, tasks
import logging
from dotenv import load_dotenv
import os
from api.TailscaleAPI import TailscaleAPI
import asyncio

# Load .env variables
load_dotenv()
DISCORD_TOKEN: Final[str] = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = int(os.getenv("DISCORD_GUILD_ID", 0))  # Optional for specific guild targeting

# Logging configuration
logging.basicConfig(level=logging.INFO)

# API and BOT setup
TAILSCALE_API_TOKEN: Final[str] = os.getenv("TAILSCALE_API_TOKEN")
ts = TailscaleAPI(api_token=TAILSCALE_API_TOKEN)
intents = discord.Intents.default()
intents.messages = True  # Enable message handling
intents.guilds = True    # Enable guild events

bot = commands.Bot(command_prefix="!", intents=intents)

# Bot Context (placeholder)
class BotContext:
    def __init__(self):
        self.tailnet = os.getenv("TAILNET_NAME")  # Name of the Tailscale tailnet

context = BotContext()

# Event: On Ready
@bot.event
async def on_ready():
    logging.info(f"Logged in as {bot.user}")
    logging.info("Connected guilds:")
    for guild in bot.guilds:
        logging.info(f"- {guild.name} (ID: {guild.id})")
    # Start background tasks
    monitor_tailnet_changes.start()

# Command: Ping
@bot.command(name="ping", help="Check if the bot is running")
async def ping(ctx):
    await ctx.send("Pong! The bot is running.")

# Command: List Devices
@bot.command(name="list_devices", help="List all devices on the Tailscale network")
async def list_devices(ctx):
    try:
        devices = ts.list_devices(context.tailnet)
        if not devices:
            await ctx.send("No devices found on the Tailscale network.")
            return
        
        device_list = "\n".join([f"- {device['hostname']} ({device['ip']})" for device in devices])
        await ctx.send(f"Devices on Tailscale:\n{device_list}")
    except Exception as e:
        logging.error(f"Error listing devices: {e}")
        await ctx.send("Failed to retrieve device list.")

# Background Task: Monitor Tailnet Changes
@tasks.loop(minutes=1)
async def monitor_tailnet_changes():
    """
    Periodically check for changes in the Tailscale network and send alerts to a Discord channel.
    """
    try:
        devices = ts.list_devices(context.tailnet)
        # Logic for detecting changes (e.g., new devices, disconnected devices)
        # Example:
        logging.info("Monitoring Tailnet for changes...")
    except Exception as e:
        logging.error(f"Error monitoring Tailnet: {e}")

# Error Handling: Command Errors
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Unknown command. Use `!help` to see available commands.")
    else:
        logging.error(f"Error occurred: {error}")
        await ctx.send("An unexpected error occurred. Please check the logs.")

# Run the bot
if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
