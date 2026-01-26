# coding: utf-8
from enum import Enum

from qfluentwidgets import FluentIconBase, getIconColor, Theme


class Icon(FluentIconBase, Enum):

    ANIMATION = "Animation"
    ANIMATIONCLIP = "AnimationClip"
    TEXTEDIT = "TextEdit"
    STANDING = "Standing"
    RUNNING = "Running"
    MID = "Mid"
    MIDLINE = "MidLine"
    MOBA = "Moba"
    CHARACTER = "Character"
    GRID = "Grid"
    MENU = "Menu"
    TEXT = "Text"
    PRICE = "Price"
    EMOJI_TAB_SYMBOLS = "EmojiTabSymbols"

    def path(self, theme=Theme.AUTO):
        return f":/gallery/images/icons/{self.value}_{getIconColor(theme)}.svg"
