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

def is_users_channel(channel: discord.VoiceChannel, user: discord.Member):
    return active_channels[user.id] == channel.id

def add_active_channel(channel: discord.VoiceChannel, user_id: int):
    active_channels[user_id] = channel.id

def remove_active_channel(user_id: int):
    active_channels.pop(user_id, None)

async def set_invite_permissions(channel: discord.VoiceChannel, invited: discord.Member):
    await channel.set_permissions(target=invited, view_channel=True, connect=True)
    
async def set_permissions(channel: discord.VoiceChannel, user: discord.Member):
    await channel.set_permissions(target=channel.guild.default_role, connect=False, view_channel=False)
    await channel.set_permissions(target=user, connect=True, view_channel=True, move_members=True)

async def self_destruct(channel: discord.VoiceChannel, user_id: int):
    await asyncio.sleep(300)
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
        max_length=30,
        placeholder="max 30 chars."
    )
    limit = discord.ui.TextInput(
        label="Limit the amount of people who can join",
        required=False,
        max_length=2,
        placeholder="Leave blank or '0' for unlimited"
    )
    hidden = discord.ui.TextInput(
        label="Show/Hide channel from channel list",
        required=False,
        max_length=1,
        placeholder="0 Show | 1 Hidden, default 0"
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            category = interaction.guild.get_channel(vc_cat)
            user_limit = 0
            if self.limit.value:
                try:
                    user_limit = int(self.limit.value)
                    if user_limit < 0:
                        user_limit = 0
                    elif user_limit > 99:
                        user_limit = 99
                except ValueError:
                    user_limit = 0

            channel_name = self.name.value or interaction.user.display_name
            
            channel = await category.create_voice_channel(
                name=channel_name,
                user_limit=user_limit if user_limit > 0 else None,
                position=1
            )
            if self.hidden.value == None:
                self.hidden.value = str(0)
            
            add_active_channel(channel, interaction.user.id)
            
            if self.hidden.value == "1":
                try:
                    await set_permissions(channel, interaction.user)
                except Exception as e:
                    logger.error(e)
                    
            await interaction.response.send_message(
                f"Created channel: **{channel.name}**\n"
                f"Limit: {'Unlimited' if user_limit == 0 else user_limit}\n"
                f"Hidden: {'Shown' if self.hidden.value == "0" else 'Hidden'}"
                f"Use /vc_inv @member to invite people to the vc",
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

@app_commands.command()
async def vc_inv(interaction: discord.Interaction, user: discord.Member):
    if not has_active_channel(interaction.user.id):
        await interaction.response.send_message("You need to create a custom Voice Channel to use this command.", ephemeral=True, delete_after=5)
        return
    vc = await interaction.user.fetch_voice()
    if vc == discord.NotFound:
        await interaction.response.send_message("You must be in a custom Voice Channel to use this command.", ephemeral=True, delete_after=5)
        return
    
    if not is_users_channel(vc.channel, interaction.user):
        await interaction.response.send_message("You must be in your own custom Voice Channel to use this command.", ephemeral=True, delete_after=5)
        return
    
    await set_invite_permissions(vc.channel, user)
    try:
        await user.send(f"You have been invited to join: {vc.channel.name}\n{vc.channel.jump_url}")
    except Exception as e:
        logger.error(f"Couldnt Message User\n{e}")
    
    await interaction.response.send_message(f"Invited: {user.display_name}", ephemeral=True, delete_after=5)

async def setup(client: discord.Client, guild: discord.Guild):
    client.tree.add_command(send_tempvc_msg, guild=guild)
    client.tree.add_command(vc_inv, guild=guild)
    client.add_view(PromptView())