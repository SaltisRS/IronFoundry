import redis
import redis.asyncio
import asyncio
import os

from dotenv import load_dotenv
from loguru import logger
from redis.asyncio import StrictRedis
from redis.asyncio.client import PubSub


class RedisClient:
    def __init__(self):
        load_dotenv()
        self.host = os.getenv("REDIS_HOST")
        self.port = os.getenv("REDIS_PORT")
        self.password = os.getenv("REDIS_PASSWORD")
        self.client = None
        self.reconnect = False
    
    # Connect to the redis cache, retrying with exponential backoff
    async def connect(self) -> None:
        retries = 0
        while not self.client:
            self.reconnect = True
            try:
                self.client = StrictRedis(host=self.host,
                                                port=self.port,
                                                password=self.password,
                                                decode_responses=True)
                await self.client.ping()
                logger.success("Connected to redis cache")
                self.reconnect = False
                return self.client
            except (redis.ConnectionError, redis.TimeoutError, redis.AuthenticationError) as exc:
                logger.error(exc)
                self.client = None
                retries += 1
                logger.warning(f"Could not connect to redis cache, retrying in {2 ** retries} seconds. {retries}/7") 
                if retries >= 7: # Exponential backoff, 2^7 = 128 seconds
                    logger.error("Could not connect to redis cache, giving up")
                    self.reconnect = False
                    break
                await asyncio.sleep(2 ** retries)
                continue
    
    async def subscribe(self, channel: str) -> PubSub:
        if not self.client and not self.reconnect:
            await self.connect()
        
        logger.info(f"Subscribing to {channel}")
        sub = self.client.pubsub()
        await sub.subscribe(channel)
        return sub
    
    async def publish(self, channel: str, message: any) -> int:
        if not self.client and not self.reconnect:
            await self.connect()
        
        logger.info(f"Publishing message to {channel}")
        await self.client.publish(channel, message)
        
    async def close(self) -> None:
        if self.client:
            self.client.close()
            logger.success("Closed connection to redis cache")
        else:
            logger.warning("No connection to close")