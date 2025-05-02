"""
Task to periodically check for and remove expired ACL entries.
"""
import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv
from services.tasks.acl_manager import ACLManager
from services.logging import logger

load_dotenv()

# How often to check for expired entries (in seconds)
# Default: every minute
CHECK_INTERVAL = int(os.getenv("ACL_EXPIRY_CHECK_INTERVAL", 60))

class ExpiryChecker:
    def __init__(self, bot=None):
        """Initialize the expiry checker with optional bot for notifications."""
        self.acl_manager = ACLManager()
        self.bot = bot
        self.notification_channel_id = os.getenv("NOTIFICATION_CHANNEL_ID")
        logger.info(f"Expiry checker initialized with check interval of {CHECK_INTERVAL} seconds")
        
    async def notify_expired_users(self, expired_users):
        """Send a notification to the configured channel about expired users."""
        if not self.bot or not self.notification_channel_id or not expired_users:
            return
            
        try:
            channel = await self.bot.fetch_channel(int(self.notification_channel_id))
            if channel:
                timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
                users_list = ", ".join(expired_users)
                await channel.send(f"⏰ **Automatic Cleanup**: Removed {len(expired_users)} expired ACL entries at {timestamp}\n"
                                  f"Users: {users_list}")
        except Exception as e:
            logger.error(f"Failed to send expiry notification: {e}")
    
    async def check_expired_entries(self):
        """Check for and remove expired ACL entries."""
        try:
            logger.info("Running scheduled check for expired ACL entries")
            expired_users = self.acl_manager.check_and_remove_expired_entries()
            
            if expired_users:
                logger.info(f"Removed {len(expired_users)} expired ACL entries: {', '.join(expired_users)}")
                await self.notify_expired_users(expired_users)
            else:
                logger.info("No expired ACL entries found")
                
        except Exception as e:
            logger.error(f"Error checking for expired ACL entries: {e}")
    
    async def start_periodic_check(self):
        """Start periodic checking for expired entries."""
        logger.info(f"Starting periodic ACL expiry checks every {CHECK_INTERVAL} seconds")
        while True:
            await self.check_expired_entries()
            await asyncio.sleep(CHECK_INTERVAL) 