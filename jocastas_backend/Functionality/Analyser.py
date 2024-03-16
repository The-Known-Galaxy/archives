import argparse
import os
import json

from ..Functionality import Generator
from ..Utilities import Logger
from ..Utilities import Files
from ..Utilities import Arguments
from ..Utilities.Constants import *
from ..Utilities.Terminal import TerminalColorCode as CC
from ..Utilities.Terminal import Colour as c


class ArchiveAnalyser:
    """Handles all analysis."""

    def __init__(self, arguments: argparse.Namespace):
        self.Arguments = arguments
        self.Log = Logger.Logger(arguments)

    def ListContents(self):
        """Lists all archive content."""
        if self.Arguments.verbosity >= 1:
            self.Log.Info(f"Logging all {self.Arguments.list}")

        # reading meta files for both archives.
        archives = Files.FindArchiveFolders()
        for archive in archives:

            # reading archive meta data first
            meta_data = None
            try:
                archive_meta_data_path = os.path.join(
                    os.getcwd(), archive, META_FILE_NAME_JSON
                )
                with open(archive_meta_data_path, "r") as meta_file:
                    meta_data = json.load(meta_file)
            except:
                self.Log.Warn(
                    f"The {c(CC.PINK, archive)} archives don't have a {META_FILE_NAME_JSON}"
                )
                continue

            # custom printing since this should be saved to a file
            print(f"{archive}:")
            if self.Arguments.list == Arguments.VALID_LIST_CHOICES["categories"]:
                category_list = []
                for category_data in meta_data["categories"]:
                    category_list.append(
                        {
                            "name": category_data["name"],
                            "index": category_data["index"],
                            "entry_count": category_data["total_entries"],
                        }
                    )

                category_list.sort(key=Generator.get_index_key)

                for category in category_list:
                    print(category["name"])
            elif self.Arguments.list == Arguments.VALID_LIST_CHOICES["entries"]:
                entry_list = []
                for category_data in meta_data["categories"]:
                    for entry_data in category_data["entries"]:
                        entry_list.append(
                            {
                                "name": entry_data["name"],
                                "index": entry_data["index"]
                                + 1000 * category_data["index"],
                            }
                        )

                entry_list.sort(key=Generator.get_index_key)

                for entry in entry_list:
                    print(entry["name"])
