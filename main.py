import json
from pathlib import Path

import typer
from tqdm import tqdm
from typing_extensions import Annotated

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


# TODO: should add this func logic
@app.command()
def show_config() -> None:
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
    moved = 0
    errors = 0

    all_files = [f for f in dir_path.iterdir() if f.is_file()]

    # loop for organize all files in given directory
    for file in tqdm(all_files, desc="Organizing files", unit="file"):
        tqdm.write(f"Processing {file.name}")

        if not file.suffix:
            continue

        destination_dir = file_categories.get(file.suffix.lower(), uncategorized_dir)
        destination_path = dir_path.joinpath(destination_dir)

        target_path = destination_path.joinpath(file.name)

        try:
            # create destination_dir
            destination_path.mkdir(exist_ok=True)

            # Preventing file overwrite
            counter = 1
            while target_path.exists():
                target_path = destination_path.joinpath(
                    f"{file.stem}_{counter}{file.suffix}",
                )
                counter += 1

            # move file to destination_dir
            file.rename(target_path)
            moved += 1

        except Exception as e:
            print(f"Error moving file {file.name}: {e}")
            errors += 1

    print("-" * 50)
    print(f"Done: {moved} files moved, {errors} errors.")


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
        f"Are you sure you want to organize the directory '{DIR_PATH}'?"
    ):
        typer.echo("Operation cancelled.")
        raise typer.Exit()

    file_categories = load_config()

    create_dirs_and_move_files(DIR_PATH, UNCATEGORIZED_DIR, file_categories)


if __name__ == "__main__":
    app()
