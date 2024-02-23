import math
from enum import Enum

from ..Utilities.Constants import *


class TerminalColorCode(Enum):
    RESET = "\033[0m"
    GREY = "\x1b[30;20m"
    RED = "\x1b[31;20m"
    GREEN = "\x1b[32;20m"
    YELLOW = "\x1b[33;20m"
    BLUE = "\x1b[34;20m"
    PINK = "\x1b[35;20m"


def Colour(given_colour: TerminalColorCode, text: str) -> str:
    """
    Colours text the given text based on the colour given.
    """
    return f"{given_colour.value}{text}{TerminalColorCode.RESET.value}"


def create_ascii_progress_bar(progress: float = 0, length: int = 10) -> str:
    """
    Creates a progress bar out of ASCII art.
    Example: `[####  ]`
    """
    # clamping progress between 0 and 1
    progress = max(0, min(progress, 1))
    number_of_progress_characters = math.floor(progress * length)
    return f"[{PROGRESS_BAR_CHARACTER * number_of_progress_characters}{' ' * (length - number_of_progress_characters)}]"


def conditional_progress_bar_prefix(
    should: bool = True, progress: float = 0, length: int = 10
) -> str:
    """
    Creates a progress bar, based on a condition, meant for adding it as a prefix to text.
    """

    if should:
        return create_ascii_progress_bar(progress=progress, length=length) + " "
    else:
        return ""
