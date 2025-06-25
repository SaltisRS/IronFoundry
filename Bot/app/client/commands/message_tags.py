import discord

from loguru import logger

from .groups.tags import Tags



group = Tags()

_instructions = """
1. Click the Grouping tab on the bottom of your screen and click the Green Faces Icon to go into the Clan Interface
2. Click "Find" and search "Iron Foundry" 
3. Click "Chat". It should now say "Iron Foundry" at the top and you should be able to see other clan members online.
4. Hop to World [world number]
5. In that same tab, click "Settings" and then click "Apply" and wait for one of the moderators to accept your application."""


@group.command()
async def instructions(interaction: discord.Interaction):
    embed = discord.Embed(title="How to Join the In Game CC")
    embed.description = _instructions
    await interaction.response.send_message(embed=embed)
    

@group.command()
async def requirements(interaction: discord.Interaction):
    with open("assets/rank_reqs.png", "rb") as f:
        file = discord.File(f)
    await interaction.response.send_message(file=file)
     
        
@group.command()
async def mentee(interaction: discord.Interaction):
    with open("assets/mentee.png", "rb") as f:
        file = discord.File(f)
    await interaction.response.send_message(file=file)
    
    
@group.command()
async def upgrades(interaction: discord.Interaction):
    with open("assets/direct_upgrades.png", "rb") as f:
        file = discord.File(f)
    await interaction.response.send_message(file=file)
    
async def setup(client: discord.Client, guild):
    client.tree.add_command(group, guild=guild)