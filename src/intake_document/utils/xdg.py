"""XDG Base Directory utilities."""

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

from xdg_base_dirs import (
    xdg_cache_home,
    xdg_config_dirs,
    xdg_config_home,
    xdg_data_dirs,
    xdg_data_home,
    xdg_state_home,
)

from intake_document.utils.exceptions import XDGError


class XDGPaths:
    """Helper class for XDG Base Directory paths."""

    def __init__(self, app_name: str) -> None:
        """Initialize the XDG paths for the application.

        Args:
            app_name: The name of the application
        """
        self.logger = logging.getLogger(__name__)
        self.app_name = app_name

        # Initialize XDG base directories
        self._config_dir = xdg_config_home() / app_name
        self._data_dir = xdg_data_home() / app_name
        self._cache_dir = xdg_cache_home() / app_name
        self._state_dir = xdg_state_home() / app_name

        # Get additional config and data directories
        self._config_dirs = [Path(d) / app_name for d in xdg_config_dirs()]
        self._data_dirs = [Path(d) / app_name for d in xdg_data_dirs()]

        # Runtime directory support
        self._runtime_dir = self._get_runtime_dir() / app_name

        self.logger.debug(f"Initialized XDG paths for {app_name}")

    def _get_runtime_dir(self) -> Path:
        """Get the XDG runtime directory, with fallback.

        Returns:
            Path: The runtime directory

        Raises:
            XDGError: If runtime directory couldn't be determined or created
        """
        runtime_dir = os.environ.get("XDG_RUNTIME_DIR")

        if runtime_dir:
            path = Path(runtime_dir)
            if not path.exists():
                self.logger.warning(
                    f"XDG_RUNTIME_DIR exists but points to non-existent path: {path}"
                )
                # Fall back to cache dir as per XDG spec
                self.logger.info(
                    "Falling back to XDG_CACHE_HOME for runtime files"
                )
                return xdg_cache_home()
            return path

        # XDG spec says we should fall back to a similar capability dir and warn
        self.logger.warning(
            "XDG_RUNTIME_DIR not set, falling back to XDG_CACHE_HOME"
        )
        return xdg_cache_home()

    def ensure_directories(self) -> None:
        """Ensure all XDG directories exist.

        Raises:
            XDGError: If any directory cannot be created
        """
        dirs_to_create = [
            (self.config_dir, "config"),
            (self.data_dir, "data"),
            (self.cache_dir, "cache"),
            (self.state_dir, "state"),
            (self.runtime_dir, "runtime"),
        ]

        for directory, dir_type in dirs_to_create:
            try:
                self.logger.debug(
                    f"Ensuring {dir_type} directory exists: {directory}"
                )
                directory.mkdir(parents=True, exist_ok=True, mode=0o700)
            except (OSError, PermissionError) as e:
                error_msg = (
                    f"Failed to create {dir_type} directory at {directory}"
                )
                self.logger.error(f"{error_msg}: {str(e)}")
                raise XDGError(error_msg, detail=str(e))

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

    @property
    def runtime_dir(self) -> Path:
        """Get the runtime directory for the application.

        Returns:
            Path: The runtime directory
        """
        return self._runtime_dir

    @property
    def config_dirs(self) -> List[Path]:
        """Get all config directories in order of preference.

        Returns:
            List[Path]: List of config directories
        """
        # XDG spec: user config dir takes precedence over system dirs
        return [self.config_dir] + self._config_dirs

    @property
    def data_dirs(self) -> List[Path]:
        """Get all data directories in order of preference.

        Returns:
            List[Path]: List of data directories
        """
        # XDG spec: user data dir takes precedence over system dirs
        return [self.data_dir] + self._data_dirs

    def get_all_paths(self) -> Dict[str, Path]:
        """Get all primary XDG paths for the application.

        Returns:
            Dict[str, Path]: A dictionary mapping path types to paths
        """
        return {
            "config": self.config_dir,
            "data": self.data_dir,
            "cache": self.cache_dir,
            "state": self.state_dir,
            "runtime": self.runtime_dir,
        }

    def find_config_file(self, filename: str) -> Optional[Path]:
        """Find a config file by checking all config directories in order.

        Args:
            filename: The name of the configuration file to find

        Returns:
            Optional[Path]: Path to the first matching file, or None if not found
        """
        self.logger.debug(f"Searching for config file: {filename}")

        # Check each config directory in order of preference
        for config_dir in self.config_dirs:
            file_path = config_dir / filename
            if file_path.exists() and file_path.is_file():
                self.logger.debug(f"Found config file at: {file_path}")
                return file_path

        self.logger.debug(
            f"Config file '{filename}' not found in any config directory"
        )
        return None

    def find_data_file(self, filename: str) -> Optional[Path]:
        """Find a data file by checking all data directories in order.

        Args:
            filename: The name of the data file to find

        Returns:
            Optional[Path]: Path to the first matching file, or None if not found
        """
        self.logger.debug(f"Searching for data file: {filename}")

        # Check each data directory in order of preference
        for data_dir in self.data_dirs:
            file_path = data_dir / filename
            if file_path.exists() and file_path.is_file():
                self.logger.debug(f"Found data file at: {file_path}")
                return file_path

        self.logger.debug(
            f"Data file '{filename}' not found in any data directory"
        )
        return None
