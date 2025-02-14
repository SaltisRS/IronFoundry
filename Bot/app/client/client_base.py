import discord
import os
from discord import app_commands

from dotenv import load_dotenv
from datetime import datetime
from loguru import logger

from client.modules.redis_client import RedisClient
from client.commands.bingo_commands import setup
#from client.commands.system import add_system_user


class DiscordClient(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.all())
        load_dotenv()
        self.tree = app_commands.CommandTree(self)
        self.token = os.getenv("DISCORD_TOKEN")
        self.redis_client = RedisClient()
        self.preset_guild_id = os.getenv("GUILD_ID")
        self.selected_guild = None
        
    async def set_guild(self):
        try:
            self.selected_guild = await self.fetch_guild(self.preset_guild_id)
        except discord.errors.Forbidden:
            logger.error("Bot does not have access to the guild")
            return
        if self.selected_guild is None:
            logger.error("Guild not found")
            return
        logger.info(f"Guild set to {self.selected_guild}")
        
            
    async def load_commands(self):
        await setup(self, self.selected_guild)
        result = await self.tree.sync(guild=self.selected_guild)
        logger.info(f"Commands loaded: {result}")
        
        
    # Setup for Redis and other services/modules
    async def setup_hook(self):
        await self.redis_client.connect()
        await self.set_guild()
        await self.load_commands()
        
    async def on_member_join(self, member: discord.Member):
        logger.info(f"{member} joined the server")
        await member.add_roles(*[discord.Object(id=1279492982902358119),discord.Object(id=1279852765803446403),discord.Object(id=1277240949524664370), discord.Object(id=1333568211987206238)])
        
    
    #! Do NOT handle Bot setup here, use setup_hook instead as it runs before bot start.
    async def on_ready(self):
        logger.info(f"Bot is ready as {self.user} at {datetime.now()}")

