import discord
from discord import app_commands

ticket_archive = discord.Object(id=1007428258339504228)
ticket_category = discord.Object(id=945058998158258257)
tickets_role = 1348267270719148092


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

    @discord.ui.button(label='Create Ticket', style=discord.ButtonStyle.primary, custom_id="create_ticket")
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="Ticket Created!", description="Your ticket has been created! Please wait for a staff member to assist you!", color=discord.Color.green())
        await interaction.response.send_message("Creating Ticket...", ephemeral=True, delete_after=5)
        guild = interaction.guild
        ticket_channel = await guild.create_text_channel(name=f'ticket-{interaction.user}', category=ticket_category)
        await ticket_channel.set_permissions(interaction.user, read_messages=True, send_messages=True)
        await ticket_channel.set_permissions(guild.get_role(tickets_role), read_messages=True, send_messages=True)
        await ticket_channel.send(f"{interaction.user.mention} {guild.get_role(tickets_role).mention}", embed=embed, view=InnerTicketView())

@app_commands.command()
async def send_ticket_view(interaction: discord.Interaction):
    embed = discord.Embed(title="Open a ticket!", description="Click the button below to open a ticket!", color=discord.Color.blurple())
    view = TicketView()
    await interaction.response.send_message(embed=embed, view=view)
    
    
async def ticket_setup(client: discord.Client, guild: discord.Guild):
    client.tree.add_command(send_ticket_view, guild=guild)
    client.add_view(TicketView)
    client.add_view(InnerTicketView)