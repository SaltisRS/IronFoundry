import io
import discord

from discord import app_commands
from typing import Optional

from ..imagegen.models import CanvasLayout, OTWEntry, ColorKey
from ..imagegen.fonts import FontSet
from ..imagegen.icons import SkillIcon, BossIcon
from ..imagegen.layouts import SINGLE_LAYOUT, DOUBLE_LAYOUT, TRIPLE_LAYOUT
from ..imagegen.canvas import OTWCanvas


LAYOUT = CanvasLayout(
    constrain_left=91,
    constrain_right=1312,
    constrain_top=60,
    constrain_bottom=712,
    pad_x=60,
    pad_y=60,
)
LAYOUT.colors = (ColorKey.SOTW, (57, 117, 64))
LAYOUT.colors = (ColorKey.BOTW, (45, 72, 247))
LAYOUT.colors = (ColorKey.ROTW, (110, 7, 245))
LAYOUT.colors = (ColorKey.HIGHLIGHT_DATE, (128, 0, 32))

FONTS = FontSet(
    bold_path="assets/fonts/RuneScape-Bold-12.otf",
    quill_path="assets/fonts/RuneScape-Quill.otf",
)

ALL_SKILLS = [
    app_commands.Choice(name=icon.name.replace("_", " ").title(), value=icon.name)
    for icon in SkillIcon
]

ALL_BOSSES = [
    app_commands.Choice(name=icon.name.replace("_", " ").title(), value=icon.name)
    for icon in BossIcon
]

ALL_RAIDS = [
    app_commands.Choice(name=name, value=value)
    for name, value in [
        ("Chambers of Xeric", "COX"),
        ("Theatre of Blood", "TOB"),
        ("Tombs of Amascut", "TOA"),
    ]
]


def _filter_choices(
    choices: list[app_commands.Choice[str]], current: str
) -> list[app_commands.Choice[str]]:
    if not current:
        return choices[:25]
    lower = current.lower()
    return [c for c in choices if lower in c.name.lower()][:25]


async def skill_autocomplete(
    interaction: discord.Interaction, current: str
) -> list[app_commands.Choice[str]]:
    return _filter_choices(ALL_SKILLS, current)


async def boss_autocomplete(
    interaction: discord.Interaction, current: str
) -> list[app_commands.Choice[str]]:
    return _filter_choices(ALL_BOSSES, current)


async def raid_autocomplete(
    interaction: discord.Interaction, current: str
) -> list[app_commands.Choice[str]]:
    return _filter_choices(ALL_RAIDS, current)


def _resolve_entry(
    value: Optional[str],
    label: str,
    icon_enum: type[SkillIcon] | type[BossIcon],
    color_key: ColorKey,
) -> Optional[OTWEntry]:
    if not value:
        return None
    try:
        icon = icon_enum[value]
    except KeyError:
        return None
    return OTWEntry(
        label=label,
        name=value.replace("_", " ").title(),
        icon_path=icon.path,
        color_key=color_key,
    )


def register_otw_command(tree: app_commands.CommandTree, _guild):
    @tree.command(name="otw", description="Generate an Of The Week image", guild=_guild)
    @app_commands.describe(
        date="Date range (e.g. 'February 19th - 26th')",
        skill="Skill of the week",
        boss="Boss of the week",
        raid="Raid of the week",
    )
    @app_commands.autocomplete(
        skill=skill_autocomplete,
        boss=boss_autocomplete,
        raid=raid_autocomplete,
    )
    async def otw(
        interaction: discord.Interaction,
        date: str,
        skill: Optional[str] = None,
        boss: Optional[str] = None,
        raid: Optional[str] = None,
    ):
        await interaction.response.defer()

        entry_configs = [
            (skill, "SKILL OF THE WEEK", SkillIcon, ColorKey.SOTW),
            (boss, "BOSS OF THE WEEK", BossIcon, ColorKey.BOTW),
            (raid, "RAID OF THE WEEK", BossIcon, ColorKey.ROTW),
        ]

        entries: list[OTWEntry] = []
        for value, label, icon_enum, color_key in entry_configs:
            entry = _resolve_entry(value, label, icon_enum, color_key)
            if value and not entry:
                await interaction.followup.send(
                    f"Unknown value: {value}", ephemeral=True
                )
                return
            if entry:
                entries.append(entry)

        if not entries:
            await interaction.followup.send(
                "You must select at least one skill, boss, or raid.",
                ephemeral=True,
            )
            return

        preset = {
            1: SINGLE_LAYOUT,
            2: DOUBLE_LAYOUT,
            3: TRIPLE_LAYOUT,
        }.get(len(entries))

        if not preset:
            await interaction.followup.send(
                "Invalid number of entries.", ephemeral=True
            )
            return

        canvas = OTWCanvas(
            base_path="assets/backgrounds/otw_base.png",
            layout=LAYOUT,
            fonts=FONTS,
            preset=preset,
            date_text=date,
        )
        image = canvas.render(entries)

        buf = io.BytesIO()
        image.save(buf, format="PNG")
        buf.seek(0)

        await interaction.followup.send(file=discord.File(buf, filename="otw.png"))
