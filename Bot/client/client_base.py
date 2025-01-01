import discord

import redis
from redis.asyncio import StrictRedis
from datetime import datetime
from loguru import logger
import redis.asyncio
import redis.asyncio.client


class DiscordClient(discord.Client):
    def __init__(self, config: dict):
        """

        Args:
            config (dict):
            
            Pass a dictionary with the following keys:
            
            {
                "token": "your discord token",
                "redis": {
                    "host": "hostadress",
                    "port": hostport,
                    "password": "hostpw,
                    "channels": {
                        "chat_recv": "chat-recv",
                        "chat_send": "chat-send",
                        "collection_log": "collection-log"
                    }
                },
                
            }
        """
        super().__init__(config, intents=discord.Intents.all())
        self.token = config["token"]
        self.redis_config = config["redis"]
        self.sendhook_ingame = config["sendhook_ingame"]
        
        
    # Setup for Redis and other services/modules
    async def setup_hook(self):
        self.redis_client = StrictRedis(host=self.redis_config["host"],
                                              port=self.redis_config["port"],
                                              password=self.redis_config["password"],
                                              decode_responses=True)
    
    # Subscribe to a redis channel, returns the subscription object for further use
    async def redis_subscribe(self, channel: str) -> redis.asyncio.client.PubSub:
        logger.info(f"Subscribing to {channel}")
        sub = self.redis_client.pubsub()
        await sub.subscribe(channel)
        return sub
    
    # Publish a message to a redis channel
    async def redis_publish(self, channel: str, message: any) -> None:
        logger.info(f"Publishing message to {channel}")
        await self.redis_client.publish(channel, message)
    
    # Close the redis connection
    async def redis_close(self) -> None:
        await self.redis_client.close()
    
    # Do NOT handle Bot setup here, setup_hook instead as it runs before bot start.
    async def on_ready(self):
        logger.info(f"Bot is ready as {self.user} at {datetime.now()}")