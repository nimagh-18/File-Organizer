from __future__ import annotations

from typing import TYPE_CHECKING

import typer
import yaml

from file_organizer.config.optimize_config import optimize_config

if TYPE_CHECKING:
    from pathlib import Path

    from file_organizer.config.config_type_hint import (
        DefaultPaths,
        FileAndPathConfig,
        FileCategories,
    )


def read_config(
    file_path: Path,
    /,
    *,
    optimization: bool = False,
) -> FileCategories | DefaultPaths | FileAndPathConfig:
    """
    Reads a configuration file and returns its content as a dictionary.

    :param file_path: The Path object of the configuration file.
    :param optimization: Whether to optimize the configuration by converting
                        lists of extensions to sets.
    :raises typer.Exit: If the file does not exist or cannot be read.
    :raises yaml.YAMLError: If there is an error parsing the YAML file.
    :return: A dictionary containing the configuration data.
    """
    print(file_path)
    if not file_path.exists():
        typer.echo(
            typer.style(
                f"Configuration file {file_path} does not exist.",
                fg=typer.colors.RED,
            )
        )
        raise typer.Exit(1)

    with open(file_path, encoding="utf-8") as file:
        try:
            config = yaml.safe_load(file)

            if file_path.name == "file_categories.yaml" and optimization:
                optimize_config(config)

        except yaml.YAMLError as e:
            typer.echo(
                typer.style(f"Error reading YAML file: {e}", fg=typer.colors.RED),
            )
            raise typer.Exit(1)
        else:
            return config
