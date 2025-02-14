import asyncio
import os
import sys
import uvicorn

from fastapi import FastAPI
from loguru import logger
from pathlib import Path
from dotenv import load_dotenv

from .routers.chat_http import router as chat_router

def logging_setup():
    load_dotenv()
    logger.remove()
    log_level = "DEBUG" if os.getenv("DEBUG_LOGS", "False").lower() == "true" else "INFO"
    logger.add(sink=sys.stdout, format="{level}:{message} - [{time:HH:mm:s - DD/MM/YYYY}]", level=log_level)
    logger.add(sink=Path(__file__).parent / "logs" / "{time:MMMM-YYYY}" / "{time:DD}.log", 
               format="{level}:{message} - [{time:HH:mm:s - DD/MM/YYYY}]", 
               level=log_level, 
               rotation="1 day")
    
    logger.info("Logging set to: {log_level}")

logging_setup()

app = FastAPI(debug=True)
app.include_router(chat_router)


@app.get("/healthcheck")
async def healthcheck():
    logger.info("Healthcheck triggered")
    return {"status": "ok"}
