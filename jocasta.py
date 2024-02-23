import os
import shutil
import json
import toml
import mdformat
import time
import math

import jocastas_backend as Backend
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
arguments = Backend.Arguments.JocastaArgumentParser.parse_args()
Log = Backend.Logger.Logger(arguments)


def get_index_key(entry_data) -> int:
    """Key function for use in sorting dictionaries of categories or entries."""
    return entry_data["index"]


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


def generate_archive_directories():
    """
    Generates the entire archive structure and all necessary files from given archive describing files it finds (currently supporting lua or json).
    """
    start_time = time.perf_counter()

    # look for archive files (either lua or json)
    archive_files: list[str] = []
    for file_name in os.listdir(os.getcwd()):
        for type_suffix in ARCHIVE_FILE_TYPE_SUFFIXES:
            if file_name.endswith(f"{ARCHIVE_FILE_SUFFIX}.{type_suffix}"):
                archive_files.append(file_name)
                break

    if len(archive_files) == 0:
        if arguments.verbosity >= 1:
            Log.Info("No archive files found. Exiting.")
        return

    # ensuring all found archive files are json files (converting anything that isn't into it)
    processed_archive_files = {}
    for i in range(0, len(archive_files)):
        file_name = archive_files[i]
        processed_archive_files[file_name] = file_name

        if not file_name.endswith(".json"):
            if arguments.verbosity >= 1:
                Log.Info(f"Converting {c(CC.PINK, file_name)} to JSON.")
            file_root, file_type = os.path.splitext(file_name)
            new_name = f"{file_root}.json"

            # if the converted json file already exists, delete it.
            existing_file_path = os.path.join(os.getcwd(), new_name)
            if os.path.exists(existing_file_path):
                os.remove(existing_file_path)

            # renaming
            os.rename(file_name, new_name)
            processed_archive_files[file_name] = None
            processed_archive_files[new_name] = new_name

    # generating directories
    for file_name in processed_archive_files.values():
        with open(file_name) as json_file:
            archive_data = json.load(json_file)
            base_name = archive_data["name"]

            # cleaning existing base directory if one already exists and destruction option is supplied
            if arguments.destructive and os.path.isdir(base_name):
                if arguments.verbosity >= 1:
                    Log.Warn(
                        f"Destructive option applied. Deleting {c(CC.PINK, base_name)} archives before re-generating..."
                    )
                shutil.rmtree(base_name)

            # making base directory
            os.makedirs(base_name, exist_ok=True)

            if arguments.verbosity >= 1:
                Log.Info(
                    f"Creating category directories for {c(CC.PINK, base_name)} archives..."
                )

            categories = archive_data["categories"].items()
            total_categories = len(categories)
            categories_made = 0
            for category_name, category_data in categories:
                processed_category_name = Backend.Files.SanitiseFileName(category_name)
                if arguments.verbosity >= 2:
                    progress_bar = conditional_progress_bar_prefix(
                        arguments.concise_output and arguments.verbosity == 2,
                        categories_made / total_categories,
                    )
                    Log.Info(
                        f'\t{progress_bar}Creating category "{category_name}" <{processed_category_name}>',
                        replace_last=(
                            arguments.concise_output and arguments.verbosity == 2
                        ),
                    )

                # making category directory
                os.makedirs(
                    os.path.join(base_name, processed_category_name),
                    exist_ok=True,
                )

                # adding a meta file
                with open(
                    os.path.join(base_name, processed_category_name, META_FILE_NAME),
                    "w",
                ) as meta_file:
                    toml.dump(category_data["meta"], meta_file)

                # creating entry markdown files
                articles = category_data["articles"].items()
                total_articles = len(articles)
                articles_made = 0
                for article_name, article_data in articles:
                    processed_article_name = Backend.Files.SanitiseFileName(
                        article_name
                    )
                    if arguments.verbosity >= 3:
                        progress_bar = conditional_progress_bar_prefix(
                            arguments.concise_output, articles_made / total_articles
                        )

                        Log.Info(
                            f'\t\t{progress_bar}Creating article "{article_name}" ({processed_article_name})',
                            replace_last=arguments.concise_output,
                        )

                    # creating directory
                    os.makedirs(
                        os.path.join(
                            base_name, processed_category_name, processed_article_name
                        ),
                        exist_ok=True,
                    )

                    # adding meta file
                    with open(
                        os.path.join(
                            base_name,
                            processed_category_name,
                            processed_article_name,
                            META_FILE_NAME,
                        ),
                        "w",
                    ) as meta_file:
                        toml.dump(article_data["meta"], meta_file)

                    # creating entry and processing its content
                    with open(
                        os.path.join(
                            base_name,
                            processed_category_name,
                            processed_article_name,
                            ENTRY_FILE_NAME,
                        ),
                        "w",
                        encoding="utf-8",
                    ) as entry_file:
                        entry_file.write(
                            Backend.Files.ProcessMarkdown(article_data["content"])
                        )

                    articles_made += 1
                categories_made += 1

    if arguments.verbosity >= 1:
        end_time = time.perf_counter()
        Log.Success(f"All archives created. (took {end_time - start_time:.4f}) seconds")


def format_archives():
    """Formats all archives. Additionally, fixes any unidentified Unicode characters resulting from JSONEncoding from ROBLOX"""
    start_time = time.perf_counter()
    archive_folders = Backend.Files.FindArchiveFolders()

    if len(archive_folders) == 0 and arguments.verbosity >= 1:
        Log.Warn("No archive folders to format.")
        return

    # then iterate through all folders, categories and entry folders, to find the entry markdowns
    for archive_index, folder in enumerate(archive_folders):
        if arguments.verbosity >= 1:
            Log.Info(
                f"Formatting {c(CC.PINK, folder)} [{archive_index + 1}/{len(archive_folders)}] archives..."
            )

        archives_folder_path = os.path.join(os.getcwd(), folder)
        categories = Backend.Files.OnlyDirectories(archives_folder_path)
        total_categories = len(categories)
        for category_index, category in enumerate(categories):
            if arguments.verbosity >= 2:
                progress_bar = conditional_progress_bar_prefix(
                    arguments.concise_output and arguments.verbosity == 2,
                    (category_index + 1) / total_categories,
                )

                Log.Info(
                    f"\t{progress_bar}Formatting category [{category_index + 1}/{total_categories}]<{category}>",
                    replace_last=(
                        arguments.concise_output and arguments.verbosity == 2
                    ),
                )

            category_folder_path = os.path.join(folder, category)

            entries = Backend.Files.OnlyDirectories(category_folder_path)
            total_entries = len(entries)
            for entry_index, entry in enumerate(entries):
                entry_folder_path = os.path.join(category_folder_path, entry)
                entry_markdown_file_path = Backend.Files.FindMarkdownFile(
                    entry_folder_path
                )

                if entry_markdown_file_path is not None:
                    if arguments.verbosity >= 3:
                        progress_bar = conditional_progress_bar_prefix(
                            arguments.concise_output, (entry_index + 1) / total_entries
                        )

                        Log.Info(
                            f"\t\t{progress_bar}Formatting category <{category}> entry [{entry_index + 1}/{total_entries}]<{entry}>",
                            replace_last=arguments.concise_output,
                        )

                    # formatting file instead of text since it's quicker
                    mdformat.file(entry_markdown_file_path)

    if arguments.verbosity >= 1:
        end_time = time.perf_counter()
        Log.Success(
            f"All archives formatted! (took {(end_time - start_time):.4f} seconds)"
        )


def generate_meta():
    """Generates a single meta file for each set of archives, explaining their contents and using the existing meta files as sources of truth."""
    start_time = time.perf_counter()

    archive_folders = Backend.Files.FindArchiveFolders()

    if len(archive_folders) == 0 and arguments.verbosity >= 1:
        Log.Warn("No archive folders to generate meta files for.")
        return

    for archive in archive_folders:
        if arguments.verbosity >= 2:
            Log.Info(f"Generating meta files for {c(CC.PINK, archive)} archives...")

        # parsing all categories
        archive_path = os.path.join(os.getcwd(), archive)
        categories = Backend.Files.OnlyDirectories(archive_path)

        # creating main meta data object
        category_list = list()

        for category in categories:

            # collecting meta data from meta file
            category_path = os.path.join(archive_path, category)
            category_meta_file_path = os.path.join(category_path, META_FILE_NAME)

            # ensuring the category has a meta file
            if not os.path.exists(category_meta_file_path):
                if arguments.verbosity >= 1:
                    Log.Warn(
                        f"[{category_path}] does not have a {META_FILE_NAME}. Skipping category."
                    )
                continue

            # variables in preparation for processing meta file
            entries = Backend.Files.OnlyDirectories(category_path)
            entry_count = len(entries)
            entry_list = list()

            # parsing all entries
            for entry in entries:

                # collecting meta data from meta file
                entry_path = os.path.join(category_path, entry)
                entry_meta_file = os.path.join(entry_path, META_FILE_NAME)

                # ensuring the entry has a meta file
                if not os.path.exists(entry_meta_file):
                    if arguments.verbosity >= 1:
                        Log.Warn(
                            f"[{entry_path}] does not have a {META_FILE_NAME}. Skipping entry."
                        )
                    continue

                # reading and processing entry meta file
                with open(entry_meta_file, "r") as meta_file:
                    entry_meta_data = toml.load(meta_file)

                    # adding each bit of meta data into the list of entries, prior to adding them to the main meta object
                    entry_list.append(
                        dict(
                            markdown_path=f"{category}/{entry}/{ENTRY_FILE_NAME}",
                            **entry_meta_data,
                        )
                    )

            # sorting entries by index
            entry_list.sort(key=get_index_key)

            # reading the category meta file
            with open(category_meta_file_path, "r") as meta_file:
                # loading toml data into a python dictionary
                category_meta_data = toml.load(meta_file)

                # appending a new category dictionary
                category_list.append(
                    dict(
                        entries=entry_list,
                        total_entries=entry_count,
                        **category_meta_data,  # unpacking all category meta data into keys/values inside the new, expanded meta data
                    ),
                )

        # sorting categories
        category_list.sort(key=get_index_key)

        # compiling meta data
        archive_meta_data = dict(
            categories=category_list, category_count=len(categories)
        )

        # writing meta files (toml for readability and json for roblox processing)
        with open(os.path.join(archive, META_FILE_NAME), "w") as new_meta_toml_file:
            toml.dump(archive_meta_data, new_meta_toml_file)
        with open(
            os.path.join(archive, META_FILE_NAME_JSON), "w"
        ) as new_meta_json_file:
            json.dump(archive_meta_data, new_meta_json_file, indent=None)

        if arguments.verbosity >= 2:
            Log.Info(f"{archive.capitalize()} archive meta files created.")

    if arguments.verbosity >= 1:
        end_time = time.perf_counter()
        Log.Success(
            f"Meta file creation done! (took {(end_time - start_time):.4f} seconds)"
        )


def check_archives() -> tuple[int, str]:
    """Checks the validity of all archives files. Returns an exit code and a string explaining the result of the check."""
    start_time = time.perf_counter()

    archive_problems = 0
    category_problems = 0
    entry_problems = 0

    archive_folders = Backend.Files.FindArchiveFolders()
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
        categories = Backend.Files.OnlyDirectories(archive_path)
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
                                    Backend.Files.FindInvalidCharacters(field_value)
                                )
                                correct_entry_name = Backend.Files.SanitiseFileName(
                                    field_value
                                )

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
            entries = Backend.Files.OnlyDirectories(category_path)
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
                                        Backend.Files.FindInvalidCharacters(field_value)
                                    )
                                    correct_entry_name = Backend.Files.SanitiseFileName(
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
if Backend.Arguments.no_arguments(arguments) or arguments.help:
    Backend.Arguments.JocastaArgumentParser.print_help()
    exit(0)

if arguments.version:
    print(f"{Backend.Arguments.JocastaArgumentParser.prog} v{TOOL_VERSION}")
    exit(0)

if arguments.generate:
    generate_archive_directories()

if arguments.format:
    format_archives()

if arguments.meta:
    generate_meta()

if arguments.check:
    exit_code, result_string = check_archives()
    if exit_code == 0:
        Log.Success(result_string)
    else:
        Log.Error(result_string)
        exit(exit_code)
