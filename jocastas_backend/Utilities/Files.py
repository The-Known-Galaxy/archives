import re
import os

TOP_LEVEL_FOLDER_IGNORE_LIST = ["jocastas_backend"]


def SanitiseFileName(name: str) -> str:
    """Sanitises and converts a given file name to a file system-friendly form."""
    return re.sub(
        "\_*$", "", re.sub("_{2,}", "_", re.sub("\W", "_", name.casefold().strip()))
    )


def FindInvalidCharacters(entry_or_category_name: str) -> list[str]:
    """
    Finds all the incorrect characters of a given entry/category name.
    Finds any characters that are NOT word characters, a space, a tab, a ', a ", a dash, any of the 3 forms of brackets, any punctuation, or the ampersand.
    """
    return re.findall(
        "[^\w\ '\"\-\(\)\[\]\{\}\<\>\/\.\:\;\&\,\!\?]", entry_or_category_name
    )


def ProcessMarkdown(original_markdown_content: str) -> str:
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


def FindMarkdownFile(path: str) -> None | str:
    """Finds a markdown file in the directory at the given path."""
    if not os.path.isdir(path):
        return None

    for file_name in os.listdir(path):
        if file_name.endswith(".md"):
            return os.path.join(path, file_name)


def FindArchiveFolders() -> list[str]:
    """Returns a list of all the archive folders."""
    archive_base_folders = []
    for file_name in os.listdir(os.getcwd()):
        # ignoring hidden directories
        if (
            os.path.isdir(file_name)
            and not file_name.startswith(".")
            and file_name not in TOP_LEVEL_FOLDER_IGNORE_LIST
        ):
            archive_base_folders.append(file_name)
    return archive_base_folders


def OnlyDirectories(path_prefix: str) -> list[str]:
    """Prunes the list of directory children, leaving only the directories in the list."""
    directory_list = os.listdir(path_prefix)
    files_to_remove = []
    for file in os.listdir(path_prefix):
        if not os.path.isdir(os.path.join(path_prefix, file)):
            files_to_remove.append(file)

    for file in files_to_remove:
        directory_list.remove(file)

    return directory_list
