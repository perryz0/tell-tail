import os

class BotContext:
    def __init__(self):
        self.tailnet = os.getenv("TAILNET_NAME")  # Name of the Tailscale tailnet