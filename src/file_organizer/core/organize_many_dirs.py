"""
Multi-directory file organization command with enhanced progress tracking.

This module provides a command-line interface for organizing multiple directories
simultaneously using the file categorization rules defined in the configuration.
It features advanced progress visualization with real-time file information.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import typer
from rich.console import Console

from file_organizer.core.validator import load_config, validate_directory_access
from file_organizer.filesystem.beautiful_display_and_progress import (
    BeautifulDisplayAndProgress,
)
from file_organizer.filesystem.create_and_move import LocalFileOrganizer
from file_organizer.filesystem.dir_cleaner import remove_dirs

if TYPE_CHECKING:
    from file_organizer.config.config_type_hint import FileCategories

console = Console()


def organize_many_dirs(
    paths: str,
    *,
    include_hidden: bool,
    dry_run: bool,
    force: bool,
    skip_confirmation: bool,
    recursive: bool,
    pattern: str,
    iteration_depth: int,
) -> None:
    """
    Organize multiple directories simultaneously using configured categorization rules.

    This function processes a comma-separated list of directory paths, validates their
    accessibility, and organizes files into categorized subdirectories based on file
    extensions and size rules defined in the configuration. It supports dry-run mode,
    recursive traversal, glob pattern filtering, hidden file inclusion, and depth limiting.
    Progress is displayed with rich formatting, and empty directories are cleaned up after
    organization.

    :param paths: Comma-separated string of directory paths to organize (e.g., "/path1,/path2").
    :param include_hidden: If True, includes hidden files (starting with '.') in the organization.
    :param dry_run: If True, simulates the organization without making changes.
    :param force: If True, bypasses security checks for restricted directories.
    :param skip_confirmation: If True, skips user confirmation prompts.
    :param recursive: If True, organizes files in subdirectories recursively.
    :param pattern: Glob pattern to match files (e.g., "*.txt", "*.{jpg,png}"). Defaults to "*".
    :param iteration_depth: Maximum recursion depth for subdirectories (-1 for unlimited).
    :returns: None
    :raises typer.Exit: If no valid paths are provided, paths fail validation, or user cancels the operation.
    :example:

        Organize two directories with a depth limit of 2:

        .. code-block:: bash

            organizer organize /path/to/dir1,/path/to/dir2 --depth 2 --pattern "*.txt"
    """
    # Parse and clean input paths
    path_list: list[Path] = [Path(p.strip()) for p in paths.split(",") if p.strip()]

    if not path_list:
        console.print(
            "[red]Error: No valid paths provided. Please provide comma-separated directory paths.[/red]"
        )
        raise typer.Exit(1)

    # Validate each directory path
    valid_paths: list[Path] = []
    for path in path_list:
        if validate_directory_access(path, force):
            valid_paths.append(path)
        else:
            console.print(
                f"[yellow]Skipping invalid or restricted path: {path}[/yellow]"
            )

    if not valid_paths:
        console.print(
            "[red]Error: No valid directories to organize. All paths failed validation.[/red]"
        )
        raise typer.Exit(1)

    # Load configuration once for all directories
    file_categories: FileCategories = load_config(
        file_categories=True,
        optimization=True,
    )

    # Request user confirmation unless skipped
    if not dry_run and not skip_confirmation:
        path_summary = "\n".join(f"  • {p.resolve()}" for p in valid_paths)
        confirmation_message = (
            f"Are you sure you want to organize {len(valid_paths)} directories?\n"
            f"{path_summary}"
        )

        if not typer.confirm(typer.style(confirmation_message, fg=typer.colors.YELLOW)):
            console.print("[red]Operation cancelled.[/red]")
            raise typer.Exit()

    # Process each directory
    total_moved = 0
    total_created_dirs = 0
    total_errors = 0

    new_history_file = True
    last_dir = False

    for i, directory_path in enumerate(valid_paths, 1):
        if i > 1:
            new_history_file = False
        if i == len(valid_paths):
            last_dir = True

        console.print(
            f"\n[bold blue]📁 Processing directory {i}/{len(valid_paths)}: {directory_path}[/bold blue]"
        )

        organizer = LocalFileOrganizer(
            directory_path,
            file_categories,
            dry_run=dry_run,
            recursive=recursive,
            new_history_file=new_history_file,
            last_dir=last_dir,
            pattern=pattern,
            iteration_depth=iteration_depth,
        )

        # This will show progress but won't spam console with individual file messages
        organizer.organize()

        stats: dict[str, int] = organizer.stats()

        moved: int          = stats["moved"]
        created_dirs: int   = stats["created"]
        errors: int         = stats["errors"]

        total_moved        += moved
        total_created_dirs += created_dirs
        total_errors       += errors

        # Clean empty directories after organization
        if not dry_run:
            removed_count, remove_errors = remove_dirs(
                path=directory_path,
                dry_run=dry_run,
            )
            total_created_dirs += removed_count
            total_errors += remove_errors

    # Display final summary
    console.print("\n" + "=" * 60)
    display = BeautifulDisplayAndProgress()

    display.display_final_results(
        total_moved,
        total_created_dirs,
        total_errors,
        dry_run=dry_run,
    )
    console.print("=" * 60)
