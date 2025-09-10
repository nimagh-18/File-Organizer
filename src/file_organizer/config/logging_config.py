# src/config/logging_config.py

import sys
from pathlib import Path

from loguru import logger

from file_organizer.config.file_allowed_logs_config_path import log_dir

# --- Config logur ---
# Remove default handlers to start with a clean slate
logger.remove()


log_dir.mkdir(exist_ok=True)
log_path: Path = log_dir.joinpath("organizer.log")

logger.add(log_path, rotation="10 MB", compression="zip", encoding="utf-8")
logger.add(
    sys.stderr,
    level="WARNING",  # Only shows WARNING, ERROR, CRITICAL
)
