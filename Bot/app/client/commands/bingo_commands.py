import discord
from discord import app_commands
from loguru import logger
from datetime import datetime, UTC
from bson import ObjectId

from ..modules.mongo import MongoClient
from .groups.bingo import Bingo
from .tiles import tiles

team_role_ids = [1335716087567880253,1335716138025484408,13357161612324373801,1335716184774934660,1335716209617928245, 1335716161232437381]
teams = []
mongo = MongoClient()
board: list[str] = tiles()
board_image: str = None
group = Bingo()


class BingoModal(discord.ui.Modal, title="Denial Response"):
    reason = discord.ui.TextInput(
        label="Reason for denial",
        max_length=2000,
        style=discord.TextStyle.paragraph,
        required=True
        )
    def __init__(self, team: discord.Role, tile: dict):
        super().__init__()
        self.team = team
        self.tile = tile
        
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message("Tile denied. Messaging affected team with reason.", ephemeral=True)
        self.tile["reason"] = self.reason.value
        await update_db({"_id" : self.team.id}, {"$push": {"denied_tiles": self.tile}})
        resp_channel = discord.utils.get(interaction.guild.channels, id=self.tile["original_channel"])
        await resp_channel.send(f"{self.team.mention} Bingo tile denied by {interaction.user.mention}\nReason:\n```{self.tile['reason']}```\n{interaction.message.jump_url}")

class BingoView(discord.ui.View):
    def __init__(self, team: discord.Role, tile: dict):
        super().__init__(timeout=None)
        self.team = team
        self.tile = tile

                
    @discord.ui.button(label="Approve", style=discord.ButtonStyle.success)
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        #Check if user is authorized
        if interaction.user.id not in await get_approved_users():
            return await interaction.response.send_message("You are not authorized to approve tiles.", ephemeral=True)
        
        await interaction.response.send_message("Tile approved.", ephemeral=True, delete_after=5)
        
        #update buttons
        self.remove_item(self.deny)
        button.disabled = True
        button.label = f"Approved by {interaction.user.display_name}"
        await interaction.message.edit(view=self)
        
        #cleanup
        try:
            await update_db({"_id" : self.team.id}, {"$push": {"approved_tiles": self.tile}})
        except Exception as e:
            logger.error(e)
        #send message to original channel
        resp_channel = discord.utils.get(interaction.guild.channels, id=self.tile["original_channel"])
        await resp_channel.send(f"{self.team.mention} Bingo tile approved by {interaction.user.mention}\n{interaction.message.jump_url}")
    
    @discord.ui.button(label="Deny", style=discord.ButtonStyle.danger)
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        #Check if user is authorized
        if interaction.user.id not in await get_approved_users():
            return await interaction.response.send_message("You are not authorized to deny tiles.", ephemeral=True)
        try:
            await interaction.response.send_modal(BingoModal(self.team, self.tile))
        except Exception as e:
            logger.error(e)
        #update buttons
        self.remove_item(self.approve)
        button.disabled = True
        button.label = f"Denied by {interaction.user.display_name}"
        await interaction.message.edit(view=self)
        
        

async def get_team_from_user_roles(user: discord.Member) -> discord.Role:
    for role in user.roles:
        if role in teams:
            logger.debug(role.__repr__())
            return role
    return None

async def parse_completed_tiles(tile_doc: dict) -> discord.Embed:
    
    embed = discord.Embed(
        title="Completed Bingo Tiles",
        color=discord.Color.random()
    )
    
    for team in tile_doc:
        logger.debug(team["approved_tiles"])
        if not team["approved_tiles"]:
            continue
        team_role: discord.Role = discord.utils.get(teams, id=team["_id"])
        embed.add_field(
            name=str(team_role.name + f"{len(team["approved_tiles"])} Tiles Completed"),
            value="\n".join([tile["tile"] for tile in team["approved_tiles"]]),
            inline=False
        )
    logger.debug(embed.__repr__())
    return embed

async def parse_denied_tiles(tile_doc: dict) -> discord.Embed:
    
    embed = discord.Embed(
        title="Denied Bingo Tiles",
        color=discord.Color.random()
    )
    for team in tile_doc:
        logger.debug(team["denied_tiles"])
        if not team["denied_tiles"]:
            continue
        team_role: discord.Role = discord.utils.get(teams, id=team["_id"])
        embed.add_field(
            name=team_role.name,
            value="\n".join([f"{tile['tile']}\n```Reason: {tile['reason']}```" for tile in team["denied_tiles"]]),
            inline=False
        )
    logger.debug(embed.__repr__())
    return embed
    

async def tile_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    options = [app_commands.Choice(name=tile, value=tile) for tile in board if current.lower() in tile.lower()]
    return options[:20]
    
async def update_db(query: dict, data: dict):
    await mongo.update_document("bingo", query, data)


async def get_approved_users() -> list[int]:
    doc = await mongo.get_document("bingo", {"_id": ObjectId("67abf2a3578b2b5dc8ef80ea")})
    return doc["users"]

async def get_denied_tiles() -> dict:
    return await mongo.get_many("bingo", {"denied_tiles": {"$ne": {}, "$exists": True}})

async def get_completed_tiles() -> dict:
    return await mongo.get_many("bingo", {"approved_tiles": {"$ne": {}, "$exists": True}})


@group.command()
async def set_board(interaction: discord.Interaction, attachment: discord.Attachment):
    """
    Set the bingo board.
    """
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("You must be admin to run this command.", ephemeral=True)
    global board_image
    board_image = attachment.url
    await interaction.response.send_message("Board updated successfully.", ephemeral=True)
    
    
@group.command(name="board")
async def get_board(interaction: discord.Interaction, visible: bool = False):
    """
    Get the current bingo board.
    """
    await interaction.response.send_message(board_image, ephemeral=not visible)

@group.command()
@app_commands.describe(extra_link="Discord Message link, Thread link or other discord resource. Linking off site is NOT allowed. ex. Gyazo, Imgur, etc.")
@app_commands.autocomplete(tile=tile_autocomplete)
async def submit(interaction: discord.Interaction, tile: str, attachment: discord.Attachment, extra_link: str = None):
    """
    Submit a bingo tile for approval.
    """
    if tile not in board:
        return await interaction.response.send_message(f"{tile} is not a valid bingo tile, make sure to select from autocomplete's list.", ephemeral=True)
    
    await interaction.response.send_message(f"**Tile:**\n ```{tile}```\n\n*Submitted for approval.*", ephemeral=False)
    try:
        team = await get_team_from_user_roles(interaction.user)
        new_tile: dict = {
            "tile": tile, 
            "attachments": [attachment.url], 
            "original_channel": interaction.channel.id, 
            "reason": None, 
            "submitter": interaction.user.id,
            "timestamp": datetime.now(tz=UTC),
            "extra": extra_link
            }
        embed = discord.Embed(
            title=tile.removesuffix(tile[-5:]),
            description=f"Submitted by {interaction.user.mention} for {team.mention}",
            timestamp=datetime.now(tz=UTC),
            color=discord.Color.random()
            
        )
        embed.set_footer(text=str("Board Coords: " + tile[-5:]))
        embed.set_image(url=attachment.url)
        if extra_link:
            embed.add_field(name="Link to extra context", value=extra_link)
        view = BingoView(team=team, tile=new_tile)
        sub_channel = discord.utils.get(interaction.guild.channels, id=1335725797532766218)
        await sub_channel.send(embed=embed, view=view)
    except Exception as e:
        logger.error(e)
        await interaction.response.send_message("An error occurred while submitting the tile.", ephemeral=True)

    
@group.command()
async def denied(interaction: discord.Interaction):
    """
    Get all denied bingo tiles by Team. (Currently bugged)
    """
    embed = await parse_denied_tiles(await get_denied_tiles())
    await interaction.response.send_message(embed=embed, ephemeral=True)

    
@group.command()
async def completed(interaction: discord.Interaction):
    """
    Get all completed bingo tiles by Team. (Currently bugged)
    """
    embed = await parse_completed_tiles(await get_completed_tiles())
    await interaction.response.send_message(embed=embed, ephemeral=True)
    
    
@group.command()
async def wiseoldman(interaction: discord.Interaction):
    """
    Get a link to the current running competition.
    """
    await interaction.response.send_message("https://wiseoldman.net/competitions/77923")

    
@group.command()
async def help(interaction: discord.Interaction):
    """
    Get help with bingo commands.
    """
    embed = discord.Embed(
        title="Bingo Commands",
        color=discord.Color.random()
    )
    embed.add_field(
        name="/bingo submit [tile] [attachment] [extra_link (optional)]",
        value="Submit a bingo tile for approval, make sure to:\n - Select from the autocomplete list. Anything else will call an error.\n - Attach an image per the instructions in the rules. This can either be a file or copy pasted from clipboard. (links do not work)\n > If you are on windows, i recommend pressing win+shift+s to use the built in snipping tool. This will copy the image to your clipboard and you can paste it directly into discord. Full client screenshots are preferred.\n > A staff/legend member will review the tile and either approve or deny it.",
        inline=False
    )
    embed.add_field(
        name="/bingo board [visible]",
        value="Get the image of the current bingo board. [visible] is an optional parameter to show the board in chat for others.",
        inline=False
    )
    embed.add_field(
        name="/bingo denied",
        value="Get all denied bingo tiles by Team.",
        inline=False
    )
    embed.add_field(
        name="/bingo completed",
        value="Get all completed bingo tiles by Team.",
        inline=False
    )
    embed.add_field(
        name="/bingo wiseoldman",
        value="Get a link to the current running competition, filter using Preview As and select the skill/boss to show.",
        inline=False
    )
    await interaction.response.send_message(embed=embed)


async def setup(client: discord.Client, guild: discord.Guild):
    for role in guild.roles:
        if role.id in team_role_ids:
            teams.append(role)
    logger.debug(teams)
    
    client.tree.add_command(group, guild=guild)
    
    