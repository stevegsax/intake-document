"""
Configuration management for intake-document.

This module handles loading and managing configuration from files and
environment variables according to the XDG Base Directory specification.
"""

import configparser
import os
from pathlib import Path
from typing import Any, Dict, Optional

from xdg_base_dirs import xdg_config_home

from src.intake_document.models.settings import Settings


class Config:
    """Configuration manager for the application.

    Handles loading configuration from XDG-compliant locations and
    provides access to the application settings.
    """

    def __init__(self) -> None:
        """Initialize the configuration manager."""
        self._config_file = "init.cfg"
        self._app_name = "intake-document"
        self._settings: Optional[Settings] = None

    @property
    def settings(self) -> Settings:
        """Get the application settings.

        Returns:
            Settings: The application settings.
        """
        if self._settings is None:
            self._settings = self._load_settings()
        return self._settings

    def _get_config_path(self) -> Path:
        """Get the path to the configuration file.

        Returns:
            Path: The path to the configuration file.
        """
        config_dir = xdg_config_home() / self._app_name
        return config_dir / self._config_file

    def _load_settings(self) -> Settings:
        """Load settings from configuration files and environment variables.

        Returns:
            Settings: The application settings.
        """
        config_data: Dict[str, Any] = {}
        config_path = self._get_config_path()

        # Load configuration from file if it exists
        if config_path.exists():
            parser = configparser.ConfigParser()
            try:
                parser.read(str(config_path))
                config_data = {
                    s: dict(parser.items(s)) for s in parser.sections()
                }
            except Exception as e:
                raise ValueError(f"Error reading config file: {e}")

        # Override with environment variables
        mistral_api_key = os.environ.get("MISTRAL_API_KEY")
        if mistral_api_key:
            if "mistral" not in config_data:
                config_data["mistral"] = {}
            config_data["mistral"]["api_key"] = mistral_api_key

        # Convert the flat config structure to a settings object
        return Settings.model_validate(
            {
                "mistral": config_data.get("mistral", {}),
                "app": config_data.get("app", {}),
            }
        )

    def save_config(self) -> None:
        """Save the current configuration to the config file."""
        if self._settings is None:
            return

        config_path = self._get_config_path()
        config_path.parent.mkdir(parents=True, exist_ok=True)

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

        with open(config_path, "w") as f:
            parser.write(f)

    def show_config(self) -> Dict[str, Any]:
        """Get the current configuration as a dictionary.

        Returns:
            Dict[str, Any]: The current configuration.
        """
        return self._settings.model_dump() if self._settings else {}


# Global instance
config = Config()
