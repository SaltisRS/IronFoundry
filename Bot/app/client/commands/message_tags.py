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
    await interaction.followup.send("https://copyparty.ironfoundry.cc/public/rank-requirements/latest/rank-reqs.png")


@group.command()
async def mentee(interaction: discord.Interaction):
    await interaction.response.defer()
    await interaction.followup.send("https://copyparty.ironfoundry.cc/public/rank-requirements/latest/mentee.png")


@group.command()
async def upgrades(interaction: discord.Interaction):
    await interaction.response.defer()
    await interaction.followup.send("https://copyparty.ironfoundry.cc/public/rank-requirements/latest/directupgrades.png")


async def setup(client: discord.Client, guild):
    client.tree.add_command(group, guild=guild)
