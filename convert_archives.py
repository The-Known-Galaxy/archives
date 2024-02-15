import argparse
import os
import shutil
import json
import toml
import re

# config variables
ARCHIVE_FILE_SUFFIX = "_archives"
ARCHIVE_FILE_TYPE_SUFFIXES = ["lua", "json"]
META_FILE_NAME = "meta.toml"

COLOUR_SEQUENCE = {"RESET": "\033[0m", "YELLOW": "\x1b[33;20m", "GREEN": "\x1b[32;20m"}
OUTPUT_LOG_TYPES = {
    "INFO": COLOUR_SEQUENCE["GREEN"] + "INFO" + COLOUR_SEQUENCE["RESET"],
    "WARNING": COLOUR_SEQUENCE["YELLOW"] + "WARN" + COLOUR_SEQUENCE["RESET"],
}

# CLI arguments for program configuration
argument_parser = argparse.ArgumentParser(
    prog="generator",
    add_help=True,
    exit_on_error=True,
    allow_abbrev=True,
    description="Processes generated archive files (either lua or json) into full archive directories, making them TKG-game ready.",
    epilog="Created, developed and maintained by ShadowEngineer",
)
argument_parser.add_argument(
    "-V",
    "--version",
    action="version",
    dest="version",
    version="%(prog)s 0.0.1",
    help="Displays tool version.",
)
argument_parser.add_argument(
    "-v",
    "--verbose",
    action="store_true",
    dest="verbose",
    help="Adds more-informative intermediate program outputs.",
)
argument_parser.add_argument(
    "-g",
    "--generate",
    action="store_true",
    dest="generate",
    help="Generates the archive directories from the given JSON files.",
)
argument_parser.add_argument(
    "-d",
    "--destructive",
    action="store_true",
    dest="destructive",
    help="During archive generation, if base folders already exists, it deletes them before starting any work. Does nothing on its own. Dangerous option to use.",
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
        if arguments.verbose:
            log_info("No archive files found. Exiting.")
        return

    # ensuring all found archive files are json files (converting anything that isn't into it)
    for i in range(0, len(archive_files)):
        file_name = archive_files[i]
        if not file_name.endswith(".json"):
            if arguments.verbose:
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
                if arguments.verbose:
                    log_warn(
                        f"Destructive option applied. Deleting {base_name} archives before re-generating."
                    )
                shutil.rmtree(base_name)

            # making base directory
            os.makedirs(base_name, exist_ok=True)

            if arguments.verbose:
                log_info(f"Creating category directories for {base_name} archives")

            for category_name, category_data in archive_data["categories"].items():
                processed_category_name = sanitise_file_name(category_name)
                if arguments.verbose:
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
                    if arguments.verbose:
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
                            f"{processed_article_name}.md",
                        ),
                        "w",
                    ) as entry_file:
                        entry_file.write(process_markdown(article_data["content"]))


if arguments.generate:
    generate_archive_directories()
