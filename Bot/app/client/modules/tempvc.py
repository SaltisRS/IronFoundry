import discord
from discord import app_commands


vc_cat = discord.Object(id=945052365873090651)

active_channels = set()

async def is_empty(channel: discord.VoiceChannel):
    if len(channel.members) <= 0:
        return True
    return False

class PromptModal(discord.ui.Modal, title="VC Settings"):
    name = discord.ui.TextInput()


class PromptView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    
    
    @discord.ui.button()
    async def use_default(self, interaction: discord.Interaction, button: discord.ui.Button):
        ...
    
    
    @discord.ui.button()
    async def configure_vc(self, interaction: discord.Interaction, button: discord.ui.Button):
        ...