import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Generator

import typer
from loguru import logger
from tqdm import tqdm
from typing_extensions import Annotated

# --- Settings ---
BATCH_SIZE = 50  # The number of items we keep in the file and cleansing before saving

# --- Config logur ---
# Remove default handlers to start with a clean slate
logger.remove()

# Configure Loguru to write to a log file
log_dir = Path(__file__).parent.joinpath("logs")
log_dir.mkdir(exist_ok=True)
log_path = log_dir.joinpath("organizer.log")

logger.add(log_path, rotation="10 MB", compression="zip", encoding="utf-8")
logger.add(
    sys.stderr,
    level="WARNING",  # Only shows WARNING, ERROR, CRITICAL
)

app = typer.Typer()


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


@app.command()
def show_config() -> None:
    config = load_config()
    typer.echo(json.dumps(config, indent=4, ensure_ascii=False))


def open_config_with_specific_editor(file_path: Path):
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


@app.command()
def edit_config() -> None:
    """Open the config.json file in a text editor."""
    open_config_with_specific_editor(Path("config.json"))


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
    logs_dir_path = Path("logs")

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
        typer.Exit(0)

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


def stream_history_file(file_path: Path) -> Generator[dict[str, Any], None, None]:
    """
    Reads a history JSON file line by line and yields each JSON object
    as a dictionary. This allows for processing large files without loading
    the entire file into memory at once.

    :param file_path: The Path object of the history JSON file.
    :return: A generator that yields one dictionary per line.
    """
    if not file_path.exists():
        print(f"Error: The history file at '{file_path}' was not found.")
        return

    try:
        with open(file_path, encoding="utf-8") as f:
            python_str = ""

            for line in f:
                line: str = line.strip()

                if line in {"[", "]"}:
                    continue
                # If json object is complete
                if "}," in line or "}" in line:
                    line = line.removesuffix(",")

                    python_str += line
                    history: dict[str, str] = json.loads(python_str)
                    python_str = ""

                    yield history
                    continue

                python_str += line

    except Exception as e:
        print(f"An unexpected error occurred while reading the file: {e}")


# TODO: add logic for this function
@app.command()
def undo() -> None:
    """Transfer the content of the folder to its latest status before categorization."""
    try:
        last_history_file_path: Path = get_last_history()
    except typer.Exit:
        return

    pbar = tqdm(
        desc=typer.style("Undoing actions", fg=typer.colors.GREEN),
        unit="action",
        ncols=80,
        total=None,
    )

    moved_back_count = 0
    removed_dirs_count = 0
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

            if source_path.exists():
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
            else:
                logger.warning(f"File not found at source location: {source_path}")

        elif action == "create_dir":
            dirs_path.append(Path(history["path"]))

        pbar.update(1)

    pbar.close()

    for dir_path in reversed(dirs_path):
        if dir_path.exists():
            try:
                dir_path.rmdir()
                logger.success(f"Directory removed: {dir_path.name}")
                removed_dirs_count += 1
            except OSError as e:
                # Catch OSError for non-empty directory removal
                logger.warning(
                    f"Could not remove directory {dir_path.name}: {e}. It might not be empty."
                )
        else:
            logger.debug(f"Directory not found: {dir_path.name}")

    if errors_count == 0:
        typer.echo(
            typer.style(
                f"Undo completed: {moved_back_count} files moved back, {removed_dirs_count} directories removed.",
                fg=typer.colors.GREEN,
            )
        )
    else:
        typer.echo(
            typer.style(
                f"Undo finished with errors: {moved_back_count} files moved back, {removed_dirs_count} directories removed, {errors_count} errors.",
                fg=typer.colors.YELLOW,
            )
        )


def write_entries_in_json(entries: list[dict[str, str]]) -> None:
    pass


def create_dirs_and_move_files(
    dir_path: Path,
    uncategorized_dir: Path,
    file_categories: dict[str, str],
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
    """
    dirs_created = 0
    moved = 0
    errors = 0

    batch_entries: list[
        dict[str, str]
    ] = []  # List to store structured log entries for undo

    pbar = tqdm(
        desc=typer.style("Create dirs and move files", fg=typer.colors.GREEN),
        unit="action",
        ncols=80,
        total=None,
    )

    # make a gener to give the files one
    all_files = (f for f in dir_path.iterdir() if f.is_file())
    total_files = 0

    history_file = log_dir.joinpath(
        f"history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )

    created_dirs: set[Path] = set()

    with open(history_file, "w", encoding="utf-8") as jf:
        jf.write("[\n")
        first_entry = True

        # loop for organize all files in given directory
        for file in all_files:
            total_files += 1
            pbar.total = total_files  # update the total count in the progress bar
            pbar.refresh()

            destination_dir = file_categories.get(
                file.suffix.lower(), uncategorized_dir
            )
            destination_path = dir_path.joinpath(destination_dir)

            target_path = destination_path.joinpath(file.name)

            # Create directory only once
            if destination_path not in created_dirs:
                destination_path.mkdir(exist_ok=True)
                created_dirs.add(destination_path)
                dirs_created += 1

                logger.info(f"Directory created: {destination_path}")

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
                file.rename(target_path)
                moved += 1

                logger.success(f"File moved from {original_path} to {new_path}")
                batch_entries.append(
                    {
                        "timestamp": str(datetime.now()),
                        "action": "move_file",
                        "source": str(new_path),  # New location
                        "destination": str(original_path),  # Original location
                        "original_name": file.name,
                        "status": "success",
                    }
                )

            except Exception as e:
                # All error messages are now handled by Loguru
                logger.error(f"Error moving file {file.name}: {e}")
                errors += 1

            # Save every 50 items once
            if len(batch_entries) >= BATCH_SIZE:
                for entry in batch_entries:
                    if not first_entry:
                        jf.write(",\n")
                    jf.write(json.dumps(entry, ensure_ascii=False, indent=4))
                    first_entry = False
                batch_entries.clear()
                jf.flush()

            pbar.update(1)

        pbar.close()

        # Save the remaining items
        if batch_entries:
            for entry in batch_entries:
                if not first_entry:
                    jf.write(",\n")
                jf.write(json.dumps(entry, ensure_ascii=False, indent=4))
                first_entry = False

        # Close the json array
        jf.write("\n]")

    # Final summary is also handled by Loguru
    if errors == 0:
        logger.success(f"Done: {moved} files moved, {errors} errors.")
        typer.echo(
            typer.style(
                f"Done: {dirs_created} directory created, {moved} files moved, {errors} errors.", fg=typer.colors.GREEN
            )
        )
    else:
        logger.warning(f"Done: {moved} files moved, {errors} errors.")
        typer.echo(
            typer.style(
                f"Done: {dirs_created} directory created, {moved} files moved, {errors} errors.", fg=typer.colors.YELLOW
            )
        )


@app.command()
def organize(
    path: Annotated[str, typer.Argument(help="Path of the directory to organize")],
) -> None:
    """
    Organize an directory.

    :param path: Path of the directory to organize.
    """
    DIR_PATH = Path(path)

    UNCATEGORIZED_DIR = DIR_PATH.joinpath("Other")  # dir for unknown files

    # Request to verify from user
    if not typer.confirm(
        typer.style(
            f"Are you sure you want to organize the directory '{DIR_PATH}'?",
            fg=typer.colors.YELLOW,
        )
    ):
        typer.echo(typer.style("Operation cancelled.", fg=typer.colors.RED))
        raise typer.Exit()

    file_categories = load_config()

    create_dirs_and_move_files(DIR_PATH, UNCATEGORIZED_DIR, file_categories)


if __name__ == "__main__":
    app()
