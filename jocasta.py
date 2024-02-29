from jocastas_backend.Functionality import Formatter
from jocastas_backend.Functionality import Generator
from jocastas_backend.Functionality import Validator
from jocastas_backend.Utilities import Arguments
from jocastas_backend.Utilities import Logger
from jocastas_backend.Utilities.Constants import *

parser = Arguments.JocastaArgumentParser
arguments = parser.parse_args()
if arguments.subcommand != None:
    parser = Arguments.GetParserFromSubCommand(arguments.subcommand)
Log = Logger.Logger(arguments)


def jocasta():
    """Main CLI executor for the Jocasta archive utility."""
    print(arguments)
    if Arguments.NoArguments(arguments):
        parser.print_help()
        exit(0)

    if arguments.version:
        print(f"{Arguments.JocastaArgumentParser.prog} v{TOOL_VERSION}")
        exit(0)

    archive_generator = Generator.ArchiveGenerator(arguments)
    archive_formatter = Formatter.ArchiveFormatter(arguments)
    if arguments.generate:
        archive_generator.GenerateAllArchivesFromSource()

    if arguments.format:
        archive_formatter.FormatAllArchiveEntries()

    if arguments.meta:
        archive_generator.GenerateGlobalArchiveMetaFiles()

    if arguments.check:
        archive_validator = Validator.ArchiveValidator(arguments)
        exit_code, result_string = archive_validator.ValidateAllArchives()
        if exit_code == 0:
            Log.Success(result_string)
        else:
            Log.Error(result_string)
            exit(exit_code)


if __name__ == "__main__":
    jocasta()
