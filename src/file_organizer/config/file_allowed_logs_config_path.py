from pathlib import Path

from file_organizer.core.utils import find_project_root

default_allowed_path: Path = Path("src/file_organizer/config/allowed_path.yaml")
file_categories_path: Path = Path("src/file_organizer/config/file_categories.yaml")

# Configure Loguru to write to a log file
_project_root: Path = find_project_root(Path(__file__))
log_dir: Path = _project_root.joinpath(Path("logs"))
