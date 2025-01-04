import asyncio
from loguru import logger
from client.client_base import DiscordClient
from pathlib import Path


@logger.catch
async def main():
    # Initialize the logger
    logger.add(sink=Path(str(Path(__file__).parent) + "/logs/{time:MMMM-YYYY}/{time:DD}.log"), 
               format="{level}:{message} - [{time:HH:mm:s - DD/MM/YYYY}]", 
               level="INFO", 
               rotation="1 day")
    
    app = DiscordClient()
    await app.start(app.token)

if __name__ == "__main__":
    asyncio.run(main())