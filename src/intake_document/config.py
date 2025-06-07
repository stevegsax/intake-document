"""Simplified configuration management for intake-document."""

import configparser
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import ValidationError

from intake_document.models.settings import Settings
from intake_document.utils.exceptions import ConfigError


class Config:
    """Simplified configuration manager for the application."""

    def __init__(self) -> None:
        """Initialize the configuration manager."""
        self.logger = logging.getLogger(__name__)
        self._config_file = "intake-document.cfg"
        self._settings: Optional[Settings] = None

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

    def _get_config_path(self) -> Path:
        """Get the path to the configuration file.

        Returns:
            Path: The path to the configuration file.
        """
        # Check environment variable first
        config_path_env = os.environ.get("INTAKE_DOCUMENT_CONFIG")
        if config_path_env:
            return Path(config_path_env)
        
        # Default to user home directory
        return Path.home() / f".{self._config_file}"

    def _load_settings(self) -> Settings:
        """Load settings from config file and environment variables.

        Returns:
            Settings: The application settings.

        Raises:
            ConfigError: If settings cannot be loaded or validated
        """
        self.logger.debug("Loading settings from config file and environment variables")

        # Start with empty config data
        config_data: Dict[str, Dict[str, Any]] = {
            "mistral": {},
            "app": {},
        }

        # Try to load config file
        config_path = self._get_config_path()
        if config_path.exists():
            try:
                self.logger.debug(f"Reading config file: {config_path}")
                parser = configparser.ConfigParser()
                parser.read(str(config_path))

                # Load sections
                for section in parser.sections():
                    if section not in config_data:
                        config_data[section] = {}
                    for key, value in parser.items(section):
                        config_data[section][key] = value
                        
            except Exception as e:
                error_msg = f"Error reading config file: {config_path}"
                self.logger.error(f"{error_msg}: {str(e)}")
                raise ConfigError(error_msg, detail=str(e))
        else:
            self.logger.debug("No config file found, using environment variables and defaults")

        # Override with environment variables (higher priority)
        env_vars = {
            "MISTRAL_API_KEY": ("mistral", "api_key"),
            "INTAKE_DOCUMENT_OUTPUT_DIR": ("app", "output_dir"),
            "INTAKE_DOCUMENT_LOG_LEVEL": ("app", "log_level"),
        }
        
        for env_var, (section, key) in env_vars.items():
            value = os.environ.get(env_var)
            if value:
                config_data[section][key] = value
                self.logger.debug(f"Using environment variable {env_var}")

        # Validate and create settings
        try:
            settings = Settings.model_validate(config_data)
            self.logger.info("Settings loaded and validated successfully")
            return settings
        except ValidationError as e:
            error_msg = "Settings validation failed"
            self.logger.error(f"{error_msg}: {str(e)}")
            raise ConfigError(error_msg, detail=str(e))

    def save_config(self) -> None:
        """Save the current configuration to config file.

        Raises:
            ConfigError: If configuration cannot be saved
        """
        if self._settings is None:
            self.logger.warning("No settings to save")
            return

        config_path = self._get_config_path()

        try:
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