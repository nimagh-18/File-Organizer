import os
from pathlib import Path


# pyproject.tomlFind the root of the project by searching the pyproject.toml file
def find_project_root(file_path: Path) -> Path:
    current_path = file_path

    while not (current_path.joinpath("pyproject.toml")).exists():
        if current_path == current_path.parent:  # prevent infinite loop
            raise FileNotFoundError("Could not find project root with pyproject.toml")

        current_path: Path = current_path.parent

    return current_path


def clearscreen(numlines: int = 100) -> None:
    """
    Clear the console.
    numlines is an optional argument used only as a fall-back.
    """
    # Thanks to Steven D'Aprano, http://www.velocityreviews.com/forums

    if os.name == "posix":
        # Unix, Linux, macOS, BSD, etc.
        os.system("clear")
    elif os.name in ("nt", "dos", "ce"):
        # DOS/Windows
        os.system("CLS")
    else:
        # Fallback for other operating systems.
        print("\n" * numlines)
