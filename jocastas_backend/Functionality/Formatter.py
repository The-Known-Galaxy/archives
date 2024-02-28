import argparse
import time
import os
import mdformat
import pathlib

from ..Utilities import Logger
from ..Utilities import Files
from ..Utilities import Terminal
from ..Utilities.Terminal import TerminalColorCode as CC
from ..Utilities.Terminal import Colour as c
from ..Utilities.Constants import *


class ArchiveFormatter:
    """Handles all formatting logic."""

    def __init__(self, arguments: argparse.Namespace):
        self.Arguments = arguments
        self.Log = Logger.Logger(arguments)

    def FormatAllArchiveEntries(self):
        """Formats all archives. Additionally, fixes any unidentified Unicode characters resulting from JSONEncoding from ROBLOX"""
        start_time = time.perf_counter()
        archive_folders = Files.FindArchiveFolders()

        if len(archive_folders) == 0 and self.Arguments.verbosity >= 1:
            self.Log.Warn("No archive folders to format.")
            return

        # then iterate through all folders, categories and entry folders, to find the entry markdowns
        for archive_index, folder in enumerate(archive_folders):
            if self.Arguments.verbosity >= 1:
                self.Log.Info(
                    f"Formatting {c(CC.PINK, folder.capitalize())} [{archive_index + 1}/{len(archive_folders)}] archives..."
                )

            archives_folder_path = os.path.join(os.getcwd(), folder)
            categories = Files.OnlyDirectories(archives_folder_path)
            total_categories = len(categories)
            for category_index, category in enumerate(categories):
                if self.Arguments.verbosity >= 2:
                    progress_bar = Terminal.CreateConditionalProgressBarPrefix(
                        self.Arguments.concise_output and self.Arguments.verbosity == 2,
                        (category_index + 1) / total_categories,
                    )

                    self.Log.Info(
                        f"\t{progress_bar}Formatting category [{category_index + 1}/{total_categories}]<{category}>",
                        replace_last=(
                            self.Arguments.concise_output
                            and self.Arguments.verbosity == 2
                        ),
                    )

                category_folder_path = os.path.join(folder, category)

                category_meta_file_path = os.path.join(
                    category_folder_path, META_FILE_NAME
                )
                Files.FormatMetaFile(category_meta_file_path, allow_non_exist=True)

                entries = Files.OnlyDirectories(category_folder_path)
                total_entries = len(entries)
                for entry_index, entry in enumerate(entries):
                    entry_folder_path = os.path.join(category_folder_path, entry)

                    meta_file_path = os.path.join(entry_folder_path, META_FILE_NAME)
                    Files.FormatMetaFile(meta_file_path, allow_non_exist=True)

                    entry_markdown_file_path = Files.FindMarkdownFile(entry_folder_path)
                    if entry_markdown_file_path is not None:
                        if self.Arguments.verbosity >= 3:
                            progress_bar = Terminal.CreateConditionalProgressBarPrefix(
                                self.Arguments.concise_output,
                                (entry_index + 1) / total_entries,
                            )

                            self.Log.Info(
                                f"\t\t{progress_bar}Formatting category <{category}> entry [{entry_index + 1}/{total_entries}]<{entry}>",
                                replace_last=self.Arguments.concise_output,
                            )

                        # formatting file instead of text since it's quicker
                        mdformat.file(entry_markdown_file_path)

        if self.Arguments.verbosity >= 1:
            end_time = time.perf_counter()
            self.Log.Success(
                f"All archives formatted! (took {(end_time - start_time):.4f} seconds)"
            )
