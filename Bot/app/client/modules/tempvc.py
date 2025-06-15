import discord
import asyncio

from discord import app_commands
from loguru import logger

vc_cat = 945052365873090651
active_channels: dict[int, int] = {}


async def is_empty(channel: discord.VoiceChannel) -> bool:
    return len(channel.members) == 0


def has_active_channel(user_id: int) -> bool:
    return user_id in active_channels


def add_active_channel(channel: discord.VoiceChannel, user_id: int):
    active_channels[user_id] = channel.id


def remove_active_channel(user_id: int):
    active_channels.pop(user_id, None)


async def self_destruct(channel: discord.VoiceChannel, user_id: int):
    await asyncio.sleep(600)
    if await is_empty(channel):
        try:
            await channel.delete(reason="Temp VC timed out")
            remove_active_channel(user_id)
        except Exception as e:
            logger.error(f"Failed to delete channel {channel.id}: {e}")


class PromptModal(discord.ui.Modal, title="VC Settings"):
    name = discord.ui.TextInput(
        label="Set a name for the channel",
        required=False,
        max_length=20,
        placeholder="max 20 chars."
    )
    limit = discord.ui.TextInput(
        label="Limit the amount of people who can join",
        required=False,
        max_length=2,
        placeholder="Leave blank or '0' for unlimited"
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            category = interaction.guild.get_channel(vc_cat)
            user_limit = 0
            if self.limit.value:
                try:
                    user_limit = int(self.limit.value)
                    if user_limit < 0 or user_limit > 99:
                        user_limit = 0
                except ValueError:
                    user_limit = 0

            channel_name = self.name.value or interaction.user.display_name
            
            channel = await category.create_voice_channel(
                name=channel_name,
                user_limit=user_limit if user_limit > 0 else None,
                position=1
            )
            
            add_active_channel(channel, interaction.user.id)
            
            await interaction.response.send_message(
                f"Created channel: **{channel.name}**\n"
                f"Limit: {'Unlimited' if user_limit == 0 else user_limit}",
                ephemeral=True,
                delete_after=10
            )
            asyncio.create_task(self_destruct(channel, interaction.user.id))
            
        except Exception as e:
            logger.error(f"Failed to create custom VC: {e}")
            await interaction.response.send_message(
                "Failed to create voice channel. Please try again.",
                ephemeral=True,
                delete_after=5
            )


class PromptView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Use Default",
        style=discord.ButtonStyle.green,
        custom_id="default_vc_btn"
    )
    async def use_default(self, interaction: discord.Interaction, button: discord.ui.Button):
        if has_active_channel(interaction.user.id):
            await interaction.response.send_message(
                "You already have an active voice channel!",
                ephemeral=True,
                delete_after=5
            )
            return

        try:
            category = interaction.guild.get_channel(vc_cat)
            channel = await category.create_voice_channel(
                name=interaction.user.display_name,
                position=1
            )
            
            add_active_channel(channel, interaction.user.id)
            
            await interaction.response.send_message(
                f"Created channel: **{channel.name}**",
                ephemeral=True,
                delete_after=10
            )
            
            asyncio.create_task(self_destruct(channel, interaction.user.id))
            
        except Exception as e:
            logger.error(f"Failed to create default VC: {e}")
            await interaction.response.send_message(
                "Failed to create voice channel. Please try again.",
                ephemeral=True,
                delete_after=5
            )

    @discord.ui.button(
        label="Configure",
        style=discord.ButtonStyle.blurple,
        custom_id="config_vc_btn"
    )
    async def configure_vc(self, interaction: discord.Interaction, button: discord.ui.Button):
        if has_active_channel(interaction.user.id):
            await interaction.response.send_message(
                "You already have an active voice channel!",
                ephemeral=True,
                delete_after=5
            )
            return

        try:
            await interaction.response.send_modal(PromptModal())
        except Exception as e:
            logger.error(f"Failed to send modal: {e}")


async def voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    if before.channel and before.channel.id in active_channels.values():
        if await is_empty(before.channel):
            channel_owner = None
            for user_id, channel_id in active_channels.items():
                if channel_id == before.channel.id:
                    channel_owner = user_id
                    break
            
            if channel_owner:
                try:
                    await before.channel.delete(reason="Last member left temp VC")
                    remove_active_channel(channel_owner)
                except Exception as e:
                    logger.error(f"Failed to delete empty VC: {e}")


@app_commands.command(name="send_tempvc_msg")
async def send_tempvc_msg(interaction: discord.Interaction):
    view = PromptView()
    await interaction.response.send_message(
        "🎤 **Create Your Voice Channel**\n"
        "Create your own temporary voice channel that automatically deletes when empty!",
        view=view
    )


async def setup(client: discord.Client, guild: discord.Guild):
    client.tree.add_command(send_tempvc_msg, guild=guild)
    client.add_view(PromptView())