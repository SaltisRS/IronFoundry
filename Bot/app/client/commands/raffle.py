import json
import asyncio
import discord

from json import JSONDecodeError
from discord import app_commands
from discord.ui import View
from .groups.raffle import Raffle
from loguru import logger


DATA_FILE = "app/client/commands/raffle.json"
raffle = Raffle()
allowed_role_id = 1451624339819462706
TICKET_VALUE_GP = 1_000_000

persistent_view_message: discord.Message | None = None
_json_lock = asyncio.Lock()


# =========================
# JSON helpers (async-safe)
# =========================

def _sync_read_json():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, JSONDecodeError):
        return {
            "tickets": {},
            "donations": {},
            "last_updated": None,
            "persistent_message": None,
        }


def _sync_write_json(data: dict):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


async def _read_json():
    return await asyncio.to_thread(_sync_read_json)


async def _write_json(data: dict):
    await asyncio.to_thread(_sync_write_json, data)


# =========================
# Raffle View
# =========================

class RaffleView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.message: discord.Message | None = None
        logger.info("RaffleView initialized")

    async def update_view(self):
        try:
            if not self.message:
                return

            guild = self.message.guild
            if not guild:
                return

            data = await _read_json()
            tickets_data = data.get("tickets", {})
            donations_data = data.get("donations", {})

            total_tickets = sum(v.get("tickets", 0) for v in tickets_data.values())
            total_donations = sum(v.get("amount", 0) for v in donations_data.values())

            total_pot = total_donations + (total_tickets * TICKET_VALUE_GP)

            clan_coffer = total_pot // 2
            raffle_pool = total_pot - clan_coffer
            first_place = raffle_pool * 3 // 4
            second_place = raffle_pool - first_place

            embed = discord.Embed(
                title="🎟️ Raffle Information",
                description="Current raffle stats and prize breakdown",
                color=discord.Color.gold(),
            )

            embed.add_field(name="💰 Total Pot", value=f"{total_pot:,} GP", inline=True)
            embed.add_field(name="🎫 Total Tickets", value=f"{total_tickets:,}", inline=True)
            embed.add_field(name="💎 Total Donations", value=f"{total_donations:,} GP", inline=True)

            embed.add_field(
                name="🏆 Raffle Distribution",
                value=(
                    f"**Clan Coffer (50%):** {clan_coffer:,} GP\n"
                    f"**1st Place (37.5%):** {first_place:,} GP\n"
                    f"**2nd Place (12.5%):** {second_place:,} GP"
                ),
                inline=False,
            )

            if tickets_data:
                sorted_tickets = sorted(
                    tickets_data.items(),
                    key=lambda item: item[1].get("tickets", 0),
                    reverse=True,
                )

                lines = []
                for uid, info in sorted_tickets:
                    member = guild.get_member(int(uid))
                    name = member.mention if member else f"Unknown User (ID: {uid})"
                    lines.append(f"{name}: {info.get('tickets', 0)} ticket(s)")

                chunks, current = [], []
                for line in lines:
                    if sum(len(x) + 1 for x in current) + len(line) > 1024:
                        chunks.append("\n".join(current))
                        current = [line]
                    else:
                        current.append(line)

                if current:
                    chunks.append("\n".join(current))

                for i, chunk in enumerate(chunks[:25], 1):
                    embed.add_field(
                        name=f"🎫 Ticket Holders (Part {i})",
                        value=chunk,
                        inline=False,
                    )
            else:
                embed.add_field(
                    name="🎫 Ticket Holders",
                    value="No tickets purchased yet",
                    inline=False,
                )

            embed.set_footer(
                text=f"Last updated: {data.get('last_updated') or 'Never'} | 1 ticket = 1M GP"
            )

            await self.message.edit(embed=embed)

        except discord.HTTPException:
            pass
        except Exception:
            logger.exception("Unexpected error updating raffle view")


# =========================
# Permissions
# =========================

def has_allowed_role():
    async def predicate(interaction: discord.Interaction) -> bool:
        if isinstance(interaction.user, discord.Member):
            if any(role.id == allowed_role_id for role in interaction.user.roles):
                return True

        await interaction.response.send_message(
            "You do not have permission to use this command.",
            ephemeral=True,
        )
        return False

    return app_commands.check(predicate)


# =========================
# View helpers
# =========================

async def _update_view():
    global persistent_view_message
    if not persistent_view_message:
        return

    view = RaffleView()
    view.message = persistent_view_message
    await view.update_view()


async def _restore_persistent_view(client: discord.Client):
    global persistent_view_message

    data = await _read_json()
    info = data.get("persistent_message")
    if not info:
        return

    channel = client.get_channel(info["channel_id"])
    if not channel:
        return

    try:
        message = await channel.fetch_message(info["message_id"])
    except discord.NotFound:
        return

    view = RaffleView()
    view.message = message
    persistent_view_message = message
    await view.update_view()


# =========================
# Ticket Commands
# =========================

@raffle.command()
@has_allowed_role()
@app_commands.default_permissions(manage_guild=True)
async def add(interaction: discord.Interaction, user: discord.Member, num_tickets: int = 1):
    if interaction.user.id == user.id or num_tickets <= 0:
        return await interaction.response.send_message(
            "Invalid ticket operation.", ephemeral=True
        )

    async with _json_lock:
        data = await _read_json()
        uid = str(user.id)
        hid = str(interaction.user.id)

        data.setdefault("tickets", {})
        data["tickets"].setdefault(uid, {"handler": [], "tickets": 0})

        data["tickets"][uid]["tickets"] += num_tickets
        if hid not in data["tickets"][uid]["handler"]:
            data["tickets"][uid]["handler"].append(hid)

        data["last_updated"] = discord.utils.utcnow().isoformat()
        await _write_json(data)

    await interaction.response.send_message(
        f"✅ Added {num_tickets} ticket(s) for {user.display_name}.",
        ephemeral=True,
    )
    await _update_view()


@raffle.command()
@has_allowed_role()
@app_commands.default_permissions(manage_guild=True)
async def remove(interaction: discord.Interaction, user: discord.Member, num_tickets: int = 1):
    if num_tickets <= 0:
        return await interaction.response.send_message(
            "Number of tickets must be greater than 0.", ephemeral=True
        )

    async with _json_lock:
        data = await _read_json()
        uid = str(user.id)

        if uid not in data.get("tickets", {}):
            return await interaction.response.send_message(
                f"{user.display_name} has no tickets.",
                ephemeral=True,
            )

        if num_tickets >= data["tickets"][uid]["tickets"]:
            del data["tickets"][uid]
            msg = f"✅ Removed all tickets for {user.display_name}."
        else:
            data["tickets"][uid]["tickets"] -= num_tickets
            msg = f"✅ Removed {num_tickets} ticket(s) for {user.display_name}."

        data["last_updated"] = discord.utils.utcnow().isoformat()
        await _write_json(data)

    await interaction.response.send_message(msg, ephemeral=True)
    await _update_view()


# =========================
# Donation Commands
# =========================

@raffle.command()
@has_allowed_role()
@app_commands.default_permissions(manage_guild=True)
async def add_donated(interaction: discord.Interaction, user: discord.Member, gp_amount: int):
    if gp_amount <= 0:
        return await interaction.response.send_message(
            "Donation amount must be greater than 0.",
            ephemeral=True,
        )

    async with _json_lock:
        data = await _read_json()
        uid = str(user.id)
        hid = str(interaction.user.id)

        data.setdefault("donations", {})
        data["donations"].setdefault(uid, {"handler": [], "amount": 0})

        data["donations"][uid]["amount"] += gp_amount
        if hid not in data["donations"][uid]["handler"]:
            data["donations"][uid]["handler"].append(hid)

        data["last_updated"] = discord.utils.utcnow().isoformat()
        await _write_json(data)

    await interaction.response.send_message(
        f"✅ Added {gp_amount:,} GP to {user.display_name}'s donations.",
        ephemeral=True,
    )
    await _update_view()


@raffle.command()
@has_allowed_role()
@app_commands.default_permissions(manage_guild=True)
async def remove_donated(interaction: discord.Interaction, user: discord.Member, gp_amount: int):
    if gp_amount <= 0:
        return await interaction.response.send_message(
            "Donation amount must be greater than 0.",
            ephemeral=True,
        )

    async with _json_lock:
        data = await _read_json()
        uid = str(user.id)

        if uid not in data.get("donations", {}):
            return await interaction.response.send_message(
                f"{user.display_name} has no donations.",
                ephemeral=True,
            )

        current = data["donations"][uid]["amount"]
        if gp_amount >= current:
            del data["donations"][uid]
            msg = f"✅ Removed all donations for {user.display_name}."
        else:
            data["donations"][uid]["amount"] -= gp_amount
            msg = f"✅ Removed {gp_amount:,} GP from {user.display_name}'s donations."

        data["last_updated"] = discord.utils.utcnow().isoformat()
        await _write_json(data)

    await interaction.response.send_message(msg, ephemeral=True)
    await _update_view()


# =========================
# View Commands
# =========================

@raffle.command()
@has_allowed_role()
@app_commands.default_permissions(manage_guild=True)
async def send_view(interaction: discord.Interaction):
    global persistent_view_message

    if persistent_view_message:
        return await interaction.response.send_message(
            "A raffle view is already active.",
            ephemeral=True,
        )

    view = RaffleView()
    embed = discord.Embed(
        title="🎟️ Raffle Information",
        description="Loading...",
        color=discord.Color.blue(),
    )

    message = await interaction.channel.send(embed=embed, view=view)
    view.message = message
    persistent_view_message = message

    async with _json_lock:
        data = await _read_json()
        data["persistent_message"] = {
            "channel_id": message.channel.id,
            "message_id": message.id,
        }
        await _write_json(data)

    await view.update_view()
    await interaction.response.send_message("✅ Raffle view sent!", ephemeral=True)


@raffle.command()
@has_allowed_role()
@app_commands.default_permissions(manage_guild=True)
async def remove_view(interaction: discord.Interaction):
    global persistent_view_message

    if not persistent_view_message:
        return await interaction.response.send_message(
            "⚠️ No raffle view is active.",
            ephemeral=True,
        )

    try:
        await persistent_view_message.delete()
    except discord.NotFound:
        pass

    persistent_view_message = None

    async with _json_lock:
        data = await _read_json()
        data["persistent_message"] = None
        await _write_json(data)

    await interaction.response.send_message("✅ Raffle view removed.", ephemeral=True)


# =========================
# Setup
# =========================

async def setup(client: discord.Client, guild: discord.Guild):
    client.tree.add_command(raffle, guild=guild)
    client.loop.create_task(_restore_persistent_view(client))
