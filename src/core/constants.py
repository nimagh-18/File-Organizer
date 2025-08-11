import os
import platform
from functools import lru_cache
from pathlib import Path


class SystemProtector:
    def __init__(self, allowed_paths_config: dict[str, str]) -> None:
        system = platform.system().lower()

        if system == "linux":
            paths = allowed_paths_config.get("linux", [])
        elif system == "darwin":  # macOS
            paths = allowed_paths_config.get("mac", [])
        elif system == "windows":
            paths = allowed_paths_config.get("windows", [])
        else:
            paths = []

        self._allowed_paths: frozenset[Path] = frozenset(self._resolve_paths(paths))

    def _resolve_paths(self, paths: list[str]) -> list[Path]:
        """Expands environment variables and resolves paths."""
        resolved: list[Path] = []

        for path_str in paths:
            # Expand environment variables like %USERPROFILE%
            expanded_path_str = os.path.expandvars(path_str)
            resolved.append(Path(expanded_path_str).resolve())
        return resolved

    @lru_cache(maxsize=1024)
    def is_allowed(self, path: Path) -> bool:
        """
        Check if a path is a subdirectory of any of the allowed paths.
        The home directory is always allowed by default.
        """
        try:
            abs_path = path.resolve().absolute()
            home_dir = Path.home().resolve().absolute()

            # The home directory itself and its subdirectories are always allowed by default
            if abs_path == home_dir:
                return False

            # Check if the path is a subdirectory of any allowed path
            for allowed_path in self._allowed_paths:
                if abs_path.is_relative_to(allowed_path):
                    return True

            return False
        except Exception as e:
            # logger.error(f"Path validation error for '{path}': {e}")
            return False  # Fail-safe, assume not allowed
