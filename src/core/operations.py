from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Generator

import ijson
import typer
from loguru import logger
from src.core.constants import SystemProtector
from src.core.utils import find_project_root
from tqdm import tqdm

# --- Settings ---
BATCH_SIZE = 50  # The number of items we keep in the file and cleansing before saving

# --- Config logur ---
# Remove default handlers to start with a clean slate
logger.remove()

# Configure Loguru to write to a log file
project_root = find_project_root(Path(__file__))
log_dir = project_root.joinpath("src/logs")

log_dir.mkdir(exist_ok=True)
log_path = log_dir.joinpath("organizer.log")

logger.add(log_path, rotation="10 MB", compression="zip", encoding="utf-8")
logger.add(
    sys.stderr,
    level="WARNING",  # Only shows WARNING, ERROR, CRITICAL
)


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


def load_config() -> dict[str, str]:
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
        return json.load(jf)


def parse_history_file(history_file: Path) -> datetime:
    """Parse the history files in the logs directory and return a list of."""
    return datetime.strptime(
        history_file.stem.replace("history_", ""),
        "%Y%m%d_%H%M%S",
    )


def get_last_history() -> Path:
    """
    Get the last history file from the logs directory.

    Checks the logs directory for files that match the naming
    convention "history_YYYYMMDD_HHMMSS.json", extracts the date and time from
    the file names, and returns the most recent file based on the date and time.

    :raises typer.Exit: if logs directory does not exist or no history files found

    :return: The Path object of the most recent history file.
    """
    logs_dir_path = Path("src/logs")

    histories_date_and_time: list[datetime] = []

    # Check if the logs directory exists
    if not logs_dir_path.exists():
        logger.error("Logs directory does not exist.")
        typer.echo(typer.style("Logs directory does not exist.", fg=typer.colors.RED))
        raise typer.Exit(1)

    for file in logs_dir_path.iterdir():
        if file.suffix != ".json":
            continue

        if not file.name.startswith("history_"):
            continue

        file_datetime = parse_history_file(file)
        if file_datetime:
            histories_date_and_time.append(file_datetime)

    if not histories_date_and_time:
        logger.info("No history files found.")
        typer.echo(typer.style("No history files found.", fg=typer.colors.YELLOW))
        raise typer.Exit(0)

    # Sort the list of datetime objects in descending order
    histories_date_and_time.sort(reverse=True)

    history_file_date_and_time: str = histories_date_and_time[0].strftime(
        "%Y%m%d_%H%M%S"
    )

    # Absolute path of the last history file
    last_history_file_path: Path = logs_dir_path.joinpath(
        f"history_{history_file_date_and_time}.json",
    ).resolve()

    return last_history_file_path


def stream_history_file(file_path: Path) -> Generator[Any, Any, None]:
    """
    Reads a history JSON file using the ijson library for streaming.

    :param file_path: The path to the history JSON file.
    :yield: A dictionary for each object in the top-level JSON array.
    """
    if not file_path.exists():
        print(f"Error: The history file at '{file_path}' was not found.")
        return

    try:
        with open(file_path, "rb") as f:
            objects = ijson.items(f, "item")

            yield from objects
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


def undo_files(last_history_file_path: Path) -> tuple[int, int, list[Path]]:
    """
    Reverts file moves from the last organization operation and collects created directory paths.

    This function reads the latest history file, moves files back to their
    original locations, and records the paths of directories that were created.
    It uses a dynamic progress bar for efficiency.

    :param last_history_file_path: The path to the latest history JSON file.
    :return: A tuple containing the count of files moved back, the number of errors
             during file moves, and a list of Path objects for the directories to be removed.
    """
    pbar = tqdm(
        desc=typer.style("Undoing actions", fg=typer.colors.GREEN),
        unit="action",
        ncols=80,
        total=None,
    )

    moved_back_count = 0
    errors_count = 0
    total_files = 0

    dirs_path: list[Path] = []

    for history in stream_history_file(last_history_file_path):
        total_files += 1
        pbar.total = total_files  # update the total count in the progress bar
        pbar.refresh()

        action = history.get("action")
        status = history.get("status")

        if status != "success":
            logger.debug(f"Skipping action due to previous error: {action}")
            continue

        if action == "move_file":
            source_path = Path(history["source"])
            destination_path = Path(history["destination"])

            if not source_path.exists():
                logger.warning(f"File not found at source location: {source_path}")
                continue

            try:
                # Check if the destination already exists to avoid overwriting
                if destination_path.exists():
                    logger.warning(
                        f"Destination path {destination_path} already exists. Skipping move back."
                    )
                    continue

                source_path.rename(destination_path)
                logger.success(
                    f"File moved back from {source_path.name} to {destination_path.parent}"
                )
                moved_back_count += 1
            except Exception as e:
                logger.error(f"Error moving file back {source_path}: {e}")
                errors_count += 1

        elif action == "create_dir":
            dirs_path.append(Path(history["path"]))

        pbar.update(1)

    pbar.close()

    return moved_back_count, errors_count, dirs_path


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


def write_one_line(file_path: Path, line: str) -> None:
    """
    Writes a single line of text to a file in append mode.

    This is primarily used to add simple characters like '[' or ']' to
    the history log file.

    :param file_path: The path of the file to write to.
    :param line: The string to be written to the file.
    """
    with open(file_path, "a", encoding="utf-8") as jf:
        jf.write(line)


def write_entries(
    file_path: Path,
    batch_entries: list[dict[str, str]],
    first_entry: bool = False,
) -> None:
    """
    Appends a batch of JSON entries to a history log file.

    This function serializes a list of dictionaries into a JSON format
    and appends them to a file. It handles the formatting (adding commas)
    to ensure the file remains a valid JSON array. The list of entries
    is cleared after writing to free up memory.

    :param file_path: The path of the file to append the entries to.
    :param batch_entries: A list of dictionaries representing the actions
                          to be logged. This list is cleared after writing.
    :param first_entry: A flag to determine if this is the first entry in the JSON array,
                        to prevent adding a leading comma.
    """
    with open(file_path, "a", encoding="utf-8") as jf:
        for entry in batch_entries:
            if not first_entry:
                jf.write(",\n")
            jf.write(json.dumps(entry, ensure_ascii=False, indent=4))
            first_entry = False
        batch_entries.clear()
        jf.flush()


def create_dirs_and_move_files(
    dir_path: Path,
    uncategorized_dir: Path,
    file_categories: dict[str, str],
    dry_run: bool,
) -> None:
    """
    Organizes files in a given directory by moving them into subdirectories
    based on their file extensions.

    It creates new directories for each category (e.g., 'Images', 'Documents')
    if they don't exist. Files without a matching category are moved to a
    specific 'Other' directory.

    :param dir_path: The path of the directory to be organized.
    :param uncategorized_dir: The Path object for the directory where
                              uncategorized files will be moved.
    :param file_categories: A dictionary mapping file extensions (keys)
                            to category names (values).
    :param dry_run: If True, simulates the organization process without
                    making any changes to the file system.
    """
    dirs_created = 0
    moved = 0
    errors = 0

    batch_entries: list[
        dict[str, str]
    ] = []  # List to store structured log entries for undo

    # Use a different color and description for dry_run
    pbar_color = typer.colors.CYAN if dry_run else typer.colors.GREEN
    pbar_desc = "Simulating actions" if dry_run else "Performing actions"
    pbar = tqdm(
        desc=typer.style(pbar_desc, fg=pbar_color),
        unit="action",
        ncols=80,
        total=None,
    )

    all_files = (f for f in dir_path.iterdir() if f.is_file())
    total_files = 0
    first_entry = True

    history_file_path: Path = log_dir.joinpath(
        f"history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )

    if not dry_run:
        write_one_line(history_file_path, "[\n")

    created_dirs: set[Path] = set()

    file_suffixs: set[str] = set()

    for file in all_files:
        total_files += 1
        pbar.total = total_files
        pbar.refresh()

        file_suffixs.add(file.suffix)

        destination_dir = file_categories.get(file.suffix.lower(), uncategorized_dir)
        destination_path = dir_path.joinpath(destination_dir)

        target_path = destination_path.joinpath(file.name)

        # Create directory only once
        if destination_path not in created_dirs:
            if dry_run:
                pbar.write(
                    typer.style(
                        f"📦 Would create directory: {destination_path.name}",
                        fg=typer.colors.BLUE,
                    )
                )
            else:
                destination_path.mkdir(exist_ok=True)
                logger.info(f"Directory created: {destination_path}")

            created_dirs.add(destination_path)
            dirs_created += 1

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
            # Preventing file overwrite
            counter = 1
            while target_path.exists():
                target_path = destination_path.joinpath(
                    f"{file.stem}_{counter}{file.suffix}",
                )
                counter += 1

            # Save original path before moving
            original_path = file.resolve()
            new_path = target_path.resolve()

            # Move file to destination_dir
            if dry_run:
                pbar.write(
                    typer.style(
                        f"📄 Would move: {file.name} -> {destination_path.name}",
                        fg=typer.colors.BLUE,
                    )
                )
            else:
                file.rename(target_path)
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

            moved += 1

        except Exception as e:
            if dry_run:
                pbar.write(
                    typer.style(
                        f"❌ Would have failed to move file {file.name}: {e}",
                        fg=typer.colors.RED,
                    )
                )
            else:
                logger.error(f"Error moving file {file.name}: {e}")
            errors += 1

        if len(batch_entries) >= BATCH_SIZE and not dry_run:
            write_entries(history_file_path, batch_entries, first_entry)
            first_entry = False

        pbar.update(1)

    pbar.close()

    if batch_entries and not dry_run:
        write_entries(history_file_path, batch_entries, first_entry)
        write_one_line(history_file_path, "\n]")

    # Final summary with a clear distinction for dry_run
    if dry_run:
        typer.echo(
            typer.style(
                f"\n[Dry Run]: Would have created {dirs_created} directories: {sorted([d.name for d in created_dirs])}\n"
                f"           Would have moved {moved} files with the following suffixes: {sorted(file_suffixs)}\n"
                f"           and encountered {errors} potential errors.",
                fg=typer.colors.CYAN,
            )
        )
    else:
        if errors == 0:
            typer.echo(
                typer.style(
                    f"\nDone: {dirs_created} directory created, {moved} files moved, {errors} errors.",
                    fg=typer.colors.GREEN,
                )
            )
        else:
            typer.echo(
                typer.style(
                    f"\nDone: {dirs_created} directory created, {moved} files moved, {errors} errors.",
                    fg=typer.colors.YELLOW,
                )
            )


# --- validate_directory_access function ---
_system_protector_instance = SystemProtector()  # Instantiate once globally or pass it


def validate_directory_access(path: Path) -> bool:
    """Validate directory is safe and accessible."""
    # First check existence and permissions
    if not path.exists():
        logger.error(f"Error: Path does not exist: {path}")
        typer.echo(
            typer.style(
                f"Error: The path '{path}' does not exist.", fg=typer.colors.RED
            )
        )
        return False

    if not path.is_dir():
        logger.error(f"Error: Path is not a directory: {path}")
        typer.echo(
            typer.style(
                f"Error: The path '{path}' is not a directory.", fg=typer.colors.RED
            )
        )
        return False

    if not os.access(path, os.R_OK | os.W_OK):
        logger.error(f"Error: Insufficient permissions for path: {path}")
        typer.echo(
            typer.style(
                f"Error: Insufficient permissions to read/write in '{path}'.",
                fg=typer.colors.RED,
            )
        )
        return False

    # Then check protection status using the global instance
    if _system_protector_instance.is_protected(path):
        logger.warning(f"Attempted to access protected path: {path}")
        typer.echo(
            typer.style(
                f"Error: You cannot organize a protected system or sensitive directory: '{path}'. Operation cancelled.",
                fg=typer.colors.RED,
            )
        )
        return False

    return True
