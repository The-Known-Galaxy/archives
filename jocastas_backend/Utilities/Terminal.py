from enum import Enum

COLOUR_SEQUENCE = {
    "RESET": "\033[0m",
    "GREY": "\x1b[30;20m",
    "RED": "\x1b[31;20m",
    "GREEN": "\x1b[32;20m",
    "YELLOW": "\x1b[33;20m",
    "BLUE": "\x1b[34;20m",
    "PINK": "\x1b[35;20m",
}


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
