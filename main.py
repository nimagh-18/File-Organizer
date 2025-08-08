import json
import sys
from datetime import datetime
from pathlib import Path

import typer
from loguru import logger
from tqdm import tqdm
from typing_extensions import Annotated

# --- Settings ---
BATCH_SIZE = 50  # The number of items we keep in the file and cleansing before saving

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


# TODO: add logic for this function
@app.command()
def undo() -> None:
    """Transfer the content of the folder to its latest status before categorization."""
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
    # Remove default handlers to start with a clean slate
    logger.remove()

    moved = 0
    errors = 0

    batch_entries: list[
        dict[str, str]
    ] = []  # List to store structured log entries for undo

    # First we count the number of files (without storage)
    total_files = sum(1 for f in dir_path.iterdir() if f.is_file())

    # make a gener to give the files one
    all_files = (f for f in dir_path.iterdir() if f.is_file())

    # Configure Loguru to write to a log file
    log_dir = Path(__file__).parent.joinpath("logs")
    log_dir.mkdir(exist_ok=True)
    log_path = log_dir.joinpath("organizer.log")
    logger.add(log_path, rotation="10 MB", compression="zip", encoding="utf-8")
    logger.add(
        sys.stderr,
        level="WARNING",  # Only shows WARNING, ERROR, CRITICAL
    )

    history_file = log_dir.joinpath(
        f"history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )

    created_dirs: set[Path] = set()

    with open(history_file, "w", encoding="utf-8") as jf:
        jf.write("[\n")
        first_entry = True

        # loop for organize all files in given directory
        for file in tqdm(
            all_files,
            total=total_files,
            desc=typer.style("Organizing files", fg=typer.colors.GREEN),
            unit="file",
            ncols=80,
        ):
            if not file.suffix:
                continue

            destination_dir = file_categories.get(
                file.suffix.lower(), uncategorized_dir
            )
            destination_path = dir_path.joinpath(destination_dir)

            target_path = destination_path.joinpath(file.name)

            # Create directory only once
            if destination_path not in created_dirs:
                destination_path.mkdir(exist_ok=True)
                created_dirs.add(destination_path)
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
                f"Done: {moved} files moved, {errors} errors.", fg=typer.colors.GREEN
            )
        )
    else:
        logger.warning(f"Done: {moved} files moved, {errors} errors.")
        typer.echo(
            typer.style(
                f"Done: {moved} files moved, {errors} errors.", fg=typer.colors.YELLOW
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
