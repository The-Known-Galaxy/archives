import argparse
from enum import Enum

from ..Utilities import Constants
from ..Utilities import Files
from ..Utilities.Terminal import Colour as c
from ..Utilities.Terminal import TerminalColorCode as CC


TOOL_EPILOG = "Created, developed and maintained by ShadowEngineer"
JocastaArgumentParser = argparse.ArgumentParser(
    prog=Constants.TOOL_NAME,
    add_help=True,
    exit_on_error=True,
    allow_abbrev=True,
    description="""
Processes and manages archive files, guaranteeing compliance with TKG-game systems.
Able to generate archives from a Studio-exported JSON format (created using the Plugin), format files, generate meta data, and validate all files.

Inteded for use by programmers of the TKG Development Team, and CI/CD actions in this repository.
Bugs should be reported to ShadowEngineer directly, via Issues on GitHub.

Yes, the name derives from the in-lore Chief Librarian, Jocasta Nu.""",
    epilog=TOOL_EPILOG,
    formatter_class=argparse.RawTextHelpFormatter,
)

# group of arguments for organisation
global_arguments = JocastaArgumentParser.add_argument_group(
    "Global",
    "Options that don't do anything specific since they modify universal program behaviour.",
)
generation_arguments = JocastaArgumentParser.add_argument_group(
    "Generation", "Options related to generation of archive files."
)
management_arguments = JocastaArgumentParser.add_argument_group(
    "Management",
    "Options related to management, validation and house-keeping of the archive files.",
)
analysis_arguments = JocastaArgumentParser.add_argument_group(
    "Analysis",
    "Options related to analysing the archives and studying their contents for interest or statistical purposes.",
)

# arguments
global_arguments.add_argument(
    "-V",
    "--version",
    action="store_true",
    dest="version",
    help="Displays %(prog)s version.",
)
global_arguments.add_argument(
    "-v",
    "--verbose",
    action="count",
    default=0,
    dest="verbosity",
    help="Adds more-informative intermediate outputs. Can be specified multiple times for more verbosity.",
)
global_arguments.add_argument(
    "-C",
    "--concise-output",
    action="store_true",
    dest="concise_output",
    help="""During some verbose outputs, overwrites the previous output lines instead of writing new ones, which reduces the overall line count of the total program output.
Sometimes helpful when it's hard to keep track of what's being done during frequently logged and highly verbose outputs.
It is advised not to change your terminal window size when this option is applied.""",
)

generation_arguments.add_argument(
    "-g",
    "--generate",
    action="store_true",
    dest="generate",
    help="Generates the archive directories from the existing JSON files.",
)
generation_arguments.add_argument(
    "-d",
    "--destructive",
    action="store_true",
    dest="destructive",
    help="If using the --generate option, if base folders already exists, it deletes them before starting any work. Does nothing on its own. Dangerous option to use.",
)
generation_arguments.add_argument(
    "-m",
    "--generate-meta",
    action="store_true",
    dest="meta",
    help="Generates a summative meta file, explaining the contents of the entire archives.",
)

management_arguments.add_argument(
    "-f",
    "--format",
    action="store_true",
    dest="format",
    help="Formats all the archive entries.",
)
management_arguments.add_argument(
    "-c",
    "--check",
    action="store_true",
    dest="check",
    help="Ignoring all other options, checks all the files, ensuring they meet the structuring, naming and content rules that the game expects the archives to be in.",
)

VALID_LIST_CHOICES = {
    "categories": "categories",
    "entries": "entries",
}
analysis_arguments.add_argument(
    "-l",
    "--list",
    action="store",
    dest="list",
    choices=VALID_LIST_CHOICES.values(),
    help="Lists all of the existing contents for the given list type.",
)

# sub-commands
sub_command_parser = JocastaArgumentParser.add_subparsers(
    title="Subcommands",
    description="Sub-commands for accomplishing special archive-manipulation tasks automatically.",
    dest="subcommand",
    required=False,
)


class Subcommand(Enum):
    CREATE_COMMAND_NAME = "create"
    UPDATE_COMMAND_NAME = "update"
    DELETE_COMMAND_NAME = "delete"


VALID_ARCHIVES = Files.FindArchiveFolders()
VALID_OBJECTS = ["category", "entry"]
VALID_OBJECTS_TEXT = Constants.HELP_TEXT_VALUE_DELIMITER.join(
    [c(CC.BLUE, obj) for obj in VALID_OBJECTS]
)
FORMATTED_ENTRY = c(CC.BLUE, "entry")

CREATE_DESCRIPTION = f"Creates a new {VALID_OBJECTS_TEXT}."
CreateCommandParser = sub_command_parser.add_parser(
    name=Subcommand.CREATE_COMMAND_NAME.value,
    prog=f"{Constants.TOOL_NAME} {Subcommand.CREATE_COMMAND_NAME.value}",
    description=CREATE_DESCRIPTION,
    help=CREATE_DESCRIPTION,
    epilog=TOOL_EPILOG,
    add_help=True,
    allow_abbrev=True,
    exit_on_error=True,
    formatter_class=argparse.RawTextHelpFormatter,
)
CreateCommandParser.add_argument(
    "archive",
    choices=VALID_ARCHIVES,
    help=f"The {c(CC.PINK, 'archive')} to add to.",
)
CreateCommandParser.add_argument("name", help=f"The name to give it.")
CreateCommandParser.add_argument(
    "-c",
    "--into-category",
    action="store",
    dest="category",
    type=str,
    help=f"The category to create into. If supplied, then an {FORMATTED_ENTRY} will be created into the category with the supplied name.",
    metavar="EXISTING_CATEGORY_NAME",
)
CreateCommandParser.add_argument(
    "-i",
    "--creation-index",
    action="store",
    dest="index",
    type=int,
    help=f"The index at which to create at.",
)

UPDATE_DESCRIPTION = f"Updates existing {VALID_OBJECTS_TEXT} meta data."
UpdateCommandParser = sub_command_parser.add_parser(
    name=Subcommand.UPDATE_COMMAND_NAME.value,
    prog=f"{Constants.TOOL_NAME} {Subcommand.UPDATE_COMMAND_NAME.value}",
    description=UPDATE_DESCRIPTION,
    help=UPDATE_DESCRIPTION,
    epilog=TOOL_EPILOG,
    add_help=True,
    allow_abbrev=True,
    exit_on_error=True,
    formatter_class=argparse.RawTextHelpFormatter,
)
UpdateCommandParser.add_argument(
    "archive",
    choices=VALID_ARCHIVES,
    help=f"The {c(CC.PINK, 'archive')} to modify something in.",
)
UpdateCommandParser.add_argument(
    "name", help=f"The name of the {VALID_OBJECTS_TEXT} to modify."
)
UpdateCommandParser.add_argument(
    "-c",
    "--inside-category",
    action="store",
    dest="category",
    type=str,
    help=f"The category to modify inside. If supplied, then the {FORMATTED_ENTRY} with the given name will be modified instead.",
    metavar="EXISTING_CATEGORY_NAME",
)
UpdateCommandParser.add_argument(
    "-i",
    "--new-index",
    action="store",
    dest="index",
    type=int,
    help=f"A new index for the {VALID_OBJECTS_TEXT}. Must be a positive whole number.",
    metavar="NUMBER",
)
UpdateCommandParser.add_argument(
    "-n",
    "--new-name",
    action="store",
    dest="new_name",
    type=str,
    help=f"A new name for the {VALID_OBJECTS_TEXT}. Cannot be a duplicate of something already in the given archives.",
    metavar="NAME",
)
UpdateCommandParser.add_argument(
    "-a",
    "--new-author",
    action="store",
    dest="author",
    type=str,
    help=f"A new author for the {FORMATTED_ENTRY}. Should be the full and correctly spelled ROBLOX username of the entry's author.",
    metavar="USERNAME",
)
UpdateCommandParser.add_argument(
    "-y",
    "--new-release-year",
    action="store",
    dest="year",
    type=int,
    help=f"A new release year for the {FORMATTED_ENTRY}. Should be a positive whole number greater than or equal to 2020, since no entries could have possibly been made before then.",
    metavar="YEAR",
)

DELETE_DESCRIPTION = (
    f"{c(CC.RED, 'Deletes')} an existing {VALID_OBJECTS_TEXT} from the archives."
)
DeleteCommandParser = sub_command_parser.add_parser(
    name=Subcommand.DELETE_COMMAND_NAME.value,
    prog=f"{Constants.TOOL_NAME} {Subcommand.DELETE_COMMAND_NAME.value}",
    description=DELETE_DESCRIPTION,
    help=DELETE_DESCRIPTION,
    epilog=TOOL_EPILOG,
    add_help=True,
    allow_abbrev=True,
    exit_on_error=True,
    formatter_class=argparse.RawTextHelpFormatter,
)
DeleteCommandParser.add_argument(
    "archive",
    choices=VALID_ARCHIVES,
    help=f"The {c(CC.PINK, 'archive')} to delete a {VALID_OBJECTS_TEXT} in.",
)
DeleteCommandParser.add_argument(
    "name", help=f"The name of the {VALID_OBJECTS_TEXT} to {c(CC.RED, 'delete')}."
)
DeleteCommandParser.add_argument(
    "-c",
    "--inside-category",
    action="store",
    dest="category",
    type=str,
    help=f"The category to delete inside. If supplied, then the {FORMATTED_ENTRY} with the given name will be {c(CC.RED, 'deleted')} instead.",
    metavar="EXISTING_CATEGORY_NAME",
)


COMMAND_TO_PARSER = {
    Subcommand.CREATE_COMMAND_NAME.value: CreateCommandParser,
    Subcommand.UPDATE_COMMAND_NAME.value: UpdateCommandParser,
    Subcommand.DELETE_COMMAND_NAME.value: DeleteCommandParser,
}


def GetParserFromSubCommand(subcommand: str) -> argparse.ArgumentParser:
    """Returns the parser object for a given subcommand."""
    try:
        return COMMAND_TO_PARSER[subcommand]
    except KeyError:
        print(
            f'given subcommand "{subcommand}" does not have a parser associated with it'
        )
        raise


def NoArguments(args: argparse.Namespace) -> bool:
    """Checks whether any arguments have been given."""
    match args.subcommand:
        case Subcommand.CREATE_COMMAND_NAME.value:
            return not (args.archive or args.name or args.category or args.index)
        case Subcommand.UPDATE_COMMAND_NAME.value:
            return not (
                args.archive
                or args.name
                or args.category
                or args.index
                or args.new_name
                or args.author
                or args.year
            )
        case Subcommand.DELETE_COMMAND_NAME.value:
            return not (False)
        case _:
            return not (
                args.version
                or args.generate
                or args.destructive
                or args.meta
                or args.format
                or args.check
                or args.list
            )
