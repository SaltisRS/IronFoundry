import discord
import os
from discord import app_commands

from dotenv import load_dotenv
from datetime import datetime
from loguru import logger

from client.modules.redis_client import RedisClient
from client.mongo_modules.join import add_role

class DiscordClient(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.all())
        load_dotenv()
        self.tree = app_commands.CommandTree()
        self.token = os.getenv("DISCORD_TOKEN")
        self.redis_client = RedisClient()
        
        
    # Setup for Redis and other services/modules
    async def setup_hook(self):
        await self.redis_client.connect()
        
    async def on_member_join(self, member: discord.Member):
        logger.info(f"{member} joined the server")
        await member.add_roles(*[discord.Object(id=1279492982902358119),discord.Object(id=1279852765803446403),discord.Object(id=1277240949524664370), discord.Object(id=1333568211987206238)])

    @app_commands.command("addrole", "add a role to db")
    async def _add_role(self, interaction: discord.Interaction, role: discord.Role):
        await add_role(role)
        await interaction.response.send_message(f"Role {role.name} added to database", ephemeral=True)
        
    
    #! Do NOT handle Bot setup here, use setup_hook instead as it runs before bot start.
    async def on_ready(self):
        await self.tree.sync(guild=discord.Object(id=945052365327839254))
        logger.info(f"Bot is ready as {self.user} at {datetime.now()}")

