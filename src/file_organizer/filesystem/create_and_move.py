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
from typing import TYPE_CHECKING, Any

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

    from rich.progress import Progress, TaskID

    from file_organizer.config.config_type_hint import FileCategories

import rich

console = rich.console.Console()


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


class LocalFileOrganizer:
    """A class to organize files in a directory into categorized subdirectories."""

    BATCH_SIZE = 50

    def __init__(
        self,
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
    ) -> None:
        """
        Initialize the LocalFileOrganizer with directory and configuration settings.

        :param dir_path: Path of the directory to be organized.
        :param file_categories: Dictionary containing file categorization rules.
        :param dry_run: If True, simulates the process without making changes.
        :param recursive: If True, organizes files in subdirectories recursively.
        :param new_history_file: If True, creates a new history file for undo functionality.
        :param last_dir: If True, closes the history file JSON array.
        :param pattern: Glob pattern to match files (e.g., "*.txt", "*.{jpg,png}").
        :param include_hidden: If True, includes hidden files (starting with '.').
        :param iteration_depth: Maximum recursion depth for subdirectories (-1 for unlimited).
        :returns: None
        """
        # Initialize counters for created directories, moved files, and errors
        self.created_dir_count = 0
        self.moved_files_count = 0
        self.errors_count = 0
        self.batch_entries: list[dict[str, str]] = []
        self.created_dirs: set[Path] = set()
        self.file_suffixes: set[str] = set()

        # Cache mapping: (suffix, min_size_mb, max_size_mb) -> destination_dir
        self.suffix_to_category_mapping: dict[tuple[str, int, float], str] = {}

        # Store input parameters as instance attributes
        self.dir_path = dir_path
        self.file_categories = file_categories
        self.dry_run = dry_run
        self.recursive = recursive
        self.new_history_file = new_history_file
        self.last_dir = last_dir
        self.pattern = pattern
        self.include_hidden = include_hidden
        self.iteration_depth = iteration_depth

        # Create instance without total_files -> auto-counting enabled
        self.display = BeautifulDisplayAndProgress()

        # Create progress bar for file operations
        self.progress: Progress = self.display.create_advanced_progress()

        # Initialize history file for undo functionality
        if new_history_file:
            self.first_entry = True
            self.history_file_path: Path = log_dir.joinpath(
                f"history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            )
        else:
            self.first_entry = True
            self.history_file_path = get_last_history()

        if not dry_run and new_history_file:
            write_one_line(self.history_file_path, "[\n")

    def organize(self) -> None:
        """
        Organize files in the directory by moving them into categorized subdirectories.

        Processes files matching the specified pattern, creating directories based on
        file extensions and size variants. Supports dry-run mode, recursive traversal,
        and depth limiting. Displays progress and logs operations.

        :returns: Tuple of (moved_files_count, created_dir_count, errors_count).
        :raises typer.Exit: If no files match the pattern or configuration is invalid.
        :example:

            Organize files in a directory recursively with depth limit:

            .. code-block:: bash

                organizer organize /path/to/dir --recursive --depth 2 --pattern "*.txt"
        """
        # Validate glob pattern before processing
        validate_glob_pattern(self.pattern)

        with self.progress:
            task_id = self.progress.add_task(
                f"{'Simulating' if self.dry_run else 'Organizing'} files...",
                total=None,
            )

            it: Generator[Path, None, None] = self._create_files_gen()

            try:
                first: Path = next(it)
            except StopIteration:
                console.print(
                    f"[yellow]No files found matching pattern '{self.pattern}' in {self.dir_path}.[/yellow]",
                )
                raise typer.Exit(0)
            else:
                # Chain the first file with the rest of the generator
                all_files: chain[Path] = chain([first], it)

            self._iterate_files(task_id, all_files)

        self.display.display_organization_stats(self.file_categories)

        # Final flush of remaining batch entries
        if self.batch_entries and not self.dry_run:
            self._finalize_history()

        if self.dry_run:
            console.print(
                f"[cyan]File suffixes processed: {sorted(self.file_suffixes)}[/cyan]",
            )
        console.print("=" * 60)

    def stats(self) -> dict[str, int]:
        """
        Return statistics about the organization process.

        :returns: Dictionary with counts of created directories, moved files, and errors.
        :example:

            Get stats after organization:

            .. code-block:: python

                organizer = LocalFileOrganizer(...)
                organizer.organize()
                print(organizer.stats())  # {'created': 2, 'moved': 10, 'errors': 0}
        """
        return {
            "created": self.created_dir_count,
            "moved": self.moved_files_count,
            "errors": self.errors_count,
        }

    def _create_files_gen(self) -> Generator[Path, Any, None]:
        """
        Generate a sequence of files to process based on pattern and options.

        Filters files by pattern, hidden status, and depth. Excludes files in created directories.

        :returns: Generator yielding file paths.
        """
        file_iteration_methods = {
            "recursive": self.dir_path.rglob,
            "not_recursive": self.dir_path.glob,
        }

        for f in (
            file_iteration_methods["recursive"](self.pattern)
            if self.recursive
            else file_iteration_methods["not_recursive"](self.pattern)
        ):
            if not f.is_file():
                continue
            if not (self.include_hidden or not f.name.startswith(".")):
                continue
            if any(f.is_relative_to(created_dir) for created_dir in self.created_dirs):
                continue
            if not (
                self.iteration_depth < 0
                or (len(f.parents) - len(self.dir_path.parents) - 1)
                <= self.iteration_depth
            ):
                continue
            yield f

    def _categorize_file(self, file: Path) -> str:
        """
        Determine the destination directory for a file based on its extension and size.

        Uses cached mappings for performance and falls back to configuration rules if no cache hit.
        Results are cached for future lookups to optimize performance.

        :param file: File to categorize.
        :returns: Name of the destination directory.
        :raises typer.Exit: If category variant configuration is invalid (e.g., missing 'name').
        :example:

            Categorize a file based on its extension and size:

            .. code-block:: python

                organizer = LocalFileOrganizer(...)
                dest_dir = organizer._categorize_file(Path("example.jpg"))
                print(dest_dir)  # e.g., "Images"
        """
        file_stat_info: stat_result = file.stat()
        file_size: float = format_size_to_mb(file_stat_info.st_size)

        # Check cache for destination directory
        destination_dir: str = self._check_cache(file, file_size)

        dir_min_size, dir_max_size = 0, float("inf")

        if not destination_dir:
            destination_dir = self._find_category(file, file_size)

            # Cache the result for future lookups
            self.suffix_to_category_mapping[
                (file.suffix, dir_min_size, dir_max_size)
            ] = destination_dir

        return destination_dir

    def _check_cache(self, file: Path, file_size: float) -> str:
        """
        Check the cache for a matching destination directory based on file suffix and size.

        Iterates through cached mappings to find a directory for the given file's suffix
        and size range.

        :param file: File to check in the cache.
        :param file_size: Size of the file in megabytes.
        :returns: Destination directory name if found in cache, otherwise empty string.
        """
        for (
            suffix,
            min_size,
            max_size,
        ), cached_dir in self.suffix_to_category_mapping.items():
            if suffix == file.suffix and min_size <= file_size < max_size:
                destination_dir = cached_dir
                return destination_dir
        return ""

    def _find_category(self, file: Path, file_size: float) -> str:
        """
        Find the destination directory for a file based on configuration rules.

        Matches the file's extension and size against categories and variants in
        the configuration. Logs the matched category and caches the result.

        :param file: File to categorize.
        :param file_size: Size of the file in megabytes.
        :returns: Name of the destination directory.
        :raises typer.Exit: If category variant configuration is invalid (e.g., missing 'name').
        :example:

            Find category for a file:

            .. code-block:: python

                organizer = LocalFileOrganizer(...)
                dest_dir = organizer._find_category(Path("doc.pdf"), 1.5)
                print(dest_dir)  # e.g., "Documents"
        """
        destination_dir = ""

        category_matched = False
        for category in self.file_categories["categories"]:
            if file.suffix not in category.get("extensions", []):
                continue
            for variant in category.get("variants", []):
                dir_min_size = variant.get("min_size_mb", 0)
                dir_max_size = variant.get("max_size_mb", float("inf"))

                if file_size >= dir_min_size and file_size < dir_max_size:
                    if "name" not in variant:
                        console.print(
                            "[red]Error: Category variant missing name in configuration![/red]",
                        )
                        raise typer.Exit(1)
                    destination_dir += variant["name"] + "-"
                    break

            destination_dir += category["name"]
            category_matched = True

            logger.info(
                f"File {file.name} matches category '{category['name']}' with size {file_size:.2f} MB",
            )
            break

        if not category_matched:
            destination_dir = self.file_categories["defaults"]["name"]

        return destination_dir

    def _create_dir(self, destination_path: Path) -> None:
        """
        Create a destination directory if it doesn't exist.

        :param destination_path: Path of the directory to create.
        :returns: None
        """
        # Create directory if it doesn't exist and hasn't been created
        if (destination_path not in self.created_dirs) and (
            not destination_path.exists()
        ):
            if self.dry_run:
                self.progress.console.print(
                    f"[blue]📦 Would create directory: {destination_path.name}[/blue]",
                )
            else:
                destination_path.mkdir(exist_ok=True)
                logger.info(f"Directory created: {destination_path}")

            self.created_dirs.add(destination_path)
            self.created_dir_count += 1

            if not self.dry_run:
                self.batch_entries.append(
                    {
                        "timestamp": str(datetime.now()),
                        "action": "create_dir",
                        "path": str(destination_path),
                        "status": "success",
                    },
                )

    def _move_file(self, file: Path, destination_path: Path, target_path: Path) -> None:
        """
        Move a file to its destination directory, handling duplicates.

        :param file: Source file to move.
        :param destination_path: Destination directory path.
        :param target_path: Target path for the file.
        :returns: None
        """
        try:
            # Prevent file overwrite by appending a counter suffix
            counter = 1
            while target_path.exists():
                target_path = destination_path.joinpath(
                    f"{file.stem}_{counter}{file.suffix}",
                )
                counter += 1

            # Simulate or perform file move
            if self.dry_run:
                self.progress.console.print(
                    f"[blue]📄 Would move: {file.name} -> {destination_path.name}[/blue]",
                )
            else:
                original_path = file.resolve()

                try:
                    file.rename(target_path)
                except OSError:
                    # Fallback: copy then delete for cross-device compatibility
                    shutil.copy2(original_path, target_path)
                    original_path.unlink()
                new_path = target_path.resolve()

                logger.success(f"File moved from {original_path} to {new_path}")
                self.batch_entries.append(
                    {
                        "timestamp": str(datetime.now()),
                        "action": "move_file",
                        "source": str(new_path),
                        "destination": str(original_path),
                        "original_name": file.name,
                        "status": "success",
                    },
                )

            self.moved_files_count += 1

        except Exception as e:
            error_msg = f"Error processing file {file.name}: {e}"
            if self.dry_run:
                self.progress.console.print(
                    f"[red]❌ Would have failed: {error_msg}[/red]"
                )
            else:
                logger.error(error_msg)
            self.errors_count += 1

    def _flush_batch(self) -> None:
        """
        Flush batch entries to the history file.

        :returns: None
        """
        write_entries(
            self.history_file_path,
            self.batch_entries,
            self.first_entry,
        )

        self.first_entry = False
        self.batch_entries.clear()

    def _finalize_history(self) -> None:
        """
        Finalize the history file by writing remaining entries and closing JSON array.

        :returns: None
        """
        write_entries(
            self.history_file_path,
            self.batch_entries,
            self.first_entry,
        )

        if self.last_dir:
            write_one_line(self.history_file_path, "\n]")
        else:
            write_one_line(self.history_file_path, ",\n")

    def _iterate_files(self, task_id: TaskID, all_files: chain[Path]) -> None:
        """
        Iterate over files and process them for organization.

        :param task_id: Rich progress task ID.
        :param all_files: Chain of file paths to process.
        :returns: None
        """
        for file in all_files:
            self.file_suffixes.add(file.suffix)

            # Display file processing information
            action = "📁 Moving" if not self.dry_run else "👀 Would move"
            self.display.display_file_info(
                self.progress,
                task_id,
                file,
                action,
            )

            destination_dir: str = self._categorize_file(file)

            destination_path: Path = file.parent.joinpath(destination_dir)
            target_path: Path = destination_path.joinpath(file.name)

            self._create_dir(destination_path)
            self._move_file(file, destination_path, target_path)

            # Flush batch entries to history file if batch size is reached
            if len(self.batch_entries) >= self.__class__.BATCH_SIZE and not self.dry_run:
                self._flush_batch()

            self.progress.advance(task_id)
