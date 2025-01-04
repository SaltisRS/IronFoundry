import discord
from typing import Optional


#TODO: Placeholder for the actual message formatting
async def format_message(message: discord.Message, author: Optional[str] = None) -> dict:
    if author is None:
        author = f"{message.author.display_name}"
    msg: dict = {"message_type": "ToClanChat", "message": {"sender": f"{author}", "message": message.content}}
    return msg