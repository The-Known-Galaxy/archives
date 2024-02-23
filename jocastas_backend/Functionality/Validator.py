import argparse
import time
import os
import toml
from enum import Enum

from ..Utilities.Constants import *
from ..Utilities import Logger
from ..Utilities import Files
from ..Utilities.Terminal import TerminalColorCode as CC
from ..Utilities.Terminal import Colour as c


EXPECTED_CATEGORY_META_FIELDS = {"name": str, "index": int}
EXPECTED_ENTRY_META_FIELDS = {
    "name": str,
    "index": int,
    "author": str,
    "release_year": int,
}


class VALIDATIONS(Enum):
    # structure validations
    META_MISSING = f"{c(CC.BLUE, '%(path)s')} is missing a {c(CC.RED, META_FILE_NAME)}"
    META_MISSING_JSON = (
        f"{c(CC.BLUE, '%(path)s')} is missing a {c(CC.RED, META_FILE_NAME_JSON)}"
    )
    ENTRY_MISSING = (
        f"{c(CC.BLUE, '%(path)s')} is missing a {c(CC.RED, ENTRY_FILE_NAME)}"
    )

    # content validations
    META_MISSING_FIELD = f"{c(CC.BLUE, '%(path)s')}{os.path.sep}{c(CC.RED, META_FILE_NAME)} has no field named {c(CC.YELLOW, '%(field_name)s')}"
    META_INTEGER_FIELD_NOT_POSITIVE_WHOLE = f"{c(CC.BLUE, '%(path)s')}{os.path.sep}{c(CC.RED, META_FILE_NAME)}{c(CC.YELLOW, ' [%(field_name)s]')} expects a positive whole number. Current value: {c(CC.RED, '%(field_value)s')}"
    META_DUPLICATE_INDEX = f"{c(CC.BLUE, '%(path)s')}{os.path.sep}{c(CC.RED, META_FILE_NAME)}{c(CC.YELLOW, ' [%(field_name)s]')} has a duplicate index with the entry {c(CC.RED, '%(other_file_name)s')}"
    INVALID_RELEASE_YEAR = f"{c(CC.BLUE, '%(path)s')}{os.path.sep}{c(CC.RED, META_FILE_NAME)}{c(CC.YELLOW, ' [%(field_name)s]')} expects a year on or after 2020. Given year: {c(CC.RED, '%(field_value)s')}"
    META_STRING_FIELD_NOT_STRING = f"{c(CC.BLUE, '%(path)s')}{os.path.sep}{c(CC.RED, META_FILE_NAME)}{c(CC.YELLOW, ' [%(field_name)s]')} expects a string. Current value: {c(CC.RED, '%(field_value)s')}"
    META_STRING_FIELD_BLANK = f"{c(CC.BLUE, '%(path)s')}{os.path.sep}{c(CC.RED, META_FILE_NAME)}{c(CC.YELLOW, ' [%(field_name)s]')} is an empty string."
    META_STRING_FIELD_WITH_INVALID_CHARACTERS = f"{c(CC.BLUE, '%(path)s')}{os.path.sep}{c(CC.RED, META_FILE_NAME)}{c(CC.YELLOW, ' [%(field_name)s]')} has invalid characters. Offending characters: {c(CC.RED, '%(characters)s')}"
    META_AND_FOLDER_NAME_MISMATCH = f"{c(CC.BLUE, '%(path)s')} folder name does not match entry name. It should be \"{c(CC.YELLOW, '%(correct_name)s')}\" (from \"%(actual_name)s\"). Did you rename the entry?"


class ArchiveValidator:
    """Handles validation of all archives."""

    def __init__(self, arguments: argparse.Namespace):
        self.Arguments = arguments
        self.Log = Logger.Logger(arguments)

    def __log(self, validation_type: VALIDATIONS, message_substitutions: dict):
        """Logs out a validation breach."""
        self.Log.Warn(validation_type.value % message_substitutions)

    def ValidateAllArchives(self) -> tuple[int, str]:
        """Checks the validity of all archives files. Returns an exit code and a string explaining the result of the check."""
        start_time = time.perf_counter()

        archive_problems = 0
        category_problems = 0
        entry_problems = 0

        archive_folders = Files.FindArchiveFolders()
        if len(archive_folders) == 0 and self.Arguments.verbosity >= 1:
            self.Log.Warn("No archive folders to check.")
            return

        # checking all archives
        for archive in archive_folders:
            archive_path = os.path.join(os.getcwd(), archive)

            # checking meta file existence
            if not os.path.exists(os.path.join(archive_path, META_FILE_NAME)):
                archive_problems += 1
                self.__log(VALIDATIONS.META_MISSING, {"path": archive_path})
            if not os.path.exists(os.path.join(archive_path, META_FILE_NAME_JSON)):
                archive_problems += 1
                self.__log(VALIDATIONS.META_MISSING_JSON, {"path": archive_path})

            # now checking all categories
            categories = Files.OnlyDirectories(archive_path)
            existing_category_indices = {}
            for category in categories:
                category_path = os.path.join(archive_path, category)

                # checking meta file existence
                category_meta_file_path = os.path.join(category_path, META_FILE_NAME)
                if not os.path.exists(category_meta_file_path):
                    category_problems += 1
                    self.__log(VALIDATIONS.META_MISSING, {"path": category_path})
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
                                    self.__log(
                                        VALIDATIONS.META_INTEGER_FIELD_NOT_POSITIVE_WHOLE,
                                        {
                                            "path": category_path,
                                            "field_name": field,
                                            "field_value": str(field_value),
                                        },
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
                                    self.__log(
                                        VALIDATIONS.META_DUPLICATE_INDEX,
                                        {
                                            "path": category_path,
                                            "field_name": field,
                                            "other_file_name": str(existing_entry_name),
                                        },
                                    )
                                elif value_type == str and (
                                    type(field_value) != str or field_value_str == None
                                ):
                                    category_problems += 1
                                    self.__log(
                                        VALIDATIONS.META_STRING_FIELD_NOT_STRING,
                                        {
                                            "path": category_path,
                                            "field_name": field,
                                            "field_value": str(field_value),
                                        },
                                    )
                                elif value_type == str:
                                    non_matching_characters: list = (
                                        Files.FindInvalidCharacters(field_value)
                                    )
                                    correct_entry_name = Files.SanitiseFileName(
                                        field_value
                                    )

                                    if len(non_matching_characters) > 0:
                                        category_problems += 1
                                        self.__log(
                                            VALIDATIONS.META_STRING_FIELD_WITH_INVALID_CHARACTERS,
                                            {
                                                "path": category_path,
                                                "field_name": field,
                                                "characters": f"\"{''.join(non_matching_characters)}\"",
                                            },
                                        )
                                    elif (
                                        field == "name"
                                        and os.path.basename(category_path)
                                        != correct_entry_name
                                    ):
                                        category_problems += 1
                                        self.Log.Warn(
                                            VALIDATIONS.META_AND_FOLDER_NAME_MISMATCH,
                                            {
                                                "path": category_path,
                                                "correct_name": correct_entry_name,
                                                "actual_name": field_value,
                                            },
                                        )
                                    elif field_value_str.strip() == "":
                                        category_problems += 1
                                        self.__log(
                                            VALIDATIONS.META_STRING_FIELD_BLANK,
                                            {
                                                "path": category_path,
                                                "field_name": field,
                                            },
                                        )
                            except KeyError:
                                category_problems += 1
                                self.__log(
                                    VALIDATIONS.META_MISSING_FIELD,
                                    {
                                        "path": category_path,
                                        "field_name": field,
                                    },
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
                        self.__log(VALIDATIONS.META_MISSING, {"path": entry_path})
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
                                        self.__log(
                                            VALIDATIONS.META_INTEGER_FIELD_NOT_POSITIVE_WHOLE,
                                            {
                                                "path": entry_path,
                                                "field_name": field,
                                                "field_value": str(field_value),
                                            },
                                        )
                                    elif value_type == int and (
                                        field == "index"
                                        and existing_entry_indices.get(field_value_int)
                                        != None
                                    ):
                                        existing_entry_name = (
                                            existing_entry_indices.get(field_value_int)
                                        )
                                        entry_problems += 1
                                        self.__log(
                                            VALIDATIONS.META_DUPLICATE_INDEX,
                                            {
                                                "path": entry_path,
                                                "field_name": field,
                                                "other_file_name": str(
                                                    existing_entry_name
                                                ),
                                            },
                                        )
                                    elif (
                                        value_type == int
                                        and field == "release_year"
                                        and field_value_int < 2020
                                    ):
                                        entry_problems += 1
                                        self.__log(
                                            VALIDATIONS.INVALID_RELEASE_YEAR,
                                            {
                                                "path": entry_path,
                                                "field_name": field,
                                                "field_value": str(field_value),
                                            },
                                        )
                                    elif value_type == str and (
                                        type(field_value) != str
                                        or field_value_str == None
                                    ):
                                        entry_problems += 1
                                        self.__log(
                                            VALIDATIONS.META_STRING_FIELD_NOT_STRING,
                                            {
                                                "path": entry_path,
                                                "field_name": field,
                                                "field_value": str(field_value),
                                            },
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
                                            self.__log(
                                                VALIDATIONS.META_STRING_FIELD_WITH_INVALID_CHARACTERS,
                                                {
                                                    "path": entry_path,
                                                    "field_name": field,
                                                    "characters": f"\"{''.join(non_matching_characters)}\"",
                                                },
                                            )
                                        elif (
                                            field == "name"
                                            and os.path.basename(entry_path)
                                            != correct_entry_name
                                        ):
                                            entry_problems += 1
                                            self.__log(
                                                VALIDATIONS.META_AND_FOLDER_NAME_MISMATCH,
                                                {
                                                    "path": entry_path,
                                                    "correct_name": correct_entry_name,
                                                    "actual_name": field_value,
                                                },
                                            )
                                        elif field_value_str.strip() == "":
                                            entry_problems += 1
                                            self.__log(
                                                VALIDATIONS.META_STRING_FIELD_BLANK,
                                                {
                                                    "path": entry_path,
                                                    "field_name": field,
                                                },
                                            )

                                except KeyError:
                                    entry_problems += 1
                                    self.__log(
                                        VALIDATIONS.META_MISSING_FIELD,
                                        {
                                            "path": entry_path,
                                            "field_name": field,
                                        },
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
