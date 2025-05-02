import os

class BotContext:
    def __init__(self):
        self.tailnet = os.getenv("TAILNET_NAME")  # Name of the Tailscale tailnet
        self.devices_cache = {}  # Cache to track device IDs and their details
        self.last_devices = set()  # Set of device IDs from previous monitoring run
        self.notification_channel_id = os.getenv("NOTIFICATION_CHANNEL_ID")  # Discord channel ID for notifications