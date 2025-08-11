from __future__ import annotations

from typing import Annotated

import typer
from src.core.operations import add_allowed_path_to_config

app = typer.Typer()


@app.command()
def add_path(
    path: Annotated[
        str, typer.Argument(help="Path of the directory to add in allowed_paths")
    ],
) -> None:
    """
    Adds a specified directory path to the list of allowed directories
    in the configuration file for the current operating system.

    This command provides a secure way to grant the organizer tool
    permission to operate on a new directory without manual file editing.

    :param path: The absolute or relative path of the directory
                 to be added to the allowed list.
    :type path: str
    """
    add_allowed_path_to_config(path)
