import discord
import os

from dotenv import load_dotenv

from discord import app_commands
from .groups.system import System
from ..modules.mongo import MongoClient
load_dotenv()
mongodb = MongoClient()
system = System()

owner = os.getenv("OWNER_ID")

async def check_sysadmin(user: discord.User) -> bool:
    _user = await mongodb.get_document(collection="Users", query={"_id": str(user.id)})
    if _user:
        return _user["individual_permissions"]["sysadmin"]
    return False

@system.command()
async def add_system_user(interaction: discord.Interaction, user: discord.User = None):
    """
    Sets system user permissions for the bot.
    
    Pass in a user, or the command author will be used.
    """
    if interaction.user.id != int(owner):
        await interaction.response.send_message("You do not have permission to run this command", ephemeral=True)
        return
    if not user:
        user = interaction.user
    _user = await mongodb.get_document(collection="Users", query={"_id": str(user.id)})
    if _user:
        _user["individual_permissions"]["sysadmin"] = True
        await mongodb.update_document(collection="Users", query={"_id": str(user.id)}, update=_user)
        await interaction.response.send_message("User permissions updated successfully", ephemeral=True)
    else:
        await interaction.response.send_message("User not found in database, link first.", ephemeral=True)
        
@system.command()
@app_commands.check(check_sysadmin)
async def whitelist_link(interaction: discord.Interaction, link: str):
    if await check_sysadmin(interaction.user) == True:
        await mongodb.insert_document(collection="System", document={"tag": "whitelisted_url", "url": link})
        await interaction.response.send_message(f"{link} whitelisted.", ephemeral=True)
    else:
        await interaction.response.send_message("You do not have permission to run this command", ephemeral=True)


async def setup(client: discord.Client, guild: discord.Guild):
    client.tree.add_command(system, guild=guild)