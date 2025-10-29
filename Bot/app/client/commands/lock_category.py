import discord
from discord import app_commands

locked_categories = {}


@app_commands.command()
@app_commands.default_permissions(adminsitrator=True)
async def lock_category(
    interaction: discord.Interaction, category: discord.CategoryChannel
):
    channel_order = {channel.id: channel.position for channel in category.channels}

    locked_categories[category.id] = channel_order

    await interaction.response.send_message(
        f"✅ Locked {len(channel_order)} channels in **{category.name}**",
        ephemeral=True,
    )
