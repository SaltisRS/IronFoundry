import json
import asyncio
import discord

from json import JSONDecodeError
from discord import app_commands
from discord.ui import View
from .groups.raffle import Raffle
from loguru import logger
from datetime import datetime, timezone


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

def discord_timestamp(iso_string: str | None, style: str = "R") -> str:
    """
    Convert an ISO timestamp to a Discord-formatted timestamp.
    
    Parameters:
    - iso_string: ISO 8601 timestamp string (e.g., from data['last_updated'])
    - style: Discord timestamp style (R = relative, f = short datetime, F = long, etc.)

    Returns:
    - A string like "<t:unix_ts:style>" or "Never" if input is None/invalid
    """
    if not iso_string:
        return "Never"

    try:
        dt = datetime.fromisoformat(iso_string).replace(tzinfo=timezone.utc)
        ts = int(dt.timestamp())
        return f"<t:{ts}:{style}>"
    except Exception:
        return "Never"

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
            embed.set_image(url="https://media.discordapp.net/attachments/965397194482012200/1451652879646588968/RAFFLE_FLYER_2.png?ex=6946f498&is=6945a318&hm=2b32f2f9216fe5c3926138460a320bfc1bc32564988147162cf099fd5824ade9&=&format=webp&quality=lossless&width=1324&height=2353")
            # ---- Totals ----
            embed.add_field(name="💰 Total Pot", value=f"{total_pot:,} GP", inline=True)
            embed.add_field(name="🎫 Total Tickets", value=f"{total_tickets:,}", inline=True)
            embed.add_field(name="💎 Total Donations", value=f"{total_donations:,} GP", inline=True)

            # ---- Prizes ----
            embed.add_field(
                name="🏆 Raffle Distribution",
                value=(
                    f"**Clan Coffer (50%):** {clan_coffer:,} GP\n"
                    f"**1st Place (37.5%):** {first_place:,} GP\n"
                    f"**2nd Place (12.5%):** {second_place:,} GP"
                ),
                inline=False,
            )

            field_count = 4  # already added fields

            # =====================
            # Ticket Holders
            # =====================
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

                for i, chunk in enumerate(chunks):
                    if field_count >= 25:
                        break
                    embed.add_field(
                        name="🎫 Ticket Holders" if i == 0 else f"🎫 Ticket Holders (Part {i+1})",
                        value=chunk,
                        inline=False,
                    )
                    field_count += 1
            else:
                embed.add_field(
                    name="🎫 Ticket Holders",
                    value="No tickets purchased yet",
                    inline=False,
                )
                field_count += 1

            # =====================
            # Donators
            # =====================
            if donations_data and field_count < 25:
                sorted_donations = sorted(
                    donations_data.items(),
                    key=lambda item: item[1].get("amount", 0),
                    reverse=True,
                )

                lines = []
                for uid, info in sorted_donations:
                    member = guild.get_member(int(uid))
                    name = member.mention if member else f"Unknown User (ID: {uid})"
                    lines.append(f"{name}: {info.get('amount', 0):,} GP")

                chunks, current = [], []
                for line in lines:
                    if sum(len(x) + 1 for x in current) + len(line) > 1024:
                        chunks.append("\n".join(current))
                        current = [line]
                    else:
                        current.append(line)

                if current:
                    chunks.append("\n".join(current))

                for i, chunk in enumerate(chunks):
                    if field_count >= 25:
                        break
                    embed.add_field(
                        name="💎 Donators" if i == 0 else f"💎 Donators (Part {i+1})",
                        value=chunk,
                        inline=False,
                    )
                    field_count += 1
            elif field_count < 25:
                embed.add_field(
                    name="💎 Donators",
                    value="No donations yet",
                    inline=False,
                )

            embed.set_footer(
                text=f"Last updated: {discord_timestamp(data.get('last_updated'))} | 1 ticket = 1M GP"
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
        message = await channel.get_message(info["message_id"])
    except discord.NotFound:
        return

    view = RaffleView()
    view.message = message
    persistent_view_message = message
    await view.update_view()

def _make_transaction(
    *,
    tx_type: str,
    handler_id: int,
    target_id: int | None = None,
    amount: int | None = None,
):
    return {
        "type": tx_type,
        "handler": str(handler_id),
        "target": str(target_id) if target_id else None,
        "amount": amount,
        "timestamp": discord.utils.utcnow().isoformat(),
    }

# =========================
# Ticket Commands
# =========================

@raffle.command()
@has_allowed_role()
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
        
        data.setdefault("transactions", [])
        data["transactions"].append(
            _make_transaction(
                tx_type="ticket_add",
                handler_id=interaction.user.id,
                target_id=user.id,
                amount=num_tickets,
            )
        )

        
        await _write_json(data)

    await interaction.response.send_message(
        f"✅ Added {num_tickets} ticket(s) for {user.display_name}.",
        ephemeral=True,
    )
    await _update_view()


@raffle.command()
@has_allowed_role()
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
        data.setdefault("transactions", [])
        data["transactions"].append(
            _make_transaction(
                tx_type="ticket_remove",
                handler_id=interaction.user.id,
                target_id=user.id,
                amount=num_tickets,
            )
        )

        await _write_json(data)

    await interaction.response.send_message(msg, ephemeral=True)
    await _update_view()


# =========================
# Donation Commands
# =========================

@raffle.command()
@has_allowed_role()
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
        data.setdefault("transactions", [])
        data["transactions"].append(
            _make_transaction(
                tx_type="donation_add",
                handler_id=interaction.user.id,
                target_id=user.id,
                amount=gp_amount,
            )
        )

        await _write_json(data)

    await interaction.response.send_message(
        f"✅ Added {gp_amount:,} GP to {user.display_name}'s donations.",
        ephemeral=True,
    )
    await _update_view()


@raffle.command()
@has_allowed_role()
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
        data.setdefault("transactions", [])
        data["transactions"].append(
            _make_transaction(
                tx_type="donation_remove",
                handler_id=interaction.user.id,
                target_id=user.id,
                amount=gp_amount,
            )
        )

        await _write_json(data)

    await interaction.response.send_message(msg, ephemeral=True)
    await _update_view()


# =========================
# View Commands
# =========================

@raffle.command()
@has_allowed_role()
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

@raffle.command()
@app_commands.default_permissions(administrator=True)
async def clear(interaction: discord.Interaction):
    """Clear all raffle tickets and donations"""

    async with _json_lock:
        data = await _read_json()

        data["tickets"] = {}
        data["donations"] = {}
        data["last_updated"] = discord.utils.utcnow().isoformat()

        await _write_json(data)

    await interaction.response.send_message(
        "🧹 Raffle cleared! All tickets and donations have been reset.",
        ephemeral=True,
    )

    await _update_view()

@raffle.command()
@app_commands.describe(
    handler="Filter by staff member who performed the action",
    target="Filter by user who was affected",
    tx_type="Filter by transaction type (ticket_add, ticket_remove, donation_add, donation_remove, raffle_clear)"
)
async def audit(
    interaction: discord.Interaction,
    handler: discord.Member | None = None,
    target: discord.Member | None = None,
    tx_type: str | None = None,
):
    """Show raffle transactions with optional filters"""

    data = await _read_json()
    transactions = data.get("transactions", [])

    if not transactions:
        return await interaction.response.send_message(
            "No transactions recorded yet.",
            ephemeral=True,
        )

    # Apply filters
    filtered = []

    for tx in transactions:
        # Filter handler
        if handler and str(tx["handler"]) != str(handler.id):
            continue

        # Filter target
        if target:
            if tx.get("target") != str(target.id):
                continue

        # Filter transaction type
        if tx_type and tx.get("type") != tx_type:
            continue

        filtered.append(tx)

    if not filtered:
        return await interaction.response.send_message(
            "No transactions match the specified filters.",
            ephemeral=True,
        )

    # Sort chronologically
    filtered.sort(key=lambda tx: tx.get("timestamp", ""))

    guild = interaction.guild
    lines = []

    for tx in filtered:
        handler_id = int(tx["handler"])
        target_id = int(tx["target"]) if tx.get("target") else None
        amount = tx.get("amount")
        tx_type_val = tx.get("type")
        timestamp = tx.get("timestamp", "Unknown Time")

        handler_member = guild.get_member(handler_id) if guild else None
        handler_name = handler_member.mention if handler_member else f"Unknown User (ID: {handler_id})"

        target_name = "—"
        if target_id:
            target_member = guild.get_member(target_id) if guild else None
            target_name = target_member.mention if target_member else f"Unknown User (ID: {target_id})"

        tx_map = {
            "ticket_add": "Added Tickets",
            "ticket_remove": "Removed Tickets",
            "donation_add": "Added Donation",
            "donation_remove": "Removed Donation",
            "raffle_clear": "Cleared Raffle",
        }
        tx_label = tx_map.get(tx_type_val, tx_type_val)

        line = f"[{timestamp}] {handler_name} → {target_name} | {tx_label}"
        if amount is not None:
            line += f" ({amount})"

        lines.append(line)

    # Chunk lines safely
    chunks, current = [], []
    for line in lines:
        if sum(len(x) + 1 for x in current) + len(line) > 1024:
            chunks.append("\n".join(current))
            current = [line]
        else:
            current.append(line)
    if current:
        chunks.append("\n".join(current))

    embed = discord.Embed(
        title="📜 Raffle Transaction Audit",
        description=f"Total matching transactions: {len(filtered)}",
        color=discord.Color.dark_blue(),
    )

    for i, chunk in enumerate(chunks[:25], 1):
        embed.add_field(
            name="Transactions" if i == 1 else f"Transactions (Part {i})",
            value=chunk,
            inline=False,
        )

    await interaction.response.send_message(embed=embed, ephemeral=True)


@raffle.command()
async def audit_summary(interaction: discord.Interaction):
    """Show a summary of handlers and which users they have handled"""

    data = await _read_json()
    tickets_data = data.get("tickets", {})
    donations_data = data.get("donations", {})

    # handler_id -> { "tickets": set(user_ids), "donations": set(user_ids) }
    handler_map: dict[str, dict[str, set[str]]] = {}

    # Collect ticket handlers
    for user_id, user_data in tickets_data.items():
        for handler_id in user_data.get("handler", []):
            handler_map.setdefault(handler_id, {"tickets": set(), "donations": set()})
            handler_map[handler_id]["tickets"].add(user_id)

    # Collect donation handlers
    for user_id, user_data in donations_data.items():
        for handler_id in user_data.get("handler", []):
            handler_map.setdefault(handler_id, {"tickets": set(), "donations": set()})
            handler_map[handler_id]["donations"].add(user_id)

    if not handler_map:
        return await interaction.response.send_message(
            "No handler activity recorded yet.",
            ephemeral=True,
        )

    guild = interaction.guild
    embed = discord.Embed(
        title="🛠️ Raffle Handler Summary",
        description="Shows which users each staff member has handled tickets or donations for",
        color=discord.Color.dark_gold(),
    )

    field_count = 0

    for handler_id, types in sorted(handler_map.items(), key=lambda x: (len(x[1]["tickets"]) + len(x[1]["donations"])), reverse=True):
        if field_count >= 25:
            break

        handler_member = guild.get_member(int(handler_id)) if guild else None
        handler_name = handler_member.mention if handler_member else f"Unknown User (ID: {handler_id})"

        lines = []

        # Tickets handled
        for uid in sorted(types["tickets"]):
            member = guild.get_member(int(uid)) if guild else None
            name = member.mention if member else f"Unknown User (ID: {uid})"
            lines.append(f"🎫 {name}")

        # Donations handled
        for uid in sorted(types["donations"]):
            member = guild.get_member(int(uid)) if guild else None
            name = member.mention if member else f"Unknown User (ID: {uid})"
            lines.append(f"💎 {name}")

        if not lines:
            lines.append("—")

        # Chunk lines safely
        chunks, current = [], []
        for line in lines:
            if sum(len(x) + 1 for x in current) + len(line) > 1024:
                chunks.append("\n".join(current))
                current = [line]
            else:
                current.append(line)
        if current:
            chunks.append("\n".join(current))

        for i, chunk in enumerate(chunks):
            if field_count >= 25:
                break
            embed.add_field(
                name=handler_name if i == 0 else f"{handler_name} (cont.)",
                value=chunk,
                inline=False,
            )
            field_count += 1

    await interaction.response.send_message(embed=embed, ephemeral=True)


# =========================
# Setup
# =========================

async def setup(client: discord.Client, guild: discord.Guild):
    client.tree.add_command(raffle, guild=guild)
    client.loop.create_task(_restore_persistent_view(client))
