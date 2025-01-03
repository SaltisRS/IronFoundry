import discord
import os

from dotenv import load_dotenv
from datetime import datetime
from loguru import logger

from client.modules.redis_client import RedisClient


class DiscordClient(discord.Client):
    def __init__(self, config: dict):
        super().__init__(intents=discord.Intents.all())
        load_dotenv()
        self.config = config
        self.token = os.getenv("DISCORD_TOKEN")
        
        
    # Setup for Redis and other services/modules
    async def setup_hook(self):
        self.redis_client = RedisClient()
        await self.redis_client.connect()

    
    # Do NOT handle Bot setup here, use setup_hook instead as it runs before bot start.
    async def on_ready(self):
        logger.info(f"Bot is ready as {self.user} at {datetime.now()}")