import discord
from discord import app_commands
from ..mongo_modules.join import add_role, get_roles, delete_role


@app_commands.command(name="db_add")
async def add(interaction: discord.Interaction, role: discord.Role):
    result = await add_role(role)
    if result:
        await interaction.response.send_message(
            "Role added successfully", ephemeral=True
        )
    else:
        await interaction.response.send_message("Error adding role", ephemeral=True)


@app_commands.command(name="db_get")
async def get(interaction: discord.Interaction):
    result: list[discord.Object] = await get_roles()
    if result:
        roles = "\n".join([f"{role['name'], role['id']}" for role in result])
        await interaction.response.send_message(f"Roles:\n{roles}", ephemeral=True)
    else:
        await interaction.response.send_message("No roles found", ephemeral=True)


@app_commands.command(name="db_delete")
async def delete(interaction: discord.Interaction, role: discord.Role):
    result = await delete_role(role)
    if result:
        await interaction.response.send_message(
            "Role deleted successfully", ephemeral=True
        )
    else:
        await interaction.response.send_message("Error deleting role", ephemeral=True)


def load(client: discord.Client):
    print(client.selected_guild)
    client.tree.add_command(add, guild=client.selected_guild)
    client.tree.add_command(get, guild=client.selected_guild)
    client.tree.add_command(delete, guild=client.selected_guild)
