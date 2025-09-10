from __future__ import annotations

import json
from pathlib import Path


def write_one_line(file_path: Path, line: str) -> None:
    """
    Writes a single line of text to a file in append mode.

    This is primarily used to add simple characters like '[' or ']' to
    the history log file.

    :param file_path: The path of the file to write to.
    :param line: The string to be written to the file.
    """
    with open(file_path, "a", encoding="utf-8") as jf:
        jf.write(line)


def write_entries(
    file_path: Path,
    batch_entries: list[dict[str, str]],
    first_entry: bool = False,
) -> None:
    """
    Appends a batch of JSON entries to a history log file.

    This function serializes a list of dictionaries into a JSON format
    and appends them to a file. It handles the formatting (adding commas)
    to ensure the file remains a valid JSON array. The list of entries
    is cleared after writing to free up memory.

    :param file_path: The path of the file to append the entries to.
    :param batch_entries: A list of dictionaries representing the actions
                          to be logged. This list is cleared after writing.
    :param first_entry: A flag to determine if this is the first entry in the JSON array,
                        to prevent adding a leading comma.
    """
    with open(file_path, "a", encoding="utf-8") as jf:
        for entry in batch_entries:
            if not first_entry:
                jf.write(",\n")
            jf.write(json.dumps(entry, ensure_ascii=False, indent=4))
            first_entry = False
        batch_entries.clear()
        jf.flush()
