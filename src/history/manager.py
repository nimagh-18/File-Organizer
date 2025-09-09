from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import ijson
import typer
from loguru import logger
from src.filesystem.beautiful_display_and_progress import BeautifulDisplayAndProgress

if TYPE_CHECKING:
    from collections.abc import Generator


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
    :return: A tuple containing:
             - count of files moved back,
             - number of errors during file moves,
             - list of Path objects for the directories to be removed.
    """
    # Create progress bar
    progress = BeautifulDisplayAndProgress().create_advanced_progress()

    moved_back_count = 0
    errors_count = 0
    dirs_path: list[Path] = []

    # Load all history entries first (to set correct progress total)
    all_history: tuple[Any, ...] = tuple(stream_history_file(last_history_file_path))

    with progress:
        task_id = progress.add_task("Undoing actions", total=len(all_history))

        for history in all_history:
            action = history.get("action")
            status = history.get("status")

            if status != "success":
                logger.debug(f"Skipping action due to previous error: {action}")
                progress.advance(task_id)
                continue

            if action == "move_file":
                source_path = Path(history["source"])
                destination_path = Path(history["destination"])

                if not source_path.exists():
                    logger.warning(f"File not found at source location: {source_path}")
                    progress.advance(task_id)
                    continue

                try:
                    # Check if the destination already exists to avoid overwriting
                    if destination_path.exists():
                        logger.warning(
                            f"Destination path {destination_path} already exists. Skipping move back."
                        )
                        progress.advance(task_id)
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

            # Advance progress after each action
            progress.advance(task_id)

    return moved_back_count, errors_count, dirs_path
