import os
import discord
from loguru import logger
from .groups.tags import Tags

group = Tags()

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

_instructions = """
1. Click the Grouping tab on the bottom of your screen and click the Green Faces Icon to go into the Clan Interface
2. Click "Find" and search "Iron Foundry" 
3. Click "Chat". It should now say "Iron Foundry" at the top and you should be able to see other clan members online.
4. Hop to World [world number]
5. In that same tab, click "Settings" and then click "Apply" and wait for one of the moderators to accept your application.
"""

@group.command()
async def instructions(interaction: discord.Interaction):
    await interaction.response.defer()
    embed = discord.Embed(title="How to Join the In Game CC")
    embed.description = _instructions
    await interaction.followup.send(embed=embed)

@group.command()
async def requirements(interaction: discord.Interaction):
    await interaction.response.defer()
    file_path = os.path.join(ASSETS_DIR, "rank_reqs.png")
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        await interaction.followup.send("Image not found. Please contact a moderator.", ephemeral=True)
        return
    with open(file_path, "rb") as f:
        file = discord.File(f)
    await interaction.followup.send(file=file)

@group.command()
async def mentee(interaction: discord.Interaction):
    await interaction.response.defer()
    file_path = os.path.join(ASSETS_DIR, "mentee.png")
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        await interaction.followup.send("Image not found. Please contact a moderator.", ephemeral=True)
        return
    with open(file_path, "rb") as f:
        file = discord.File(f)
    await interaction.followup.send(file=file)

@group.command()
async def upgrades(interaction: discord.Interaction):
    await interaction.response.defer()
    file_path = os.path.join(ASSETS_DIR, "direct_upgrades.png")
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        await interaction.followup.send("Image not found. Please contact a moderator.", ephemeral=True)
        return
    with open(file_path, "rb") as f:
        file = discord.File(f)
    await interaction.followup.send(file=file)

async def setup(client: discord.Client, guild):
    client.tree.add_command(group, guild=guild)
