import argparse


JocastaArgumentParser = argparse.ArgumentParser(
    prog="jocasta",
    add_help=False,
    exit_on_error=True,
    allow_abbrev=True,
    description="""
Processes and manages archive files, guaranteeing compliance with TKG-game systems.
Able to generate archives from a Studio-exported JSON format (created using the Plugin), format files, generate meta data, and validate all files.

Inteded for use by programmers of the TKG Development Team, and CI/CD actions in this repository.
Bugs should be reported to ShadowEngineer directly, via Issues on GitHub.

Yes, the name derives from the in-lore Chief Librarian, Jocasta Nu.""",
    epilog="Created, developed and maintained by ShadowEngineer",
    formatter_class=argparse.RawTextHelpFormatter,
)

# group of arguments for organisation
global_arguments = JocastaArgumentParser.add_argument_group(
    "Global",
    "Options that don't do anything specific, or modify all program behaviour, regardless of other options.",
)
generation_arguments = JocastaArgumentParser.add_argument_group(
    "Generation", "Options related to generation of archive files."
)
management_arguments = JocastaArgumentParser.add_argument_group(
    "Management",
    "Options related to management, validation and house-keeping of the archive files.",
)

# arguments
global_arguments.add_argument(
    "-h",
    "--help",
    action="store_true",
    dest="help",
    help="Displays help message, and exits.",
)
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


def NoArguments(args: argparse.Namespace) -> bool:
    """Checks whether any arguments have been given."""
    return not (
        args.help
        or args.version
        # or args.verbosity != 0 ignoring verbosity since it doesn't do anything on its own
        or args.generate
        or args.destructive
        or args.meta
        or args.format
        or args.check
    )
