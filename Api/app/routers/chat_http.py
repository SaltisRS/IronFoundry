import os
import asyncio


from loguru import logger
from fastapi import APIRouter, Request, status
from fastapi.datastructures import Headers
from dotenv import load_dotenv

from ..modules.redis_client import RedisClient


load_dotenv()

#? Generic Collection Router
router = APIRouter()
previous_messages = set()
redis = RedisClient()

async def verify_headers(headers: Headers):
    if headers.get("Verification-Code").lower() == str(os.getenv("CHAT_HEADER_SECRET")).lower():
        return True
    return False

async def process_message(data: dict):
    messages = set()
    for message in data:
        processed = {"sender": str(message["sender"]).replace("\u00a0", " "),
                     "message": str(message["message"]).replace("\u00a0", " "),
                     "clan_name": message["clan_name"],
                     "clan_rank": message["clan_rank"],
                     "clan_rank_icon": message["rank"],
                     "world_type": message["is_league_world"]
                     }
        messages.add(processed)
    return messages

@router.post("/send", status_code=status.HTTP_200_OK)
async def clog_user(request: Request):
    verified = await verify_headers(request.headers)
    
    #? If the verification code is invalid, dont process the request
    if not verified:
        logger.info("Invalid Verification Code Provided")
        return status.HTTP_401_UNAUTHORIZED
    
    data = await request.json()
    if data not in previous_messages:
        previous_messages.add(data)
    else:
        return status.HTTP_208_ALREADY_REPORTED
    
    messages = await process_message(data)
    logger.info(f"{len(messages)} messages received")
    
    try:
        #handle in new thread
        task = asyncio.create_task(subscribe_temp)
        await asyncio.tasks.gather(task)
        await redis.publish("chat-send", messages)
    except Exception as e:
        logger.error(e)
        return status.HTTP_500_INTERNAL_SERVER_ERROR
    
    return status.HTTP_200_OK


async def subscribe_temp():
    logger.info("Subscribing to chat-send")
    pubsub = await redis.subscribe("chat-send")
    async for message in pubsub.listen():
        logger.info(message)
    
    await redis.unsubscribe("chat-send")
        
    