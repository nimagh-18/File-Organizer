from __future__ import annotations

import json
import platform
from pathlib import Path

import typer


def add_allowed_path_to_config(
    new_path: str, config_path: Path = Path("config.json")
) -> None:
    """
    Adds a new path to the list of allowed paths in the config file
    for the current operating system.

    :param new_path: The path string to be added (e.g., "/mnt/data").
    :param config_path: The path to the config.json file.
    """
    try:
        # Load the config file
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)
    except FileNotFoundError:
        typer.echo(
            typer.style(
                f"Error: Config file not found at {config_path}.", fg=typer.colors.RED
            )
        )
        return

    # Map platform name to config keys
    system = platform.system().lower()

    if system not in {"windows", "darwin", "linux"}:
        typer.echo(typer.style("Unsupported os!!!", fg=typer.colors.RED))
        raise typer.Exit(1)

    # Get the allowed paths for the current OS
    allowed_paths = config_data.get("allowed_paths", {})
    os_paths: list[str] | None = allowed_paths.get(system, None)

    if os_paths is None:
        # If the key doesn't exist, create it as an empty list
        os_paths = []
        allowed_paths[system] = os_paths

    # Check if the path already exists to avoid duplicates
    if new_path not in os_paths:
        os_paths.append(new_path)
        typer.echo(
            typer.style(
                f"✅ Path '{new_path}' added successfully for '{system}'.",
                fg=typer.colors.GREEN,
            )
        )
    else:
        typer.echo(
            typer.style(
                f"⚠️ Path '{new_path}' already exists for '{system}'. No changes made.",
                fg=typer.colors.YELLOW,
            )
        )
        return

    # Write the modified data back to the config file
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=4, ensure_ascii=False)
