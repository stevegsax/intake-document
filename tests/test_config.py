"""Tests for the configuration module."""

import os
from unittest.mock import patch

from src.intake_document.config import Config
from src.intake_document.models.settings import Settings


def test_config_defaults():
    """Test that the config manager returns default settings when no config exists."""
    config = Config()
    settings = config.settings

    # Check default values
    assert settings.mistral.api_key is None
    assert settings.mistral.batch_size == 5
    assert settings.mistral.max_retries == 3
    assert settings.app.output_dir == "./output"
    assert settings.app.log_level == "ERROR"


@patch.dict(os.environ, {"MISTRAL_API_KEY": "test-api-key"}, clear=True)
def test_config_env_vars():
    """Test that environment variables override default settings."""
    config = Config()
    settings = config.settings

    # Check that environment variable was used
    assert settings.mistral.api_key == "test-api-key"

    # Other settings should still have defaults
    assert settings.mistral.batch_size == 5
    assert settings.app.output_dir == "./output"


def test_show_config():
    """Test that the show_config method returns the correct dictionary."""
    config = Config()

    # Mock the settings
    config._settings = Settings(
        mistral={"api_key": "test-key", "batch_size": 10},
        app={"output_dir": "/test/dir"},
    )

    # Get the config dict
    config_dict = config.show_config()

    # Check values
    assert config_dict["mistral"]["api_key"] == "test-key"
    assert config_dict["mistral"]["batch_size"] == 10
    assert config_dict["app"]["output_dir"] == "/test/dir"
