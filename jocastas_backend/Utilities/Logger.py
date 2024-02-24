import shutil
import re
import argparse

from .Terminal import *
from .Constants import *


OUTPUT_LOG_TYPES = {
    "SUCCESS": Colour(TerminalColorCode.GREEN, "SUCCESS"),
    "INFO": Colour(TerminalColorCode.BLUE, "INFO"),
    "WARNING": Colour(TerminalColorCode.YELLOW, "WARN"),
    "ERROR": Colour(TerminalColorCode.RED, "ERROR"),
}


class Logger:
    """A logger object, which handles all logic to-do with logging information to the output."""

    def __init__(self, arguments):
        """Initialises a logger object. Takes in an `arguments` namespace containing parse arguments to Jocasta."""
        self.arguments: argparse.Namespace = arguments

    def __len_without_control_codes(self, input: str) -> tuple[int, int]:
        """
        Calculates the length of the string without control-code characters.
        Also returns the difference between the original and filtered lengths
        """
        original_length = len(input)
        filtered = input
        for control_code in TerminalColorCode:
            filtered = filtered.replace(control_code.value, "")
        new_length = len(filtered)
        return new_length, original_length - new_length

    def __log_to_output(self, log_type: str, text: str, replace_last: bool = False):
        """
        Logs given text to the output, formatted with a type.
        Handles specreplacing previous lines.
        Truncates instead of wraps if text is too long to fit onto the next screen.
        """

        # when a line ends with a carriage return, it puts the cursor back at the start of the current line
        # and the next print statement OVERWRITES the text that is there, which achieves the usual "replacing" feature some terminal programs have.
        # this is how things like "progress bars" in the terminal window are possible
        end_character = "\r" if replace_last else "\n"

        # replacing the tab explicitly with 4 spaces, because calculating string length later assumes \t is a single character, even if it maps to 2, 4 or 8 spaces in the final output
        filtered_text = re.sub("\t", " " * 4, text)

        # building the initial output tring
        final_text = f"[{log_type}]: {filtered_text}"

        # when concise output is turned on, some lines will be replaced on high verboisities.
        # truncating the end since we don't want things to wrap, to allow that to happen cleanly
        # -2 for terminal width since the final 2 characters of the string are the line terminator (\r or \n), and the null byte (\0)
        if self.arguments.concise_output:
            # during execution, if the terminal size changes, then it needs to be reflected here
            # apparently shutil has this function - no idea why though, but it works!
            terminal_width = shutil.get_terminal_size().columns

            final_text_length, length_difference = self.__len_without_control_codes(
                final_text
            )
            if final_text_length > terminal_width - 2:
                formatted_truncation_sequence = Colour(
                    TerminalColorCode.GREY, TRUNCATION_SEQUENCE
                )
                final_text = f"{final_text[: terminal_width - 2 + length_difference - len(TRUNCATION_SEQUENCE)]}{formatted_truncation_sequence}"
            # whitespace-padding the output to fit the terminal width
            else:
                padding = " " * (terminal_width - final_text_length)
                final_text = f"{final_text}{padding}"

        # outputting the processed text with the correct end character
        # flushing is turned on when replacement is necessary to get faster outputting frequency (at a loss to memory performance)
        # this is due to how printing to stdout works internally. Flushing empties the "write buffer", a separate file that outputs are put into before being bulk-written to the console
        print(final_text, end=end_character, flush=replace_last)

    def Success(self, text: str, replace_last: bool = False):
        """Logs successes."""
        self.__log_to_output(
            log_type=OUTPUT_LOG_TYPES["SUCCESS"], text=text, replace_last=replace_last
        )

    def Info(self, text: str, replace_last: bool = False):
        """Logs info."""
        self.__log_to_output(
            log_type=OUTPUT_LOG_TYPES["INFO"], text=text, replace_last=replace_last
        )

    def Warn(self, text: str, replace_last: bool = False):
        """Logs warnings."""
        self.__log_to_output(
            log_type=OUTPUT_LOG_TYPES["WARNING"], text=text, replace_last=replace_last
        )

    def Error(self, text: str, replace_last: bool = False):
        """Logs errors."""
        self.__log_to_output(
            log_type=OUTPUT_LOG_TYPES["ERROR"], text=text, replace_last=replace_last
        )
