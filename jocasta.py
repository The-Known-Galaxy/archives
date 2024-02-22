import argparse
import os
import shutil
import json
import toml
import re
import mdformat
import time

# config variables
ARCHIVE_FILE_SUFFIX = "_archives"
ARCHIVE_FILE_TYPE_SUFFIXES = ["lua", "json"]
META_FILE_NAME = "meta.toml"
META_FILE_NAME_JSON = "meta.json"
ENTRY_FILE_NAME = "entry.md"

COLOUR_SEQUENCE = {
    "RESET": "\033[0m",
    "GREY": "\x1b[30;20m",
    "RED": "\x1b[31;20m",
    "GREEN": "\x1b[32;20m",
    "YELLOW": "\x1b[33;20m",
    "BLUE": "\x1b[34;20m",
}
OUTPUT_LOG_TYPES = {
    "INFO": COLOUR_SEQUENCE["BLUE"] + "INFO" + COLOUR_SEQUENCE["RESET"],
    "WARNING": COLOUR_SEQUENCE["YELLOW"] + "WARN" + COLOUR_SEQUENCE["RESET"],
    "ERROR": COLOUR_SEQUENCE["RED"] + "ERROR" + COLOUR_SEQUENCE["RESET"],
}

# CLI arguments for program configuration
argument_parser = argparse.ArgumentParser(
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
global_arguments = argument_parser.add_argument_group(
    "Global",
    "Options that don't do anything specific, or modify all program behaviour, regardless of other options.",
)
generation_arguments = argument_parser.add_argument_group(
    "Generation", "Options related to generation of archive files."
)
management_arguments = argument_parser.add_argument_group(
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
    action="version",
    dest="version",
    version="%(prog)s 0.0.1",
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

arguments = argument_parser.parse_args()


def log_to_output(log_type: str, text: str):
    """Logs given text to the output, formatted with a type."""
    print(f"[{log_type}]: {text}")


def log_info(text: str):
    """Logs info."""
    log_to_output(OUTPUT_LOG_TYPES["INFO"], text)


def log_warn(text: str):
    """Logs warnings."""
    log_to_output(OUTPUT_LOG_TYPES["WARNING"], text)


def log_error(text: str):
    """Logs errors."""
    log_to_output(OUTPUT_LOG_TYPES["ERROR"], text)


def sanitise_file_name(name: str):
    """Sanitises and converts a given file name to a file system-friendly form."""
    return re.sub(
        "\_*$", "", re.sub("_{2,}", "_", re.sub("\W", "_", name.casefold().strip()))
    )


def process_markdown(original_markdown_content: str):
    """
    Processes the markdown outputted from the ROBLOX-side processing:
    1. making sure each sentence starts on a new line (with the 3 possible sentence ending operators)
    2. making sure every section heading is on a new line
    3. making sure there is no leading or trailing whitespace
    """
    return re.sub(
        "#\ ",
        "\n\n# ",
        re.sub(
            "\?\ ",
            "?\n",
            re.sub(
                "\!\ ",
                "!\n",
                re.sub("\.\ ", ".\n", original_markdown_content),
            ),
        ),
    ).strip()


def find_markdown_file(path: str):
    """Finds a markdown file in the directory at the given path."""
    if not os.path.isdir(path):
        return None

    for file_name in os.listdir(path):
        if file_name.endswith(".md"):
            return os.path.join(path, file_name)


def find_archive_folders() -> list[str]:
    """Returns a list of all the archive folders."""
    archive_base_folders = []
    for file_name in os.listdir(os.getcwd()):
        # ignoring hidden directories
        if os.path.isdir(file_name) and not file_name.startswith("."):
            archive_base_folders.append(file_name)
    return archive_base_folders


def get_index_key(entry_data) -> int:
    """Key function for use in sorting dictionaries of categories or entries."""
    return entry_data["index"]


def only_directories(path_prefix: str, directory_list: list):
    """Prunes the list of directory children, leaving only the directories in the list."""
    files_to_remove = []
    for file in directory_list:
        if not os.path.isdir(os.path.join(path_prefix, file)):
            files_to_remove.append(file)

    for file in files_to_remove:
        directory_list.remove(file)

    return directory_list


def generate_archive_directories():
    """
    Generates the entire archive structure and all necessary files from given archive describing files it finds (currently supporting lua or json).
    """

    # look for archive files (either lua or json)
    archive_files: list[str] = []
    for file_name in os.listdir(os.getcwd()):
        for type_suffix in ARCHIVE_FILE_TYPE_SUFFIXES:
            if file_name.endswith(f"{ARCHIVE_FILE_SUFFIX}.{type_suffix}"):
                archive_files.append(file_name)
                break

    if len(archive_files) == 0:
        if arguments.verbosity >= 1:
            log_info("No archive files found. Exiting.")
        return

    # ensuring all found archive files are json files (converting anything that isn't into it)
    for i in range(0, len(archive_files)):
        file_name = archive_files[i]
        if not file_name.endswith(".json"):
            if arguments.verbosity >= 1:
                log_info(f"Converting {file_name} to JSON.")
            file_root, file_type = os.path.splitext(file_name)
            new_name = f"{file_root}.json"
            os.rename(file_name, new_name)
            archive_files[i] = new_name

    # generating directories
    for file_name in archive_files:
        with open(file_name) as json_file:
            archive_data = json.load(json_file)
            base_name = archive_data["name"]

            # cleaning existing base directory if one already exists and destruction option is supplied
            if arguments.destructive and os.path.isdir(base_name):
                if arguments.verbosity >= 1:
                    log_warn(
                        f"Destructive option applied. Deleting {base_name} archives before re-generating..."
                    )
                shutil.rmtree(base_name)

            # making base directory
            os.makedirs(base_name, exist_ok=True)

            if arguments.verbosity >= 1:
                log_info(f"Creating category directories for {base_name} archives...")

            for category_name, category_data in archive_data["categories"].items():
                processed_category_name = sanitise_file_name(category_name)
                if arguments.verbosity >= 2:
                    log_info(
                        f"\tCreating category [{category_name}] ({processed_category_name})"
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
                for article_name, article_data in category_data["articles"].items():
                    processed_article_name = sanitise_file_name(article_name)
                    if arguments.verbosity >= 3:
                        log_info(
                            f"\t\tCreating article [{article_name}] ({processed_article_name})"
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
                        entry_file.write(process_markdown(article_data["content"]))


def format_archives():
    """Formats all archives. Additionally, fixes any unidentified Unicode characters resulting from JSONEncoding from ROBLOX"""
    start_time = time.perf_counter()
    archive_folders = find_archive_folders()

    if len(archive_folders) == 0 and arguments.verbosity >= 1:
        log_warn("No archive folders to format.")
        return

    # then iterate through all folders, categories and entry folders, to find the entry markdowns
    for archive_index, folder in enumerate(archive_folders):
        if arguments.verbosity >= 1:
            log_info(
                f"Formatting {folder} [{archive_index + 1}/{len(archive_folders)}] archives..."
            )

        archives_folder_path = os.path.join(os.getcwd(), folder)
        categories = only_directories(
            archives_folder_path, os.listdir(archives_folder_path)
        )
        total_categories = len(categories)
        for category_index, category in enumerate(categories):
            if arguments.verbosity >= 2:
                log_info(
                    f"\tFormatting category [{category_index + 1}/{total_categories}]<{category}>"
                )

            category_folder_path = os.path.join(folder, category)

            entries = only_directories(
                category_folder_path, os.listdir(category_folder_path)
            )
            total_entries = len(entries)
            for entry_index, entry in enumerate(entries):
                entry_folder_path = os.path.join(category_folder_path, entry)
                entry_markdown_file_path = find_markdown_file(entry_folder_path)

                # then format
                if entry_markdown_file_path is not None:
                    if arguments.verbosity >= 3:
                        log_info(
                            f"\t\tFormatting category <{category}> entry [{entry_index + 1}/{total_entries}]<{entry}>"
                        )
                    mdformat.file(entry_markdown_file_path)

    if arguments.verbosity >= 1:
        end_time = time.perf_counter()
        log_info(
            f"All archives formatted! (took {(end_time - start_time):.4f} seconds)"
        )


def generate_meta():
    """Generates a single meta file for each set of archives, explaining their contents and using the existing meta files as sources of truth."""
    start_time = time.perf_counter()

    archive_folders = find_archive_folders()

    if len(archive_folders) == 0 and arguments.verbosity >= 1:
        log_warn("No archive folders to generate meta files for.")
        return

    for archive in archive_folders:
        if arguments.verbosity >= 2:
            log_info(f"Generating meta files for {archive} archives...")

        # parsing all categories
        archive_path = os.path.join(os.getcwd(), archive)
        categories = os.listdir(archive)

        # creating main meta data object
        category_list = list()

        for category in categories:

            # collecting meta data from meta file
            category_path = os.path.join(archive_path, category)
            category_meta_file_path = os.path.join(category_path, META_FILE_NAME)

            # ensuring the category has a meta file
            if not os.path.exists(category_meta_file_path):
                if arguments.verbosity >= 1 and os.path.isdir(category_path):
                    log_warn(
                        f"[{category_path}] does not have a {META_FILE_NAME}. Skipping category."
                    )
                continue

            # variables in preparation for processing meta file
            entries = os.listdir(category_path)
            entries.remove(META_FILE_NAME)  # since meta file should be ignored
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
                        log_warn(
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
            log_info(f"{archive.capitalize()} archive meta files created.")

    if arguments.verbosity >= 1:
        end_time = time.perf_counter()
        log_info(
            f"Meta file creation done! (took {(end_time - start_time):.4f} seconds)"
        )


def check_archives() -> tuple[int, str]:
    """Checks the validity of all archives files. Returns an exit code and a string explaining the result of the check."""
    return 0, "All files valid."


# main program execution
if arguments.help:
    argument_parser.print_help()
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
        log_info(result_string)
    else:
        log_error(result_string)
        exit(exit_code)
