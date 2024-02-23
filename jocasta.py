import os
import json
import toml
import mdformat
import time

from jocastas_backend.Functionality import Formatter
from jocastas_backend.Functionality import Generator
from jocastas_backend.Utilities import Arguments
from jocastas_backend.Utilities import Files
from jocastas_backend.Utilities import Logger
from jocastas_backend.Utilities.Constants import *
from jocastas_backend.Utilities.Terminal import TerminalColorCode as CC
from jocastas_backend.Utilities.Terminal import Colour as c

# all the various checks that are made in check mode
CHECK_WARNINGS = {
    "ARCHIVE_LEVEL": {
        "META_MISSING": f"{c(CC.BLUE, '%(archive_path)s')} is missing a {c(CC.RED, META_FILE_NAME)}",
        "META_MISSING_JSON": f"{c(CC.BLUE, '%(archive_path)s')} is missing a {c(CC.RED, META_FILE_NAME_JSON)}",
        # meta file incorrect (someone tampered with it)
    },
    "CATEGORY_LEVEL": {
        "META_MISSING": f"{c(CC.BLUE, '%(category_path)s')} is missing a {c(CC.RED, META_FILE_NAME)}",
        "META_MISSING_FIELD": f"{c(CC.BLUE, '%(category_path)s')}{os.path.sep}{c(CC.RED, META_FILE_NAME)} has no field named {c(CC.YELLOW, '%(field_name)s')}",
        "META_INTEGER_FIELD_NOT_POSITIVE_WHOLE": f"{c(CC.BLUE, '%(category_path)s')}{os.path.sep}{c(CC.RED, META_FILE_NAME)}{c(CC.YELLOW, ' [%(field_name)s]')} expects a positive whole number. Current value: {c(CC.RED, '%(field_value)s')}",
        "META_DUPLICATE_INDEX": f"{c(CC.BLUE, '%(category_path)s')}{os.path.sep}{c(CC.RED, META_FILE_NAME)}{c(CC.YELLOW, ' [%(field_name)s]')} has a duplicate index with the category {c(CC.RED, '%(other_category_name)s')}",
        "META_STRING_FIELD_NOT_STRING": f"{c(CC.BLUE, '%(category_path)s')}{os.path.sep}{c(CC.RED, META_FILE_NAME)}{c(CC.YELLOW, ' [%(field_name)s]')} expects a string. Current value: {c(CC.RED, '%(field_value)s')}",
        "META_STRING_FIELD_BLANK": f"{c(CC.BLUE, '%(category_path)s')}{os.path.sep}{c(CC.RED, META_FILE_NAME)}{c(CC.YELLOW, ' [%(field_name)s]')} is an empty string.",
        "META_STRING_FIELD_WITH_INVALID_CHARACTERS": f"{c(CC.BLUE, '%(category_path)s')}{os.path.sep}{c(CC.RED, META_FILE_NAME)}{c(CC.YELLOW, ' [%(field_name)s]')} has invalid characters. Offending characters: {c(CC.RED, '%(characters)s')}",
        "META_AND_FOLDER_NAME_MISMATCH": f"{c(CC.BLUE, '%(category_path)s')} folder name does not match category name. It should be \"{c(CC.YELLOW, '%(correct_category_name)s')}\" (from \"%(actual_category_name)s\"). Did you rename the category?",
        # unknown fields
    },
    "ENTRY_LEVEL": {
        "META_MISSING": f"{c(CC.BLUE, '%(entry_path)s')} is missing a {c(CC.RED, META_FILE_NAME)}",
        "ENTRY_MISSING": f"{c(CC.BLUE, '%(entry_path)s')} is missing a {c(CC.RED, META_FILE_NAME)}",
        "META_MISSING_FIELD": f"{c(CC.BLUE, '%(entry_path)s')}{os.path.sep}{c(CC.RED, META_FILE_NAME)} has no field named {c(CC.YELLOW, '%(field_name)s')}",
        "META_INTEGER_FIELD_NOT_POSITIVE_WHOLE": f"{c(CC.BLUE, '%(entry_path)s')}{os.path.sep}{c(CC.RED, META_FILE_NAME)}{c(CC.YELLOW, ' [%(field_name)s]')} expects a positive whole number. Current value: {c(CC.RED, '%(field_value)s')}",
        "META_DUPLICATE_INDEX": f"{c(CC.BLUE, '%(entry_path)s')}{os.path.sep}{c(CC.RED, META_FILE_NAME)}{c(CC.YELLOW, ' [%(field_name)s]')} has a duplicate index with the entry {c(CC.RED, '%(other_entry_name)s')}",
        "INVALID_RELEASE_YEAR": f"{c(CC.BLUE, '%(entry_path)s')}{os.path.sep}{c(CC.RED, META_FILE_NAME)}{c(CC.YELLOW, ' [%(field_name)s]')} expects a year on or after 2020. Given year: {c(CC.RED, '%(field_value)s')}",
        "META_STRING_FIELD_NOT_STRING": f"{c(CC.BLUE, '%(entry_path)s')}{os.path.sep}{c(CC.RED, META_FILE_NAME)}{c(CC.YELLOW, ' [%(field_name)s]')} expects a string. Current value: {c(CC.RED, '%(field_value)s')}",
        "META_STRING_FIELD_BLANK": f"{c(CC.BLUE, '%(entry_path)s')}{os.path.sep}{c(CC.RED, META_FILE_NAME)}{c(CC.YELLOW, ' [%(field_name)s]')} is an empty string.",
        "META_STRING_FIELD_WITH_INVALID_CHARACTERS": f"{c(CC.BLUE, '%(entry_path)s')}{os.path.sep}{c(CC.RED, META_FILE_NAME)}{c(CC.YELLOW, ' [%(field_name)s]')} has invalid characters. Offending characters: {c(CC.RED, '%(characters)s')}",
        "META_AND_FOLDER_NAME_MISMATCH": f"{c(CC.BLUE, '%(entry_path)s')} folder name does not match entry name. It should be \"{c(CC.YELLOW, '%(correct_entry_name)s')}\" (from \"%(actual_entry_name)s\"). Did you rename the entry?",
        # unknown fields
    },
}


EXPECTED_CATEGORY_META_FIELDS = {"name": str, "index": int}
EXPECTED_ENTRY_META_FIELDS = {
    "name": str,
    "index": int,
    "author": str,
    "release_year": int,
}

# CLI arguments for program configuration
arguments = Arguments.JocastaArgumentParser.parse_args()
Log = Logger.Logger(arguments)


def check_archives() -> tuple[int, str]:
    """Checks the validity of all archives files. Returns an exit code and a string explaining the result of the check."""
    start_time = time.perf_counter()

    archive_problems = 0
    category_problems = 0
    entry_problems = 0

    archive_folders = Files.FindArchiveFolders()
    if len(archive_folders) == 0 and arguments.verbosity >= 1:
        Log.Warn("No archive folders to check.")
        return

    # checking all archives
    for archive in archive_folders:
        archive_path = os.path.join(os.getcwd(), archive)

        # checking meta file existence
        if not os.path.exists(os.path.join(archive_path, META_FILE_NAME)):
            archive_problems += 1
            Log.Warn(
                CHECK_WARNINGS["ARCHIVE_LEVEL"]["META_MISSING"]
                % {"archive_path": archive_path}
            )
        if not os.path.exists(os.path.join(archive_path, META_FILE_NAME_JSON)):
            archive_problems += 1
            Log.Warn(
                CHECK_WARNINGS["ARCHIVE_LEVEL"]["META_MISSING_JSON"]
                % {"archive_path": archive_path}
            )

        # now checking all categories
        categories = Files.OnlyDirectories(archive_path)
        existing_category_indices = {}
        for category in categories:
            category_path = os.path.join(archive_path, category)

            # checking meta file existence
            category_meta_file_path = os.path.join(category_path, META_FILE_NAME)
            if not os.path.exists(category_meta_file_path):
                category_problems += 1
                Log.Warn(
                    CHECK_WARNINGS["CATEGORY_LEVEL"]["META_MISSING"]
                    % {"category_path": category_path}
                )
            else:
                with open(category_meta_file_path, "r") as meta_file:
                    meta_toml = toml.load(meta_file)
                    can_set_category_index = True
                    for field, value_type in EXPECTED_CATEGORY_META_FIELDS.items():
                        try:
                            field_value = meta_toml[field]
                            field_value_int = None
                            field_value_str = None

                            try:
                                field_value_int = int(field_value)
                            except ValueError:
                                field_value_int = None

                            try:
                                field_value_str = str(field_value)
                            except ValueError:
                                field_value_str = None

                            # for the edge-case that "123" can be converted to a number
                            if value_type == int and (
                                type(field_value) != int
                                or field_value_int == None
                                or field_value_int < 0
                            ):
                                # can't set the index post-verification since the index key doesn't exist or isn't an int
                                can_set_category_index = (
                                    False
                                    if field == "index"
                                    and can_set_category_index == True
                                    else can_set_category_index
                                )

                                category_problems += 1
                                Log.Warn(
                                    CHECK_WARNINGS["CATEGORY_LEVEL"][
                                        "META_INTEGER_FIELD_NOT_POSITIVE_WHOLE"
                                    ]
                                    % {
                                        "category_path": category_path,
                                        "field_name": field,
                                        "field_value": str(field_value),
                                    }
                                )
                            elif value_type == int and (
                                field == "index"
                                and existing_category_indices.get(field_value_int)
                                != None
                            ):
                                existing_entry_name = existing_category_indices.get(
                                    field_value_int
                                )
                                category_problems += 1
                                Log.Warn(
                                    CHECK_WARNINGS["CATEGORY_LEVEL"][
                                        "META_DUPLICATE_INDEX"
                                    ]
                                    % {
                                        "category_path": category_path,
                                        "field_name": field,
                                        "other_category_name": str(existing_entry_name),
                                    }
                                )
                            elif value_type == str and (
                                type(field_value) != str or field_value_str == None
                            ):
                                category_problems += 1
                                Log.Warn(
                                    CHECK_WARNINGS["CATEGORY_LEVEL"][
                                        "META_STRING_FIELD_NOT_STRING"
                                    ]
                                    % {
                                        "category_path": category_path,
                                        "field_name": field,
                                        "field_value": str(field_value),
                                    }
                                )
                            elif value_type == str:
                                non_matching_characters: list = (
                                    Files.FindInvalidCharacters(field_value)
                                )
                                correct_entry_name = Files.SanitiseFileName(field_value)

                                if len(non_matching_characters) > 0:
                                    category_problems += 1
                                    Log.Warn(
                                        CHECK_WARNINGS["CATEGORY_LEVEL"][
                                            "META_STRING_FIELD_WITH_INVALID_CHARACTERS"
                                        ]
                                        % {
                                            "category_path": category_path,
                                            "field_name": field,
                                            "characters": f"\"{''.join(non_matching_characters)}\"",
                                        }
                                    )
                                elif (
                                    field == "name"
                                    and os.path.basename(category_path)
                                    != correct_entry_name
                                ):
                                    category_problems += 1
                                    Log.Warn(
                                        CHECK_WARNINGS["CATEGORY_LEVEL"][
                                            "META_AND_FOLDER_NAME_MISMATCH"
                                        ]
                                        % {
                                            "category_path": category_path,
                                            "correct_category_name": correct_entry_name,
                                            "actual_category_name": field_value,
                                        }
                                    )
                                elif field_value_str.strip() == "":
                                    category_problems += 1
                                    Log.Warn(
                                        CHECK_WARNINGS["CATEGORY_LEVEL"][
                                            "META_STRING_FIELD_BLANK"
                                        ]
                                        % {
                                            "category_path": category_path,
                                            "field_name": field,
                                        }
                                    )
                        except KeyError:
                            category_problems += 1
                            Log.Warn(
                                CHECK_WARNINGS["CATEGORY_LEVEL"]["META_MISSING_FIELD"]
                                % {"category_path": category_path, "field_name": field}
                            )

                    if can_set_category_index:
                        existing_category_indices[meta_toml["index"]] = (
                            os.path.basename(category_path)
                        )
            entries = Files.OnlyDirectories(category_path)
            existing_entry_indices = {}
            for entry in entries:
                entry_path = os.path.join(category_path, entry)

                # checking meta file existence
                entry_meta_file_path = os.path.join(entry_path, META_FILE_NAME)
                if not os.path.exists(entry_meta_file_path):
                    entry_problems += 1
                    Log.Warn(
                        CHECK_WARNINGS["ENTRY_LEVEL"]["META_MISSING"]
                        % {"entry_path": entry_path}
                    )
                else:
                    with open(entry_meta_file_path, "r") as meta_file:
                        meta_toml = toml.load(meta_file)
                        can_set_entry_index = True
                        for field, value_type in EXPECTED_ENTRY_META_FIELDS.items():
                            try:
                                field_value = meta_toml[field]
                                field_value_int = None
                                field_value_str = None

                                try:
                                    field_value_int = int(field_value)
                                except ValueError:
                                    field_value_int = None

                                try:
                                    field_value_str = str(field_value)
                                except ValueError:
                                    field_value_str = None

                                # for the edge-case that "123" can be converted to a number
                                if value_type == int and (
                                    type(field_value) != int
                                    or field_value_int == None
                                    or field_value_int < 0
                                ):
                                    # can't set the index post-verification since the index key doesn't exist or isn't an int
                                    can_set_entry_index = (
                                        False
                                        if field == "index"
                                        and can_set_entry_index == True
                                        else can_set_entry_index
                                    )
                                    entry_problems += 1
                                    Log.Warn(
                                        CHECK_WARNINGS["ENTRY_LEVEL"][
                                            "META_INTEGER_FIELD_NOT_POSITIVE_WHOLE"
                                        ]
                                        % {
                                            "entry_path": entry_path,
                                            "field_name": field,
                                            "field_value": str(field_value),
                                        }
                                    )
                                elif value_type == int and (
                                    field == "index"
                                    and existing_entry_indices.get(field_value_int)
                                    != None
                                ):
                                    existing_entry_name = existing_entry_indices.get(
                                        field_value_int
                                    )
                                    entry_problems += 1
                                    Log.Warn(
                                        CHECK_WARNINGS["ENTRY_LEVEL"][
                                            "META_DUPLICATE_INDEX"
                                        ]
                                        % {
                                            "entry_path": entry_path,
                                            "field_name": field,
                                            "other_entry_name": str(
                                                existing_entry_name
                                            ),
                                        }
                                    )
                                elif (
                                    value_type == int
                                    and field == "release_year"
                                    and field_value_int < 2020
                                ):
                                    entry_problems += 1
                                    Log.Warn(
                                        CHECK_WARNINGS["ENTRY_LEVEL"][
                                            "INVALID_RELEASE_YEAR"
                                        ]
                                        % {
                                            "entry_path": entry_path,
                                            "field_name": field,
                                            "field_value": str(field_value),
                                        }
                                    )
                                elif value_type == str and (
                                    type(field_value) != str or field_value_str == None
                                ):
                                    entry_problems += 1
                                    Log.Warn(
                                        CHECK_WARNINGS["ENTRY_LEVEL"][
                                            "META_STRING_FIELD_NOT_STRING"
                                        ]
                                        % {
                                            "entry_path": entry_path,
                                            "field_name": field,
                                            "field_value": str(field_value),
                                        }
                                    )
                                elif value_type == str:
                                    non_matching_characters: list = (
                                        Files.FindInvalidCharacters(field_value)
                                    )
                                    correct_entry_name = Files.SanitiseFileName(
                                        field_value
                                    )

                                    if len(non_matching_characters) > 0:
                                        entry_problems += 1
                                        Log.Warn(
                                            CHECK_WARNINGS["ENTRY_LEVEL"][
                                                "META_STRING_FIELD_WITH_INVALID_CHARACTERS"
                                            ]
                                            % {
                                                "entry_path": entry_path,
                                                "field_name": field,
                                                "characters": f"\"{''.join(non_matching_characters)}\"",
                                            }
                                        )
                                    elif (
                                        field == "name"
                                        and os.path.basename(entry_path)
                                        != correct_entry_name
                                    ):
                                        entry_problems += 1
                                        Log.Warn(
                                            CHECK_WARNINGS["ENTRY_LEVEL"][
                                                "META_AND_FOLDER_NAME_MISMATCH"
                                            ]
                                            % {
                                                "entry_path": entry_path,
                                                "correct_entry_name": correct_entry_name,
                                                "actual_entry_name": field_value,
                                            }
                                        )
                                    elif field_value_str.strip() == "":
                                        entry_problems += 1
                                        Log.Warn(
                                            CHECK_WARNINGS["ENTRY_LEVEL"][
                                                "META_STRING_FIELD_BLANK"
                                            ]
                                            % {
                                                "entry_path": entry_path,
                                                "field_name": field,
                                            }
                                        )

                            except KeyError:
                                entry_problems += 1
                                Log.Warn(
                                    CHECK_WARNINGS["ENTRY_LEVEL"]["META_MISSING_FIELD"]
                                    % {
                                        "entry_path": entry_path,
                                        "field_name": field,
                                    }
                                )
                        if can_set_category_index:
                            existing_entry_indices[meta_toml["index"]] = (
                                os.path.basename(entry_path)
                            )
    end_time = time.perf_counter()
    total_problems = archive_problems + category_problems + entry_problems
    if total_problems > 0:
        return (
            1,
            f"{c(CC.RED, str(total_problems))} problem{'s' if total_problems > 1 else ''} identified. {c(CC.RED, str(archive_problems))} archive-wide, {c(CC.RED, str(category_problems))} category-specific, {c(CC.RED, str(entry_problems))} entry-specific (took {end_time - start_time:.4f} seconds)",
        )
    return (
        0,
        f"All correct. No problems. (took {end_time - start_time:.4f} seconds)",
    )


# main program execution
if Arguments.NoArguments(arguments) or arguments.help:
    Arguments.JocastaArgumentParser.print_help()
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
    exit_code, result_string = check_archives()
    if exit_code == 0:
        Log.Success(result_string)
    else:
        Log.Error(result_string)
        exit(exit_code)
