import asyncio
import os
import sys


from dotenv import load_dotenv
from loguru import logger
from client.client_base import DiscordClient
from pathlib import Path


async def logging_setup():
    load_dotenv()
    logger.remove()
    log_level = "DEBUG" if os.getenv("DEBUG_LOGS", "False").lower() == "true" else "INFO"
    logger.add(sink=sys.stdout, format="{level}:{message} - [{time:HH:mm:s - DD/MM/YYYY}]", level=log_level)
    logger.add(sink=Path(__file__).parent / "logs" / "{time:MMMM-YYYY}" / "{time:DD}.log", 
               format="{level}:{message} - [{time:HH:mm:s - DD/MM/YYYY}]", 
               level=log_level, 
               rotation="1 day")
    
    logger.info("Logging set to: {log_level}")


@logger.catch
async def main():
    await logging_setup()
    app = DiscordClient()
    await app.start(app.token)

if __name__ == "__main__":
    asyncio.run(main())