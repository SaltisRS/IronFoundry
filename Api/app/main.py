import asyncio

from loguru import logger
from pathlib import Path

async def main():
    logger.add(sink=Path(str(Path(__file__).parent) + "/logs/{time:MMMM-YYYY}/{time:DD}.log"), 
               format="{level}:{message} - [{time:HH:mm:s - DD/MM/YYYY}]", 
               level="INFO", 
               rotation="1 day")
    


if __name__ == "__main__":
    asyncio.run(main())