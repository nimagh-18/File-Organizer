import json
import os
import sys
from pathlib import Path

import typer


def open_config_with_specific_editor(file_path: Path) -> None:
    """
    Opens a file using a specific text editor for each operating system.

    :param file_path: The Path object of the file you want to open.
    """
    try:
        if sys.platform == "win32":
            # Windows: Uses the default simple Notepad editor
            os.system(f"notepad.exe {file_path}")
        elif sys.platform == "darwin":  # macOS
            # macOS: Uses the default GUI TextEdit application
            os.system(f"open -a TextEdit {file_path}")
            # Alternative: For a simple terminal editor, use nano
            # os.system(f"nano {file_path}")
        elif sys.platform.startswith("linux"):
            # Linux: Uses the simple and user-friendly nano editor
            os.system(f"nano {file_path}")
        else:
            print(f"Unsupported operating system: {sys.platform}")

    except FileNotFoundError:
        print(f"Error: The file at {file_path} was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")


def load_config(*, file_categories: bool = True, allowed_path: bool = False) -> dict[str, str]:
    """
    Load needs config for organize a directory from config.json.

    :raises typer.Exit: if config.json is not exists
    :return: organize config
    """
    if not Path("config.json").exists():
        message = typer.style("config.json file not exists!!!\n", fg=typer.colors.RED)
        typer.echo(message)

        raise typer.Exit(1)

    with open("config.json") as jf:
        config = json.load(jf)

        if file_categories:
            return config["file_categories"]
        if allowed_path:
            return config["allowed_paths"]
        elif allowed_path and file_categories:
            return config
        else:
            typer.echo(typer.style(
                "Invalid parameters for load_config function. "
                "Please specify either 'file_categories' or 'allowed_path' or both.",
                fg=typer.colors.RED,
            ))
            raise typer.Exit(1)
