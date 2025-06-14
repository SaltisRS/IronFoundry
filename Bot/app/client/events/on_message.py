import discord
import re
from cachetools import TTLCache, cached
from loguru import logger


from ..modules.mongo import MongoClient


client = MongoClient()
cache = TTLCache(maxsize=128, ttl=60)
DISCORD_INVITE_REGEX = re.compile(r"(?:https?://)?(?:discord\.gg|discord\.com/invite)/([\w-]+)", re.IGNORECASE)

@cached(cache)
async def get_whitelisted_links() -> set[str] | None:
    try:
        links = await client.get_many(collection="System", query={"tag": "whitelisted_url"})
        if not links:
            return None
        
        allowed_links = {doc["url"] for doc in links} 
        return allowed_links
    
    except Exception as e:
        logger.debug(f"Error getting links: {e}")

async def check_allowed_links(message: discord.Message) -> set[str] | None:
    offending_links = set()
    allowed_links = await get_whitelisted_links()
    if allowed_links == None:
        return
    message_links = set(re.findall(DISCORD_INVITE_REGEX, message.content))
    for link in message_links:
        if link not in allowed_links:
            offending_links.add(link)
    if offending_links:
        return offending_links
    return


async def handle_message(client: discord.Client, message: discord.Message):
    if message.author.bot:
        return
    link_check = await check_allowed_links(message)
    if link_check:
        await message.author.send(embed=discord.Embed(title="Non whitelisted Discord Link.", description=f"Your message contained a link that is not whitelisted. Please remove the following link(s) and try again.: {link_check}", color=discord.Color.red()))
        await message.delete()
        return