from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

import typer
from src.config.logging_config import log_dir, logger
from src.history.json_writers import write_entries, write_one_line
from tqdm import tqdm

if TYPE_CHECKING:
    from pathlib import Path

# --- Settings ---
BATCH_SIZE = 50  # The number of items we keep in the file and cleansing before saving


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
        if (destination_path not in created_dirs) and (not destination_path.exists()):
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
