from models import CanvasLayout, OTWEntry, ColorKey
from fonts import FontSet
from icons import SkillIcon, BossIcon
from layouts import SINGLE_LAYOUT, DOUBLE_LAYOUT, TRIPLE_LAYOUT
from canvas import OTWCanvas

layout = CanvasLayout(
    constrain_left=91,
    constrain_right=1312,
    constrain_top=60,
    constrain_bottom=712,
    pad_x=60,
    pad_y=60,
)
layout.colors = (ColorKey.SOTW, (57, 117, 64))
layout.colors = (ColorKey.BOTW, (45, 72, 247))
layout.colors = (ColorKey.ROTW, (110, 7, 245))
layout.colors = (ColorKey.HIGHLIGHT_DATE, (128, 0, 32))

fonts = FontSet(
    bold_path="assets/fonts/RuneScape-Bold-12.otf",
    quill_path="assets/fonts/RuneScape-Quill.otf",
)

sotw = OTWEntry(
    label="SKILL OF THE WEEK",
    name="Smithing",
    icon_path=SkillIcon.SMITHING.path,
    color_key=ColorKey.SOTW,
)
botw = OTWEntry(
    label="BOSS OF THE WEEK",
    name="Vorkath",
    icon_path=BossIcon.VORKATH.path,
    color_key=ColorKey.BOTW,
)
rotw = OTWEntry(
    label="RAID OF THE WEEK",
    name="Chambers of Xeric",
    icon_path=BossIcon.COX.path,
    color_key=ColorKey.ROTW,
)

# --- Single entry ---
canvas = OTWCanvas(
    base_path="assets/backgrounds/otw_base.png",
    layout=layout,
    fonts=fonts,
    preset=SINGLE_LAYOUT,
    date_text="February 19th - 26th",
)
canvas.render([sotw]).show()

# --- Two entries ---
canvas = OTWCanvas(
    base_path="assets/backgrounds/otw_base.png",
    layout=layout,
    fonts=fonts,
    preset=DOUBLE_LAYOUT,
    date_text="February 19th - 26th",
)
canvas.render([sotw, rotw]).show()

# --- All three ---
canvas = OTWCanvas(
    base_path="assets/backgrounds/otw_base.png",
    layout=layout,
    fonts=fonts,
    preset=TRIPLE_LAYOUT,
    date_text="February 19th - 26th",
)
canvas.render([sotw, botw, rotw]).show()
