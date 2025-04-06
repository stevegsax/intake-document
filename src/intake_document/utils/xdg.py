"""XDG Base Directory utilities."""

from pathlib import Path
from typing import Dict

from xdg_base_dirs import (
    xdg_cache_home,
    xdg_config_home,
    xdg_data_home,
    xdg_state_home,
)


class XDGPaths:
    """Helper class for XDG Base Directory paths."""

    def __init__(self, app_name: str) -> None:
        """Initialize the XDG paths for the application.

        Args:
            app_name: The name of the application
        """
        self.app_name = app_name
        self._config_dir = xdg_config_home() / app_name
        self._data_dir = xdg_data_home() / app_name
        self._cache_dir = xdg_cache_home() / app_name
        self._state_dir = xdg_state_home() / app_name

    def ensure_directories(self) -> None:
        """Ensure all XDG directories exist."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.state_dir.mkdir(parents=True, exist_ok=True)

    @property
    def config_dir(self) -> Path:
        """Get the config directory for the application.

        Returns:
            Path: The config directory
        """
        return self._config_dir

    @property
    def data_dir(self) -> Path:
        """Get the data directory for the application.

        Returns:
            Path: The data directory
        """
        return self._data_dir

    @property
    def cache_dir(self) -> Path:
        """Get the cache directory for the application.

        Returns:
            Path: The cache directory
        """
        return self._cache_dir

    @property
    def state_dir(self) -> Path:
        """Get the state directory for the application.

        Returns:
            Path: The state directory
        """
        return self._state_dir

    def get_all_paths(self) -> Dict[str, Path]:
        """Get all XDG paths for the application.

        Returns:
            Dict[str, Path]: A dictionary mapping path types to paths
        """
        return {
            "config": self.config_dir,
            "data": self.data_dir,
            "cache": self.cache_dir,
            "state": self.state_dir,
        }
