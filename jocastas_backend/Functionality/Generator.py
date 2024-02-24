import argparse
import time
import os
import json
import toml
import shutil

from ..Utilities.Constants import *
from ..Utilities import Logger
from ..Utilities import Files
from ..Utilities import Terminal
from ..Utilities.Terminal import TerminalColorCode as CC
from ..Utilities.Terminal import Colour as c


class ArchiveGenerator:
    """Handles all generation logic."""

    def __init__(self, arguments: argparse.Namespace):
        self.Arguments = arguments
        self.Log = Logger.Logger(arguments)

    def __get_index_key(self, entry_data) -> int:
        """Key function for use in sorting dictionaries of categories or entries."""
        return entry_data["index"]

    def GenerateAllArchivesFromSource(self):
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
            if self.Arguments.verbosity >= 1:
                self.Log.Info("No archive files found. Exiting.")
            return

        # ensuring all found archive files are json files (converting anything that isn't into it)
        processed_archive_files = {}
        for i in range(0, len(archive_files)):
            file_name = archive_files[i]
            processed_archive_files[file_name] = file_name

            if not file_name.endswith(".json"):
                if self.Arguments.verbosity >= 1:
                    self.Log.Info(f"Converting {c(CC.PINK, file_name)} to JSON.")
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
                if self.Arguments.destructive and os.path.isdir(base_name):
                    if self.Arguments.verbosity >= 1:
                        self.Log.Warn(
                            f"Destructive option applied. Deleting {c(CC.PINK, base_name.capitalize())} archives before re-generating..."
                        )
                    shutil.rmtree(base_name)

                # making base directory
                os.makedirs(base_name, exist_ok=True)

                if self.Arguments.verbosity >= 1:
                    self.Log.Info(
                        f"Creating category directories for {c(CC.PINK, base_name)} archives..."
                    )

                categories = archive_data["categories"].items()
                total_categories = len(categories)
                categories_made = 0
                for category_name, category_data in categories:
                    processed_category_name = Files.SanitiseFileName(category_name)
                    if self.Arguments.verbosity >= 2:
                        progress_bar = Terminal.CreateConditionalProgressBarPrefix(
                            self.Arguments.concise_output
                            and self.Arguments.verbosity == 2,
                            categories_made / total_categories,
                        )
                        self.Log.Info(
                            f'\t{progress_bar}Creating category "{category_name}" <{processed_category_name}>',
                            replace_last=(
                                self.Arguments.concise_output
                                and self.Arguments.verbosity == 2
                            ),
                        )

                    # making category directory
                    os.makedirs(
                        os.path.join(base_name, processed_category_name),
                        exist_ok=True,
                    )

                    # adding a meta file
                    with open(
                        os.path.join(
                            base_name, processed_category_name, META_FILE_NAME
                        ),
                        "w",
                    ) as meta_file:
                        toml.dump(category_data["meta"], meta_file)

                    # creating entry markdown files
                    articles = category_data["articles"].items()
                    total_articles = len(articles)
                    articles_made = 0
                    for article_name, article_data in articles:
                        processed_article_name = Files.SanitiseFileName(article_name)
                        if self.Arguments.verbosity >= 3:
                            progress_bar = Terminal.CreateConditionalProgressBarPrefix(
                                self.Arguments.concise_output,
                                articles_made / total_articles,
                            )

                            self.Log.Info(
                                f'\t\t{progress_bar}Creating article "{article_name}" ({processed_article_name})',
                                replace_last=self.Arguments.concise_output,
                            )

                        # creating directory
                        os.makedirs(
                            os.path.join(
                                base_name,
                                processed_category_name,
                                processed_article_name,
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
                                Files.ProcessMarkdown(article_data["content"])
                            )

                        articles_made += 1
                    categories_made += 1

        if self.Arguments.verbosity >= 1:
            end_time = time.perf_counter()
            self.Log.Success(
                f"All archives created. (took {end_time - start_time:.4f}) seconds"
            )

    def GenerateGlobalArchiveMetaFiles(self):
        """Generates a single meta file for each set of archives, explaining their contents and using the existing meta files as sources of truth."""
        start_time = time.perf_counter()

        archive_folders = Files.FindArchiveFolders()

        if len(archive_folders) == 0 and self.Arguments.verbosity >= 1:
            self.Log.Warn("No archive folders to generate meta files for.")
            return

        for archive in archive_folders:
            if self.Arguments.verbosity >= 2:
                self.Log.Info(
                    f"Generating meta files for {c(CC.PINK, archive)} archives..."
                )

            # parsing all categories
            archive_path = os.path.join(os.getcwd(), archive)
            categories = Files.OnlyDirectories(archive_path)

            # creating main meta data object
            category_list = list()

            for category in categories:

                # collecting meta data from meta file
                category_path = os.path.join(archive_path, category)
                category_meta_file_path = os.path.join(category_path, META_FILE_NAME)

                # ensuring the category has a meta file
                if not os.path.exists(category_meta_file_path):
                    if self.Arguments.verbosity >= 1:
                        self.Log.Warn(
                            f"[{category_path}] does not have a {META_FILE_NAME}. Skipping category."
                        )
                    continue

                # variables in preparation for processing meta file
                entries = Files.OnlyDirectories(category_path)
                entry_count = len(entries)
                entry_list = list()

                # parsing all entries
                for entry in entries:

                    # collecting meta data from meta file
                    entry_path = os.path.join(category_path, entry)
                    entry_meta_file = os.path.join(entry_path, META_FILE_NAME)

                    # ensuring the entry has a meta file
                    if not os.path.exists(entry_meta_file):
                        if self.Arguments.verbosity >= 1:
                            self.Log.Warn(
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
                entry_list.sort(key=self.__get_index_key)

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
            category_list.sort(key=self.__get_index_key)

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

            if self.Arguments.verbosity >= 2:
                self.Log.Info(f"{archive.capitalize()} archive meta files created.")

        if self.Arguments.verbosity >= 1:
            end_time = time.perf_counter()
            self.Log.Success(
                f"Meta file creation done! (took {(end_time - start_time):.4f} seconds)"
            )
