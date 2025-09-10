"""
File organization core functionality with enhanced progress tracking.

This module handles the core logic of creating directories and moving files
based on categorization rules, featuring advanced progress visualization.
"""

from __future__ import annotations

import shutil
from datetime import datetime
from itertools import chain
from pathlib import Path
from typing import TYPE_CHECKING

import typer

from file_organizer.config.logging_config import log_dir, logger
from file_organizer.core.validator import validate_glob_pattern
from file_organizer.filesystem.beautiful_display_and_progress import (
    BeautifulDisplayAndProgress,
)
from file_organizer.history.json_writers import write_entries, write_one_line
from file_organizer.history.manager import get_last_history

if TYPE_CHECKING:
    from collections.abc import Generator
    from os import stat_result
    from pathlib import Path

    from rich.progress import Progress

    from file_organizer.config.config_type_hint import FileCategories

import rich

console = rich.console.Console()

# --- Settings ---
BATCH_SIZE = 50  # Number of items to keep in memory before flushing to history file


def format_size_to_mb(size_bytes: int) -> float:
    """
    Convert size from bytes to megabytes.

    :param size_bytes: Size in bytes
    :type size_bytes: int
    :return: Size in megabytes
    :rtype: float
    """
    if size_bytes == 0:
        return 0
    return size_bytes / (1000 * 1000)


def create_dirs_and_move_files(
    dir_path: Path,
    file_categories: FileCategories,
    *,
    dry_run: bool,
    recursive: bool,
    new_history_file: bool = True,
    last_dir: bool = True,
    pattern: str = "*",
    include_hidden: bool = False,
    iteration_depth: int,
) -> tuple[int, int, int]:
    """
    Organize files in a directory by moving them into categorized subdirectories.

    Creates directories for each file category and moves files based on their
    extensions and size-based variants. Uses a suffix-to-category mapping to cache
    category lookups for performance optimization, accounting for size variants.
    Supports dry-run mode, recursive traversal, glob pattern filtering, and hidden file inclusion.

    :param dir_path: Path of the directory to be organized.
    :param file_categories: Dictionary containing file categorization rules.
    :param dry_run: If True, simulates the process without making changes.
    :param recursive: If True, organizes files in subdirectories recursively.
    :param new_history_file: If True, creates a new history file for undo functionality.
    :param last_dir: If True, closes the history file JSON array.
    :param pattern: Glob pattern to match files (e.g., "*.txt", "*.{jpg,png}").
    :param include_hidden: If True, includes hidden files (starting with '.').
    :returns: Tuple of (moved_files_count, created_dir_count, errors_count).
    :raises typer.Exit: If category variant configuration or pattern is invalid.
    """
    # Validate glob pattern before processing
    validate_glob_pattern(pattern)

    created_dir_count = 0
    moved_files_count = 0
    errors_count = 0
    batch_entries: list[dict[str, str]] = []
    created_dirs: set[Path] = set()
    file_suffixes: set[str] = set()
    # Cache mapping: (suffix, min_size_mb, max_size_mb) -> destination_dir
    suffix_to_category_mapping: dict[tuple[str, int, float], str] = {}

    file_iteration_methods = {
        "recursive": dir_path.rglob,
        "not_recursive": dir_path.glob,
    }

    it: Generator[Path, None, None] = (
        f
        for f in (
            file_iteration_methods["recursive"](pattern)
            if recursive
            else file_iteration_methods["not_recursive"](pattern)
        )
        if f.is_file()
        and (include_hidden or not f.name.startswith("."))
        and not any(f.is_relative_to(created_dir) for created_dir in created_dirs)
        and (
            iteration_depth < 0
            or (len(f.parents) - len(dir_path.parents) - 1) <= iteration_depth
        )
    )

    try:
        first: Path = next(it)
    except StopIteration:
        console.print(
            f"[yellow]No files found matching pattern '{pattern}' in {dir_path}.[/yellow]"
        )
        return 0, 0, 0
    else:
        all_files: chain[Path] = chain([first], it)

    # Create instance without total_files -> auto-counting enabled
    display = BeautifulDisplayAndProgress()

    # Create progress bar
    progress: Progress = display.create_advanced_progress()

    if new_history_file:
        first_entry = True
        history_file_path: Path = log_dir.joinpath(
            f"history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        )
    else:
        first_entry = True
        history_file_path = get_last_history()

    if not dry_run and new_history_file:
        write_one_line(history_file_path, "[\n")

    with progress:
        task_id = progress.add_task(
            f"{'Simulating' if dry_run else 'Organizing'} files...",
            total=None,
        )

        for file in all_files:
            file_suffixes.add(file.suffix)

            # Update progress with file information
            action = "📁 Moving" if not dry_run else "👀 Would move"
            display.display_file_info(
                progress,
                task_id,
                file,
                action,
            )

            file_stat_info: stat_result = file.stat()
            file_size: float = format_size_to_mb(file_stat_info.st_size)

            # Check cache for destination directory
            destination_dir = ""
            for (
                suffix,
                min_size,
                max_size,
            ), cached_dir in suffix_to_category_mapping.items():
                if suffix == file.suffix and min_size <= file_size < max_size:
                    destination_dir = cached_dir
                    break

            dir_min_size, dir_max_size = 0, float("inf")

            if not destination_dir:
                category_matched = False
                for category in file_categories["categories"]:
                    if file.suffix not in category.get("extensions", []):
                        continue
                    for variant in category.get("variants", []):
                        dir_min_size = variant.get("min_size_mb", 0)
                        dir_max_size = variant.get("max_size_mb", float("inf"))

                        if file_size >= dir_min_size and file_size < dir_max_size:
                            if "name" not in variant:
                                console.print(
                                    "[red]Error: Category variant missing name in configuration![/red]"
                                )
                                raise typer.Exit(1)
                            destination_dir += variant["name"] + "-"
                            break

                    destination_dir += category["name"]
                    category_matched = True

                    logger.info(
                        f"File {file.name} matches category '{category['name']}' with size {file_size:.2f} MB"
                    )
                    break

                if not category_matched:
                    destination_dir = file_categories["defaults"]["name"]

                # Cache the result
                suffix_to_category_mapping[
                    (file.suffix, dir_min_size, dir_max_size)
                ] = destination_dir

            destination_path = file.parent.joinpath(destination_dir)
            target_path: Path = destination_path.joinpath(file.name)

            # Create directory if needed
            if (destination_path not in created_dirs) and (
                not destination_path.exists()
            ):
                if dry_run:
                    progress.console.print(
                        f"[blue]📦 Would create directory: {destination_path.name}[/blue]"
                    )
                else:
                    destination_path.mkdir(exist_ok=True)
                    logger.info(f"Directory created: {destination_path}")

                created_dirs.add(destination_path)
                created_dir_count += 1

                if not dry_run:
                    batch_entries.append(
                        {
                            "timestamp": str(datetime.now()),
                            "action": "create_dir",
                            "path": str(destination_path),
                            "status": "success",
                        }
                    )

            try:
                # Prevent file overwrite with counter suffix
                counter = 1
                while target_path.exists():
                    target_path = destination_path.joinpath(
                        f"{file.stem}_{counter}{file.suffix}",
                    )
                    counter += 1

                # Move file to destination
                if dry_run:
                    progress.console.print(
                        f"[blue]📄 Would move: {file.name} -> {destination_path.name}[/blue]"
                    )
                else:
                    original_path = file.resolve()

                    try:
                        file.rename(target_path)
                    except OSError:
                        # fallback: copy2 then unlink (safer across devices)
                        shutil.copy2(original_path, target_path)
                        original_path.unlink()
                    new_path = target_path.resolve()

                    logger.success(f"File moved from {original_path} to {new_path}")
                    batch_entries.append(
                        {
                            "timestamp": str(datetime.now()),
                            "action": "move_file",
                            "source": str(new_path),
                            "destination": str(original_path),
                            "original_name": file.name,
                            "status": "success",
                        }
                    )

                moved_files_count += 1

            except Exception as e:
                error_msg = f"Error processing file {file.name}: {e}"
                if dry_run:
                    progress.console.print(
                        f"[red]❌ Would have failed: {error_msg}[/red]"
                    )
                else:
                    logger.error(error_msg)
                errors_count += 1

            # Flush batch entries to history file
            if len(batch_entries) >= BATCH_SIZE and not dry_run:
                write_entries(history_file_path, batch_entries, first_entry)
                first_entry = False
                batch_entries.clear()

            # progress.update(task_id, advance=1)
            progress.advance(task_id)

    display.display_organization_stats(file_categories)

    # Final flush of remaining batch entries
    if batch_entries and not dry_run:
        write_entries(history_file_path, batch_entries, first_entry)

        if last_dir:
            write_one_line(history_file_path, "\n]")
        else:
            write_one_line(history_file_path, ",\n")

    if dry_run:
        console.print(f"[cyan]File suffixes processed: {sorted(file_suffixes)}[/cyan]")
    console.print("=" * 60)

    return moved_files_count, created_dir_count, errors_count
