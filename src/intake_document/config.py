"""
Configuration management for intake-document.

This module handles loading and managing configuration from files and
environment variables according to the XDG Base Directory specification.
"""

import configparser
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

# Standard library imports first
# Third-party imports
from pydantic import ValidationError

# Local application imports
from intake_document.models.settings import Settings
from intake_document.utils.exceptions import ConfigError
from intake_document.utils.xdg import XDGPaths


class Config:
    """Configuration manager for the application.

    Handles loading configuration from XDG-compliant locations and
    provides access to the application settings.
    """

    def __init__(self) -> None:
        """Initialize the configuration manager."""
        self.logger = logging.getLogger(__name__)
        self._config_file = "init.cfg"
        self._app_name = "intake-document"
        self._settings: Optional[Settings] = None
        self._xdg = XDGPaths(self._app_name)

        self.logger.debug("Configuration manager initialized")

    @property
    def settings(self) -> Settings:
        """Get the application settings.

        Returns:
            Settings: The application settings.

        Raises:
            ConfigError: If settings cannot be loaded
        """
        if self._settings is None:
            self._settings = self._load_settings()
        return self._settings

    def _find_config_files(self) -> List[Path]:
        """Find all config files in XDG config directories.

        Returns:
            List[Path]: List of found config files, in order of precedence
        """
        self.logger.debug(
            f"Searching for config files named {self._config_file}"
        )
        found_files = []

        # Check user config directory first
        user_config = self._xdg.config_dir / self._config_file
        if user_config.exists() and user_config.is_file():
            self.logger.debug(f"Found user config file: {user_config}")
            found_files.append(user_config)

        # Then check system config directories
        for config_dir in self._xdg._config_dirs:
            system_config = config_dir / self._config_file
            if system_config.exists() and system_config.is_file():
                self.logger.debug(f"Found system config file: {system_config}")
                found_files.append(system_config)

        if not found_files:
            self.logger.debug("No config files found, will use defaults")

        return found_files

    def _get_config_path(self) -> Path:
        """Get the path to the user's configuration file.

        Returns:
            Path: The path to the configuration file.
        """
        config_path = self._xdg.config_dir / self._config_file
        self.logger.debug(f"User config path: {config_path}")
        return config_path

    def _load_settings(self) -> Settings:
        """Load settings from configuration files and environment variables.

        Returns:
            Settings: The application settings.

        Raises:
            ConfigError: If settings cannot be loaded or validated
        """
        self.logger.debug(
            "Loading settings from config files and environment variables"
        )

        # Start with empty config data
        config_data: Dict[str, Dict[str, Any]] = {
            "mistral": {},
            "app": {},
        }

        # Find all config files (user and system)
        config_files = self._find_config_files()

        # Load and merge configurations in order of precedence
        parser = configparser.ConfigParser()

        for config_path in config_files:
            try:
                self.logger.debug(f"Reading config file: {config_path}")
                parser.read(str(config_path))

                # Merge into our config data, section by section
                for section in parser.sections():
                    if section not in config_data:
                        config_data[section] = {}

                    # Add all keys from this section
                    for key, value in parser.items(section):
                        config_data[section][key] = value
                        self.logger.debug(
                            f"Loaded config: [{section}] {key}={value}"
                        )

            except Exception as e:
                error_msg = f"Error reading config file: {config_path}"
                self.logger.error(f"{error_msg}: {str(e)}")
                raise ConfigError(error_msg, detail=str(e))

        # Override with environment variables
        mistral_api_key = os.environ.get("MISTRAL_API_KEY")
        if mistral_api_key:
            self.logger.debug("Found MISTRAL_API_KEY in environment variables")
            config_data["mistral"]["api_key"] = mistral_api_key

        output_dir = os.environ.get("INTAKE_DOCUMENT_OUTPUT_DIR")
        if output_dir:
            self.logger.debug(
                f"Found INTAKE_DOCUMENT_OUTPUT_DIR in environment variables: {output_dir}"
            )
            config_data["app"]["output_dir"] = output_dir

        log_level = os.environ.get("INTAKE_DOCUMENT_LOG_LEVEL")
        if log_level:
            self.logger.debug(
                f"Found INTAKE_DOCUMENT_LOG_LEVEL in environment variables: {log_level}"
            )
            config_data["app"]["log_level"] = log_level

        # Convert the config structure to a settings object
        try:
            self.logger.debug("Validating settings with Pydantic")
            settings = Settings.model_validate(config_data)
            self.logger.info("Settings loaded and validated successfully")
            return settings
        except ValidationError as e:
            error_msg = "Settings validation failed"
            self.logger.error(f"{error_msg}: {str(e)}")
            raise ConfigError(error_msg, detail=str(e))

    def save_config(self) -> None:
        """Save the current configuration to the user config file.

        Raises:
            ConfigError: If configuration cannot be saved
        """
        if self._settings is None:
            self.logger.warning("No settings to save")
            return

        config_path = self._get_config_path()

        try:
            # Ensure the directory exists
            self.logger.debug(
                f"Creating config directory if needed: {config_path.parent}"
            )
            config_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)

            parser = configparser.ConfigParser()

            # Convert settings to sections
            settings_dict = self._settings.model_dump()
            for section, values in settings_dict.items():
                if not values:
                    continue

                parser.add_section(section)
                for key, value in values.items():
                    if value is not None:
                        parser[section][key] = str(value)

            self.logger.debug(f"Writing config to: {config_path}")
            with open(config_path, "w") as f:
                parser.write(f)

            self.logger.info(f"Configuration saved to {config_path}")

        except (OSError, PermissionError) as e:
            error_msg = f"Failed to save configuration to {config_path}"
            self.logger.error(f"{error_msg}: {str(e)}")
            raise ConfigError(error_msg, detail=str(e))

    def show_config(self) -> Dict[str, Any]:
        """Get the current configuration as a dictionary.

        Returns:
            Dict[str, Any]: The current configuration.
        """
        self.logger.debug("Returning current configuration as dictionary")
        return self._settings.model_dump() if self._settings else {}


# Global instance
config = Config()
