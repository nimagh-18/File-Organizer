from __future__ import annotations

from typing import TYPE_CHECKING

import typer
from src.config.logging_config import logger

if TYPE_CHECKING:
    from pathlib import Path


def remove_dirs(
    path: Path | None = None,
    dirs_path: list[Path] | None = None,
    dry_run: bool = False,
) -> tuple[int, int]:
    """
    Removes a list of empty directories.

    This function is designed to clean up empty directories, especially those left
    over after a file organization process. It prioritizes removing a specific
    list of directories. If no list is provided, it attempts to remove all
    subdirectories within a given path.

    The function iterates through the directories in reverse order to ensure
    child directories are removed before their parents. It only removes empty
    directories and handles non-empty ones gracefully, logging a warning.

    :param path: An optional Path object of a parent directory. If 'dirs_path' is not provided,
                 the function will attempt to remove all subdirectories of this path.
    :param dirs_path: An optional list of Path objects for the specific directories to be removed.
                      This parameter takes precedence over 'path'.
    :return: A tuple containing the count of directories successfully removed
             and the number of errors encountered.
    """
    # The `skip_errors` logic might need careful review depending on how you want to handle
    # non-empty directories during dry_run when not explicitly passing dirs_path.
    # For now, keeping it simple:
    skip_os_errors = False

    removed_dirs_count = 0
    errors_count = 0
    print(dirs_path)

    if not dirs_path:
        if not path:
            raise FileNotFoundError("Either 'path' or 'dirs_path' must be provided.")
        # Only iterate over actual directories for removal candidates
        dirs_path = [f for f in path.iterdir() if f.is_dir()]
        skip_os_errors = True

    for dir_path in reversed(dirs_path):
        if not dir_path.exists():
            logger.debug(f"Directory not found: {dir_path.name}")
            continue

        if not dry_run:
            # Actual removal logic
            try:
                dir_path.rmdir()
                logger.success(f"Directory removed: {dir_path.name}")
                removed_dirs_count += 1
            except OSError as e:
                # Catch OSError for non-empty directory removal or permission issues
                if not skip_os_errors:
                    logger.warning(
                        f"Could not remove directory {dir_path.name}: {e}. It might not be empty or has permission issues."
                    )
                    errors_count += 1
        else:
            # dry_run is True
            # Simulate removal: check if the directory is empty without actually deleting it
            if dir_path.is_dir() and not list(dir_path.iterdir()):
                typer.echo(
                    typer.style(
                        f"🗑️ Would remove empty directory: {dir_path.name}",  # Changed to .name for brevity, adjust as needed
                        fg=typer.colors.BLUE,
                    )
                )
                removed_dirs_count += 1

    return removed_dirs_count, errors_count
