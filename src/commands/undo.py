from __future__ import annotations

from pathlib import Path

import typer
from src.filesystem.beautiful_display_and_progress import BeautifulDisplayAndProgress
from src.filesystem.dir_cleaner import remove_dirs
from src.history.manager import get_last_history, undo_files

app = typer.Typer()


@app.command()
def undo() -> None:
    """Transfer the content of the folder to its latest status before categorization."""
    try:
        last_history_file_path: Path = get_last_history()
    except typer.Exit:
        return

    removed_dirs_count = 0
    dirs_errors_count = 0

    moved_back_count, file_errors_count, dirs_path = undo_files(last_history_file_path)

    if dirs_path:
        removed_dirs_count, dirs_errors_count = remove_dirs(dirs_path=dirs_path)

    errors_count = file_errors_count + dirs_errors_count

    display = BeautifulDisplayAndProgress()
    display.display_final_results(
        moved_back_count,
        removed_dirs_count,
        errors_count,
        "Moved Backed Files",
        "Directories Removed",
    )
