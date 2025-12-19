import json
import discord


from discord import app_commands
from discord.ui import View
from .groups.raffle import Raffle
from loguru import logger


DATA_FILE = "app/client/commands/raffle.json"
raffle = Raffle()
allowed_role_id = 1451624339819462706
TICKET_VALUE_GP = 1_000_000

persistent_view_message: discord.Message = None


async def _write_json(json_dict: dict):
    with open(DATA_FILE, "w") as f:
        json.dump(json_dict, f, indent=2)


async def _read_json():
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        return {"tickets": {}, "donations": {}, "last_updated": None}


class RaffleView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.message = None
        logger.info("RaffleView initialized")

    async def update_view(self):
        try:
            logger.info("Starting view update")
            
            if not self.message:
                logger.error("Cannot update view: message is None")
                return

            logger.debug(f"Message ID: {self.message.id}, Channel: {self.message.channel.id}")

            data = await _read_json()
            logger.debug(f"Data loaded: tickets={len(data['tickets'])}, donations={len(data['donations'])}")

            total_tickets_count = sum(
                user_data.get("tickets", 0) for user_data in data["tickets"].values()
            )
            total_donations_gp = sum(
                user_data.get("amount", 0) for user_data in data["donations"].values()
            )

            logger.debug(f"Total tickets: {total_tickets_count}, Total donations: {total_donations_gp}")

            # Calculate GP value from tickets
            tickets_gp_value = total_tickets_count * TICKET_VALUE_GP
            total_pot_gp = total_donations_gp + tickets_gp_value

            # Calculate splits
            clan_coffer = total_pot_gp * 0.5
            raffle_pool = total_pot_gp * 0.5
            first_place = raffle_pool * 0.75
            second_place = raffle_pool * 0.25

            logger.debug(f"Pot calculations: total={total_pot_gp}, clan={clan_coffer}, 1st={first_place}, 2nd={second_place}")

            embed = discord.Embed(
                title="🎟️ Raffle Information",
                description="Current raffle stats and prize breakdown",
                color=discord.Color.gold(),
            )

            # Pot Information
            embed.add_field(
                name="💰 Total Pot",
                value=f"{total_pot_gp:,} GP",
                inline=True,
            )
            embed.add_field(
                name="🎫 Total Tickets",
                value=f"{total_tickets_count:,}",
                inline=True,
            )
            embed.add_field(
                name="💎 Total Donations",
                value=f"{total_donations_gp:,} GP",
                inline=True,
            )

            # Prize Distribution
            embed.add_field(
                name="🏆 Prize Distribution",
                value=(
                    f"**Clan Coffer (50%):** {clan_coffer:,.0f} GP\n"
                    f"**1st Place (37.5%):** {first_place:,.0f} GP\n"
                    f"**2nd Place (12.5%):** {second_place:,.0f} GP"
                ),
                inline=False,
            )

            # Ticket holders list
            if data["tickets"]:
                logger.debug(f"Processing {len(data['tickets'])} ticket holders")
                sorted_tickets = sorted(
                    data["tickets"].items(),
                    key=lambda item: item[1]["tickets"],
                    reverse=True,
                )

                ticket_list = []
                for user_id, user_data in sorted_tickets:
                    try:
                        user = self.message.guild.get_member(int(user_id))
                        if user:
                            ticket_list.append(
                                f"{user.mention}: {user_data['tickets']} ticket(s)"
                            )
                        else:
                            logger.warning(f"User {user_id} not found in guild")
                            ticket_list.append(
                                f"Unknown User (ID: {user_id}): {user_data['tickets']} ticket(s)"
                            )
                    except Exception as e:
                        logger.error(f"Error processing user {user_id}: {e}", exc_info=True)
                        ticket_list.append(
                            f"Error processing user {user_id}: {user_data['tickets']} ticket(s)"
                        )

                # Split into multiple fields if too long
                ticket_text = "\n".join(ticket_list)
                logger.debug(f"Ticket text length: {len(ticket_text)}")
                
                if len(ticket_text) > 1024:
                    logger.info("Ticket text too long, splitting into chunks")
                    # Split into chunks
                    chunks = []
                    current_chunk = []
                    current_length = 0

                    for line in ticket_list:
                        line_length = len(line) + 1  # +1 for newline
                        if current_length + line_length > 1024:
                            chunks.append("\n".join(current_chunk))
                            current_chunk = [line]
                            current_length = line_length
                        else:
                            current_chunk.append(line)
                            current_length += line_length

                    if current_chunk:
                        chunks.append("\n".join(current_chunk))

                    logger.debug(f"Split into {len(chunks)} chunks")
                    for i, chunk in enumerate(chunks, 1):
                        embed.add_field(
                            name=f"🎫 Ticket Holders (Part {i})",
                            value=chunk,
                            inline=False,
                        )
                else:
                    embed.add_field(
                        name="🎫 Ticket Holders",
                        value=ticket_text,
                        inline=False,
                    )
            else:
                logger.debug("No ticket holders")
                embed.add_field(
                    name="🎫 Ticket Holders",
                    value="No tickets purchased yet",
                    inline=False,
                )

            embed.set_footer(
                text=f"Last updated: {data['last_updated'] or 'Never'} | 1 ticket = 1M GP"
            )

            logger.info("Attempting to edit message with new embed")
            await self.message.edit(embed=embed)
            logger.info("View update completed successfully")

        except discord.HTTPException as e:
            logger.error(f"Discord HTTP error during view update: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"Unexpected error during view update: {e}", exc_info=True)


# Decorator to check if the user has the allowed role
def has_allowed_role():
    async def predicate(interaction: discord.Interaction) -> bool:
        if isinstance(interaction.user, discord.Member):
            if allowed_role_id in [role.id for role in interaction.user.roles]:
                logger.debug(f"User {interaction.user.id} has allowed role")
                return True
        logger.warning(f"User {interaction.user.id} does not have allowed role")
        await interaction.response.send_message(
            "You do not have permission to use this command.", ephemeral=True
        )
        return False

    return app_commands.check(predicate)


async def _update_view():
    """Helper function to update the persistent view"""
    global persistent_view_message
    try:
        if persistent_view_message:
            logger.info(f"Updating persistent view (message ID: {persistent_view_message.id})")
            view = RaffleView()
            view.message = persistent_view_message
            await view.update_view()
        else:
            logger.warning("Attempted to update view but persistent_view_message is None")
    except Exception as e:
        logger.error(f"Error in _update_view: {e}", exc_info=True)

@raffle.command()
@has_allowed_role()
@app_commands.default_permissions(manage_guild=True)
async def add(
    interaction: discord.Interaction, user: discord.Member, num_tickets: int = 1
):
    """Add raffle tickets for a user"""
    if interaction.user.id == user.id:
        return await interaction.response.send_message(
            "You cannot add tickets to yourself.", ephemeral=True
        )

    if num_tickets <= 0:
        return await interaction.response.send_message(
            "Number of tickets must be greater than 0.", ephemeral=True
        )

    data = await _read_json()
    user_id_str = str(user.id)
    handler_id_str = str(interaction.user.id)

    if user_id_str not in data["tickets"]:
        data["tickets"][user_id_str] = {"handler": [], "tickets": 0}

    data["tickets"][user_id_str]["tickets"] += num_tickets
    if handler_id_str not in data["tickets"][user_id_str]["handler"]:
        data["tickets"][user_id_str]["handler"].append(handler_id_str)
    data["last_updated"] = discord.utils.utcnow().isoformat()

    await _write_json(data)
    await interaction.response.send_message(
        f"✅ Added {num_tickets} ticket(s) for {user.display_name}. "
        f"They now have {data['tickets'][user_id_str]['tickets']} ticket(s).",
        ephemeral=True,
    )
    await _update_view()


@raffle.command()
@has_allowed_role()
@app_commands.default_permissions(manage_guild=True)
async def remove(
    interaction: discord.Interaction, user: discord.Member, num_tickets: int = 1
):
    """Remove raffle tickets from a user"""
    if num_tickets <= 0:
        return await interaction.response.send_message(
            "Number of tickets must be greater than 0.", ephemeral=True
        )

    data = await _read_json()
    user_id_str = str(user.id)
    handler_id_str = str(interaction.user.id)

    if (
        user_id_str not in data["tickets"]
        or data["tickets"][user_id_str]["tickets"] == 0
    ):
        return await interaction.response.send_message(
            f"{user.display_name} has no tickets to remove.", ephemeral=True
        )

    current_tickets = data["tickets"][user_id_str]["tickets"]
    if num_tickets >= current_tickets:
        removed_tickets = current_tickets
        del data["tickets"][user_id_str]
        message = (
            f"✅ Removed all {removed_tickets} ticket(s) for {user.display_name}. "
            f"They now have 0 tickets."
        )
    else:
        data["tickets"][user_id_str]["tickets"] -= num_tickets
        if handler_id_str not in data["tickets"][user_id_str]["handler"]:
            data["tickets"][user_id_str]["handler"].append(handler_id_str)
        message = (
            f"✅ Removed {num_tickets} ticket(s) for {user.display_name}. "
            f"They now have {data['tickets'][user_id_str]['tickets']} ticket(s)."
        )
    data["last_updated"] = discord.utils.utcnow().isoformat()

    await _write_json(data)
    await interaction.response.send_message(message, ephemeral=True)
    await _update_view()


@raffle.command()
@has_allowed_role()
async def list(interaction: discord.Interaction):
    """List all users with raffle tickets"""
    data = await _read_json()
    tickets_data = data["tickets"]

    if not tickets_data:
        return await interaction.response.send_message(
            "No one currently has raffle tickets.", ephemeral=True
        )

    sorted_tickets = sorted(
        tickets_data.items(), key=lambda item: item[1]["tickets"], reverse=True
    )

    ticket_list = []
    for user_id, user_data in sorted_tickets:
        user = interaction.guild.get_member(int(user_id))
        if user:
            ticket_list.append(
                f"{user.display_name}: {user_data['tickets']} ticket(s)"
            )
        else:
            ticket_list.append(
                f"Unknown User (ID: {user_id}): {user_data['tickets']} ticket(s)"
            )

    embed = discord.Embed(
        title="🎫 Current Raffle Tickets",
        description="\n".join(ticket_list),
        color=discord.Color.green(),
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


@raffle.command()
@has_allowed_role()
@app_commands.default_permissions(manage_guild=True)
async def send_view(interaction: discord.Interaction):
    """Sends a persistent view that displays current raffle information"""
    global persistent_view_message

    if persistent_view_message:
        await interaction.response.send_message(
            "A raffle view is already active. Please remove the old one first.",
            ephemeral=True,
        )
        return

    view = RaffleView()
    embed = discord.Embed(
        title="🎟️ Raffle Information",
        description="Loading...",
        color=discord.Color.blue(),
    )
    message = await interaction.channel.send(embed=embed, view=view)
    view.message = message
    persistent_view_message = message
    await view.update_view()
    await interaction.response.send_message(
        "✅ Raffle view sent!", ephemeral=True
    )


@raffle.command()
@has_allowed_role()
@app_commands.default_permissions(manage_guild=True)
@app_commands.describe(
    gp_amount="Full gp amount, 1M = 1_000_000 or 1000000 whichever works best for you."
)
async def add_donated(
    interaction: discord.Interaction, user: discord.Member, gp_amount: int
):
    """Add a GP donation for a user"""
    if gp_amount <= 0:
        return await interaction.response.send_message(
            "Donation amount must be greater than 0.", ephemeral=True
        )

    data = await _read_json()
    user_id_str = str(user.id)
    handler_id_str = str(interaction.user.id)

    if user_id_str not in data["donations"]:
        data["donations"][user_id_str] = {"handler": [], "amount": 0}

    data["donations"][user_id_str]["amount"] += gp_amount
    if handler_id_str not in data["donations"][user_id_str]["handler"]:
        data["donations"][user_id_str]["handler"].append(handler_id_str)
    data["last_updated"] = discord.utils.utcnow().isoformat()

    await _write_json(data)
    await interaction.response.send_message(
        f"✅ Added {gp_amount:,} GP to {user.display_name}'s donations. "
        f"They have now donated {data['donations'][user_id_str]['amount']:,} GP.",
        ephemeral=True,
    )
    await _update_view()


@raffle.command()
@has_allowed_role()
@app_commands.default_permissions(manage_guild=True)
@app_commands.describe(
    gp_amount="Full gp amount, 1M = 1_000_000 or 1000000 whichever works best for you."
)
async def remove_donated(
    interaction: discord.Interaction, user: discord.Member, gp_amount: int
):
    """Remove a GP donation from a user"""
    if gp_amount <= 0:
        return await interaction.response.send_message(
            "Donation amount must be greater than 0.", ephemeral=True
        )

    data = await _read_json()
    user_id_str = str(user.id)
    handler_id_str = str(interaction.user.id)

    if (
        user_id_str not in data["donations"]
        or data["donations"][user_id_str]["amount"] == 0
    ):
        return await interaction.response.send_message(
            f"{user.display_name} has no donations to remove.", ephemeral=True
        )

    current_amount = data["donations"][user_id_str]["amount"]
    if gp_amount >= current_amount:
        removed_amount = current_amount
        del data["donations"][user_id_str]
        message = (
            f"✅ Removed all {removed_amount:,} GP from {user.display_name}'s donations. "
            f"They now have 0 GP donated."
        )
    else:
        data["donations"][user_id_str]["amount"] -= gp_amount
        if handler_id_str not in data["donations"][user_id_str]["handler"]:
            data["donations"][user_id_str]["handler"].append(handler_id_str)
        message = (
            f"✅ Removed {gp_amount:,} GP from {user.display_name}'s donations. "
            f"They have now donated {data['donations'][user_id_str]['amount']:,} GP."
        )
    data["last_updated"] = discord.utils.utcnow().isoformat()

    await _write_json(data)
    await interaction.response.send_message(message, ephemeral=True)
    await _update_view()


@raffle.command()
@has_allowed_role()
async def list_donations(interaction: discord.Interaction):
    """List all users who have donated GP"""
    data = await _read_json()
    donations_data = data["donations"]

    if not donations_data:
        return await interaction.response.send_message(
            "No one has donated GP yet.", ephemeral=True
        )

    sorted_donations = sorted(
        donations_data.items(), key=lambda item: item[1]["amount"], reverse=True
    )

    donation_list = []
    for user_id, user_data in sorted_donations:
        user = interaction.guild.get_member(int(user_id))
        if user:
            donation_list.append(f"{user.display_name}: {user_data['amount']:,} GP")
        else:
            donation_list.append(
                f"Unknown User (ID: {user_id}): {user_data['amount']:,} GP"
            )

    embed = discord.Embed(
        title="💎 Current Donations",
        description="\n".join(donation_list),
        color=discord.Color.purple(),
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

@raffle.command()
@has_allowed_role()
@app_commands.default_permissions(manage_guild=True)
async def remove_view(interaction: discord.Interaction):
    """Removes the persistent raffle view"""
    global persistent_view_message
    if persistent_view_message:
        try:
            await persistent_view_message.delete()
            persistent_view_message = None
            await interaction.response.send_message(
                "✅ Raffle view removed.", ephemeral=True
            )
        except discord.NotFound:
            persistent_view_message = None
            await interaction.response.send_message(
                "⚠️ Raffle view message not found. Cleared reference.",
                ephemeral=True,
            )
    else:
        await interaction.response.send_message(
            "⚠️ No raffle view is currently active.", ephemeral=True
        )

async def setup(client: discord.Client, guild: discord.Guild):
    client.tree.add_command(raffle, guild=guild)