import asyncio
import json
from loguru import logger
from client.client_base import DiscordClient

# Read in the config to pass to the bot
def read_config():
    with open("config.json", "r") as f:
        return json.load(f)

@logger.catch
async def main():
    # Initialize the logger
    logger.add(sink="logs/{time:MMMM-YYYY}/{time:DD:HH}.log", 
               format="{level}:{time} - {message}", 
               level="INFO", 
               rotation="1 day")
    
    # Start the bot
    app = DiscordClient(config=read_config())
    await app.start(app.token)

if __name__ == "__main__":
    asyncio.run(main())