from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import typer
import yaml

if TYPE_CHECKING:
    from src.config.config_type_hint import (
        DefaultPaths,
        FileAndPathConfig,
        FileCategories,
    )


def open_config_with_specific_editor(file_path: Path) -> None:
    """
    Opens a file using a specific text editor for each operating system.

    :param file_path: The Path object of the file you want to open.
    """
    if sys.platform == "win32":
        # On Windows, `start` or the file itself opens it with the default app
        command = ["start", str(file_path)]
    elif sys.platform == "darwin":  # macOS
        command = ["open", "-a", "TextEdit", str(file_path)]
    elif sys.platform.startswith("linux"):
        command = ["xdg-open", str(file_path)]  # A standard way to open files
    else:
        typer.echo(f"Unsupported operating system: {sys.platform}")
        return

    try:
        # We use `shell=True` for `start` on Windows but avoid it for others
        is_shell = sys.platform == "win32"
        subprocess.run(command, check=True, shell=is_shell)
    except FileNotFoundError:
        typer.echo(f"Error: Could not find a suitable application to open {file_path}")
    except subprocess.CalledProcessError as e:
        typer.echo(f"An error occurred while opening the file: {e}")


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


def read_config(
    file_path: Path,
) -> FileCategories | DefaultPaths | FileAndPathConfig:
    """
    Reads a configuration file and returns its content as a dictionary.

    :param file_path: The Path object of the configuration file.
    :return: A dictionary containing the configuration data.
    """
    if not file_path.exists():
        typer.echo(
            typer.style(
                f"Configuration file {file_path} does not exist.", fg=typer.colors.RED
            )
        )
        raise typer.Exit(1)

    with open(file_path, encoding="utf-8") as file:
        try:
            config = yaml.safe_load(file)

            if file_path.name == "file_categories.yaml":
                optimize_config(config)

        except yaml.YAMLError as e:
            typer.echo(
                typer.style(f"Error reading YAML file: {e}", fg=typer.colors.RED)
            )
            raise typer.Exit(1)
        else:
            return config


def load_config(
    *, file_categories: bool = True, allowed_paths: bool = False
) -> FileCategories | DefaultPaths | FileAndPathConfig:
    """
    Load specific or combined configurations from YAML files.

    :raises typer.Exit: If no parameters are set.
    :returns: A dictionary representing the loaded configuration.
    """
    loaded_configs = {}
    if file_categories:
        loaded_configs["file_categories"] = read_config(
            Path("src/config/file_categories.yaml")
        )

    if allowed_paths:
        loaded_configs["allowed_paths"] = read_config(
            Path("src/config/allowed_path.yaml")
        )

    if not loaded_configs:
        typer.echo(
            typer.style(
                "Nothing to load, please set at least one of the parameters: "
                "file_categories or allowed_paths.",
                fg=typer.colors.RED,
            )
        )
        raise typer.Exit(1)

    # If only one type of config is requested, return it directly
    if len(loaded_configs) == 1:
        return next(iter(loaded_configs.values()))

    # If both are requested, return a combined dictionary
    return loaded_configs
