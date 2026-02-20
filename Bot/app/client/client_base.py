import discord
import os
import asyncio
from discord import app_commands

from dotenv import load_dotenv
from datetime import datetime, timedelta
from loguru import logger

from client.modules.redis_client import RedisClient
from client.events.on_message import handle_message
from client.modules.ticket import ticket_setup
from client.commands.system import setup as system_setup
from client.modules.tempvc import voice_state_update
from client.modules.tempvc import setup as tempvc_setup
from client.commands.message_tags import setup as tag_setup
from client.modules.ticket_tracker import last_activity, warned, ticket_archive
from client.commands.lock_category import locked_categories
from client.commands.raffle import setup as raffle_setup
from client.commands.otw import register_otw_command

channels_to_track = [1386299832196399217, 1088090554216235019, 1386299925641433198]
staff_roles = [965399119021617162, 965402001066299424]
restoring_categories = set()

join_msg = """### Welcome to Iron Foundry!
Head on over to #💬-speak-to-staff and click "Join CC" to create a ticket to be ranked and invited into the cc!"""


async def ticket_cleanup_task(client: discord.Client):
    await client.wait_until_ready()

    while not client.is_closed():
        now = datetime.now()
        for channel_id, last_time in list(last_activity.items()):
            channel = client.get_channel(channel_id)
            if not channel:
                continue

            if channel.name.startswith("application-"):
                continue

            if (now - last_time >= timedelta(hours=22)) and channel_id not in warned:
                try:
                    await channel.send(
                        "⏰ This ticket has been inactive for almost 24 hours. "
                        "It will be automatically archived in two hours if no further messages are sent."
                    )
                    warned.add(channel_id)
                except Exception as e:
                    print(f"Warning failed for {channel.name}: {e}")

            # 24-hour archive
            elif now - last_time > timedelta(hours=24):
                try:
                    archive = client.get_channel(ticket_archive.id)
                    await archive.send(
                        f"**{channel.name}** auto-archived after 24h of inactivity."
                    )
                    await channel.delete()
                except Exception as e:
                    print(f"Failed to delete {channel.name}: {e}")
                finally:
                    last_activity.pop(channel_id, None)
                    warned.discard(channel_id)

        await asyncio.sleep(600)


class DiscordClient(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.all())
        load_dotenv()
        self.tree = app_commands.CommandTree(self)
        self.token = os.getenv("DISCORD_TOKEN")
        self.redis_client = RedisClient()
        self.preset_guild_id = os.getenv("GUILD_ID")
        self.selected_guild = None

    async def set_guild(self):
        try:
            self.selected_guild = await self.fetch_guild(self.preset_guild_id)
        except discord.errors.Forbidden:
            logger.error("Bot does not have access to the guild")
            return
        if self.selected_guild is None:
            logger.error("Guild not found")
            return
        logger.info(f"Guild set to {self.selected_guild}")

    async def load_commands(self):
        await ticket_setup(self, self.selected_guild)
        await system_setup(self, self.selected_guild)
        await tempvc_setup(self, self.selected_guild)
        await raffle_setup(self, self.selected_guild)
        await tag_setup(self, self.selected_guild)
        register_otw_command(self.tree, self.selected_guild)
        result = await self.tree.sync(guild=self.selected_guild)
        logger.info(f"Commands loaded: {result}")

    async def setup_hook(self):
        await self.redis_client.connect()
        await self.set_guild()
        await self.load_commands()

    async def on_message(self, message: discord.Message):
        await handle_message(self, message)

    async def on_guild_channel_update(self, before, after):
        """Restore channel position if it was moved in a locked category"""
        if after.category_id not in locked_categories:
            return

        # Don't react to our own changes
        if after.category_id in restoring_categories:
            return

        stored_order = locked_categories[after.category_id]

        # Check if position changed
        if before.position != after.position and after.id in stored_order:
            restoring_categories.add(after.category_id)

            try:
                # Wait briefly to batch multiple rapid changes
                await asyncio.sleep(0.5)

                # Restore all channels to stored positions
                category = after.category
                for channel in category.channels:
                    if channel.id in stored_order:
                        expected_pos = stored_order[channel.id]
                        if channel.position != expected_pos:
                            await channel.edit(position=expected_pos)
            finally:
                # Remove lock after a delay
                await asyncio.sleep(1)
                restoring_categories.discard(after.category_id)

    async def on_member_join(self, member: discord.Member):
        general = self.get_channel(945052365873090652)
        logger.info(f"{member} joined the server")
        await member.add_roles(
            *[
                discord.Object(id=1279492982902358119),
                discord.Object(id=1279852765803446403),
                discord.Object(id=1386302676920176640),
                discord.Object(id=1333568211987206238),
            ]
        )
        await general.send(f"{join_msg}\n\n{member.mention}")

    async def on_voice_state_update(self, member, before, after):
        await voice_state_update(member, before, after)

    async def on_ready(self):
        logger.info(f"Bot is ready as {self.user} at {datetime.now()}")
        self.loop.create_task(ticket_cleanup_task(self))
