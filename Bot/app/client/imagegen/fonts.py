from dataclasses import dataclass
from PIL import ImageFont
from pathlib import Path

BASE_DIR = Path(__file__).parent


@dataclass
class FontSet:
    bold_path: str
    quill_path: str
    big_size: int = 64
    medium_size: int = 56
    small_size: int = 64

    def __post_init__(self):
        bold = BASE_DIR / self.bold_path
        quill = BASE_DIR / self.quill_path
        self.big = ImageFont.truetype(str(bold), self.big_size)
        self.medium = ImageFont.truetype(str(bold), self.medium_size)
        self.small = ImageFont.truetype(str(quill), self.small_size)
