import logging
import platform
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)


class SystemProtector:
    """Smart system directory protection with home directory exceptions."""

    def __init__(self) -> None:
        self.home_dir: Path = Path.home()
        self.system: str = platform.system().lower()

        # Comprehensive list of protected core system paths
        self._core_protected: frozenset[Path] = frozenset(
            {
                # Generic Linux/macOS paths
                Path("/"),
                Path("/bin"),
                Path("/sbin"),
                Path("/usr"),
                Path("/etc"),
                Path("/var"),
                Path("/root"),
                Path("/dev"),
                Path("/proc"),
                Path("/sys"),
                Path("/boot"),
                # macOS specific
                Path("/System"),
                Path("/Library"),
                Path("/Applications"),
                # Windows specific
                Path("C:\\Windows"),
                Path("C:\\Program Files"),
                Path("C:\\Program Files (x86)"),
                Path("C:\\ProgramData"),
                Path("C:\\$Recycle.Bin"),
            }
        )

        # Sensitive hidden directory names (regardless of location)
        self._protected_hidden: frozenset[str] = frozenset(
            {
                ".config",
                ".local",
                ".cache",
                ".ssh",
                ".gnupg",
                ".pki",
                ".npm",
                ".docker",
                ".git",
                ".svn",
                ".venv",
                ".env",
                ".bashrc",
                ".zshrc",
                ".bash_profile",
                ".profile",
                ".vim",
            }
        )

    @lru_cache(maxsize=1024)
    def is_protected(self, path: Path) -> bool:
        """
        Check if path is protected.
        - Core system paths are always protected.
        - The home directory itself is protected.
        - Sensitive hidden directories are protected, even inside home.
        - Other directories inside home are not protected.
        """
        try:
            abs_path = path.resolve().absolute()

            # Check if the home directory itself is the target
            if abs_path == self.home_dir:
                return True

            # Check if the path is inside the home directory
            if abs_path.is_relative_to(self.home_dir):
                # If it's inside home, check if any part of the path is a protected hidden directory
                for part in abs_path.parts:
                    if part in self._protected_hidden:
                        return True
                return False  # Not protected, since it's in home and not a sensitive hidden dir

            # Check if the path starts with any of the core protected paths
            for protected_path in self._core_protected:
                if abs_path.is_relative_to(protected_path):
                    return True

            return False

        except Exception as e:
            logger.error(f"Path validation error for '{path}': {e}")
            return True  # Fail safe to prevent accidental damage
