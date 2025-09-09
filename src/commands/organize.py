"""
Multi-directory file organization command with enhanced progress tracking.

This module provides a command-line interface for organizing multiple directories
simultaneously using the file categorization rules defined in the configuration.
It features advanced progress visualization with real-time file information.
"""

from __future__ import annotations

from typing import Annotated

import typer
from rich.console import Console
from src.core.organize_many_dirs import organize_many_dirs

app = typer.Typer()
console = Console()


@app.command()
def organize(
    paths: Annotated[
        str,
        typer.Argument(
            help="Comma-separated list of directory paths to organize. "
            "Example: '/path/to/folder1,/path/to/folder2'"
        ),
    ],
    include_hidden: Annotated[
        bool,
        typer.Option(
            "--include-hidden",
            help="Include hidden files (starting with '.') and system files in the organization process.",
        ),
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            help="Simulate organization process without making actual changes. "
            "Useful for previewing actions.",
        ),
    ] = False,
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Bypass security checks and allow organization of restricted directories.",
    ),
    skip_confirmation: Annotated[
        bool,
        typer.Option(
            "--yes",
            "-y",
            help="Skip all confirmation prompts and proceed automatically.",
        ),
    ] = False,
    recursive: bool = typer.Option(
        False,
        "--ricursive",
        "-r",
        help="Ricursive organizer direcory.",
    ),
    pattern: Annotated[
        str,
        typer.Option(
            "--pattern",
            help="Glob pattern to match files for organization. Examples: '*.jpg' for images, 'report*.*' for files starting with 'report'. Defaults to '*' (all files).",
        ),
    ] = "*",
) -> None:
    """
    Organize multiple directories simultaneously using configured categorization rules.

    Processes each specified directory, moving files into categorized subdirectories
    based on file extensions and size rules defined in the configuration.

    :param paths: Comma-separated list of directory paths to organize
    :param include_hidden: Whether to include hidden files in the organization process
    :param dry_run: Simulation mode without actual file operations
    :param force: Bypass security restrictions (use with caution)
    :param skip_confirmation: Automatically proceed without user prompts
    :raises typer.Exit: If no valid paths are provided or user cancels operation
    """
    organize_many_dirs(
        paths,
        include_hidden=include_hidden,
        dry_run=dry_run,
        force=force,
        skip_confirmation=skip_confirmation,
        recursive=recursive,
        pattern=pattern,
    )
