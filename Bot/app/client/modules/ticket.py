import discord
from discord import app_commands

ticket_archive = discord.Object(id=1007428258339504228)
ticket_category = discord.Object(id=945058998158258257)
tickets_role = 1348267270719148092

rankup_message = """## :star2: Welcome to Iron Foundry :star2:
We are a PVM focused clan with over 270 members. Whether you're a seasoned raider, just dipping your toes into PvM, or simply want to have people to socialize with during your never-ending grind, there’s a place for you here. 

__**Here are some important channels to be aware of**__
- #🤝-rank-structure
> Ranks are not about power or seniority, they're here to help us organize fair and exciting events. You’ll be assigned a rank based on your current gear and experience. Don't worry, you are not stuck at the rank you are assigned today, you can move up anytime as soon as you meet the next tier's requirements.
- #💬-speak-to-staff 
> This is where you will go to create a ticket if you need to speak to a staff member. Tickets can be for getting a rankup, reporting an issue, or for asking general questions.
- #🎟-event-info 
> This is where you will find information about current and upcoming clan events.
# Join us
If you are looking for a fun, friendly, and active OSRS community, you are in the right place! A member of our staff team will be with you shortly to guide you through your rank setup and get you invited to the in-game clan chat. While you wait, feel free to introduce yourself in #💬-general-chat or take a look around the channels!

*As a member of Iron Foundry, we expect everyone to be respectful to one another. Please avoid touchy subjects in game chat or discord. Discrimination towards another Foundry member for any reason will not be tolerated.*"""


class ReasonModal(discord.ui.Modal, title="Add Reason"):
    reason = discord.ui.TextInput(label="Reason for Closing Ticket", min_length=1, max_length=1000)
    def __init__(self):
        super().__init__(timeout=None, custom_id="reason_modal")
        
    async def on_submit(self, interaction: discord.Interaction):
        archive = discord.utils.get(interaction.guild.channels, id=ticket_archive.id)
        await interaction.response.send_message("Archiving Ticket...", ephemeral=True)
        await archive.send(f"**{interaction.channel.name}** Closed by {interaction.user.mention}\n\n**Reason:**\n ```{self.reason.value}```")
        await interaction.channel.delete()

class InnerTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='Close Ticket', style=discord.ButtonStyle.danger, custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        archive = discord.utils.get(interaction.guild.channels, id=ticket_archive.id)
        await interaction.response.send_message('Ticket Closed!', ephemeral=True)
        await archive.send(f'**{interaction.channel.name}** Closed by {interaction.user.mention} **Reason:** None')
        await interaction.channel.delete()
    
    @discord.ui.button(label="Close with Reason", style=discord.ButtonStyle.danger, custom_id="close_with_reason")
    async def close_with_reason(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ReasonModal())


class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='Other', style=discord.ButtonStyle.primary, custom_id="other_ticket")
    async def other_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="Ticket Created!", description="Your ticket has been created! Please wait for a staff member to assist you!", color=discord.Color.green())
        await interaction.response.send_message("Creating Ticket...", ephemeral=True, delete_after=5)
        guild = interaction.guild
        ticket_channel = await guild.create_text_channel(name=f'ticket-{interaction.user}', category=ticket_category)
        await ticket_channel.set_permissions(interaction.user, read_messages=True, send_messages=True)
        await ticket_channel.set_permissions(guild.get_role(tickets_role), read_messages=True, send_messages=True)
        await ticket_channel.send(f"{interaction.user.mention} {guild.get_role(tickets_role).mention}", embed=embed, view=InnerTicketView())
    
    
    @discord.ui.button(label='Rankup', style=discord.ButtonStyle.primary, custom_id="rankup_ticket")
    async def rankup_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="Ticket Created!", description="Your ticket has been created! Please wait for a staff member to assist you!", color=discord.Color.green())
        await interaction.response.send_message("Creating Ticket...", ephemeral=True, delete_after=5)
        guild = interaction.guild
        ticket_channel = await guild.create_text_channel(name=f'rankup-{interaction.user}', category=ticket_category)
        await ticket_channel.set_permissions(interaction.user, read_messages=True, send_messages=True)
        await ticket_channel.set_permissions(guild.get_role(tickets_role), read_messages=True, send_messages=True)
        await ticket_channel.send(f"{interaction.user.mention} {guild.get_role(tickets_role).mention}", embed=embed, view=InnerTicketView())
        await ticket_channel.send(rankup_message)

@app_commands.command()
async def send_ticket_view(interaction: discord.Interaction):
    embed = discord.Embed(title="Open a ticket!", description="Click below to open a ticket!", color=discord.Color.blurple())
    view = TicketView()
    await interaction.response.send_message(embed=embed, view=view)
    
    
async def ticket_setup(client: discord.Client, guild: discord.Guild):
    client.tree.add_command(send_ticket_view, guild=guild)
    client.add_view(TicketView())
    client.add_view(InnerTicketView())