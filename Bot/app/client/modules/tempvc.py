import discord
import asyncio

from discord import app_commands
from loguru import logger

vc_cat = 945052365873090651

active_channels: set[dict[str, int]] = set()


async def is_empty(channel: discord.VoiceChannel):
    if len(channel.members) <= 0:
        return True
    return False

async def check_set(user_id: int):
    for channel in active_channels:
        if channel.get("user_id") == user_id:
            return True
    return False

async def insert_set(channel: discord.VoiceChannel, user_id: int):
    active_channels.add({
        "user_id": user_id,
        "channel_id": channel.id
    })

async def self_destruct(channel: discord.VoiceChannel, user_id: int):
    await asyncio.sleep(600)
    if await is_empty(channel):
        try:
            await channel.delete(reason="Temp VC Timed out.")
            active_channels.remove({"user_id": user_id, "channel_id": channel.id})
        except Exception as e:
            logger.error(e)
    return

class PromptModal(discord.ui.Modal, title="VC Settings"):
    name = discord.ui.TextInput(label="Set a name for the channel", required=False, max_length=20, placeholder="max 20 chars.")
    limit = discord.ui.TextInput(label="Limit the amount of people who can join.", required=False, max_length=2, placeholder="Leave blank or '0' for unlimited")
    
    async def on_submit(self, interaction: discord.Interaction):
        category = interaction.guild.get_channel(vc_cat)
        channel = await category.create_voice_channel(name=self.name.value if self.name.value else interaction.user.name, user_limit=int(self.limit.value) if self.limit.value else None)
        await insert_set(channel, interaction.user.id)
        await interaction.response.send_message(f"Created channel: {channel.name}\nWith config: 'name: {self.name.value}' 'limit: {self.limit.value}'", ephemeral=True, delete_after=5)
        await self_destruct(channel, interaction.user.id)

class PromptView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="Use Default", style=discord.ButtonStyle.green, custom_id="default_vc_btn")
    async def use_default(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            if not await check_set(interaction.user.id):
                category = interaction.guild.get_channel(vc_cat)
                channel = await category.create_voice_channel(name=interaction.user.name, position=1)
                await insert_set(channel, interaction.user.id)
                await interaction.response.send_message(f"Created channel: {channel.name}", ephemeral=True, delete_after=5)
                await self_destruct(channel, interaction.user.id)
                return
        except Exception as e:
            logger.error(e)
        
        await interaction.response.send_message("You already have a voice channel.")
    
    
    @discord.ui.button(label="Configure", style=discord.ButtonStyle.blurple, custom_id="config_vc_btn")
    async def configure_vc(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            if not await check_set(interaction.user.id):
                await interaction.response.send_modal(PromptModal())
        except Exception as e:
            logger.error(e)
            
        await interaction.response.send_message("You already have a voice channel.")


async def voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    if await is_empty(after.channel):
        for channel in active_channels:
            if channel.get("channel_id") == after.channel.id:
                active_channels.remove(channel)
                await after.channel.delete(reason="Last member left VC")
                return
        logger.error("Channel not a Temp VC")
    return

@app_commands.command()
async def send_tempvc_msg(interaction: discord.Interaction):
    view = PromptView()
    await interaction.channel.send("Create your very own voice channel, it self destructs when empty!", view=view)


async def setup(client: discord.Client, guild: discord.Guild):
    client.tree.add_command(send_tempvc_msg, guild=guild)
    client.add_view(PromptView())