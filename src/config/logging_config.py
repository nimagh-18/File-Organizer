# src/config/logging_config.py

import sys
from pathlib import Path

from loguru import logger
from src.core.utils import find_project_root

# --- Config logur ---
# Remove default handlers to start with a clean slate
logger.remove()

# Configure Loguru to write to a log file
project_root: Path = find_project_root(Path(__file__))
log_dir: Path = project_root.joinpath("src/logs")

log_dir.mkdir(exist_ok=True)
log_path: Path = log_dir.joinpath("organizer.log")

logger.add(log_path, rotation="10 MB", compression="zip", encoding="utf-8")
logger.add(
    sys.stderr,
    level="WARNING",  # Only shows WARNING, ERROR, CRITICAL
)
