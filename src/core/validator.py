from __future__ import annotations

import os
import sys
from pathlib import Path

import typer
from loguru import logger
from src.config.utils import load_config
from src.core.constants import SystemProtector




def validate_directory_access(path: Path, force: bool) -> bool:
    """Validate directory is safe and accessible."""

    # Load config and instantiate protector (this should be done once)
    config = load_config(file_categories=False, allowed_paths=True)
    protector = SystemProtector(config)

    # Check for force flag first
    if force:
        logger.warning(
            f"Bypassing security checks for path '{path}' due to --force flag."
        )
        return True

    if not path.exists():
        typer.echo(
            typer.style(
                f"Error: The path '{path}' does not exist.", fg=typer.colors.RED
            )
        )
        return False

    if not path.is_dir():
        typer.echo(
            typer.style(
                f"Error: The path '{path}' is not a directory.", fg=typer.colors.RED
            )
        )
        return False

    if not os.access(path, os.R_OK | os.W_OK):
        typer.echo(
            typer.style(
                f"Error: Insufficient permissions to read/write in '{path}'.",
                fg=typer.colors.RED,
            )
        )
        return False

    # Use the new is_allowed method
    if not protector.is_allowed(path):
        typer.echo(
            typer.style(
                f"Error: The path '{path}' is not an allowed directory. "
                "Use --force to override this check.",
                fg=typer.colors.RED,
            )
        )
        return False

    return True
