from __future__ import annotations

from typing import TYPE_CHECKING

import typer

if TYPE_CHECKING:
    from file_organizer.config.config_type_hint import (
        FileCategories,
    )


def optimize_config(file_categories: FileCategories) -> None:
    """
    Optimize the file categories configuration by converting lists of extensions
    to sets for faster membership testing.

    :param config: The original file categories configuration.
    :return: An optimized configuration with sets for extensions.
    """
    # Iterate through each category and convert extensions to a set
    # This is to ensure faster membership testing later
    if not isinstance(file_categories, dict):
        typer.echo(
            typer.style(
                "Invalid configuration format. Expected a dictionary.",
                fg=typer.colors.RED,
            )
        )
        raise typer.Exit(1)

    # Iterate through each category in the config
    # and convert extensions to a set for faster lookups
    # This is useful for performance when checking file extensions later
    for category in file_categories["categories"]:
        extensions = category.get("extensions", [])
        category["extensions"] = set(extensions)
