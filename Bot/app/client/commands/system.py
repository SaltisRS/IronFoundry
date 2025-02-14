from .groups.system import System
import discord
from ..modules.mongo import MongoClient

mongodb = MongoClient()
system = System()

@system.command()
async def add_system_user(interaction: discord.Interaction, user: discord.User = None):
    """
    Sets system user permissions for the bot.
    """
    if not user:
        user = interaction.user
    _user = await mongodb.get_document(collection="Users", query={"_id": str(user.id)})
    if _user:
        _user["individual_permissions"]["sysadmin"] = True
        await mongodb.update_document(collection="Users", query={"_id": str(user.id)}, update=_user)
        await interaction.response.send_message("User permissions updated successfully", ephemeral=True)
    else:
        await interaction.response.send_message("User not found", ephemeral=True)