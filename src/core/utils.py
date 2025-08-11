from pathlib import Path


# pyproject.tomlFind the root of the project by searching the pyproject.toml file
def find_project_root(file_path: Path) -> Path:
    current_path = file_path

    while not (current_path.joinpath("pyproject.toml")).exists():
        if current_path == current_path.parent:  # prevent infinite loop
            raise FileNotFoundError("Could not find project root with pyproject.toml")

        current_path: Path = current_path.parent

    return current_path
