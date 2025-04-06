"""Tests for the XDG utility functions."""

from pathlib import Path
from unittest.mock import patch

from src.intake_document.utils.xdg import XDGPaths


@patch("src.intake_document.utils.xdg.xdg_config_home")
@patch("src.intake_document.utils.xdg.xdg_data_home")
@patch("src.intake_document.utils.xdg.xdg_cache_home")
@patch("src.intake_document.utils.xdg.xdg_state_home")
def test_xdg_paths(mock_state, mock_cache, mock_data, mock_config):
    """Test that XDGPaths correctly uses the XDG base directories."""
    # Set up mock return values
    mock_config.return_value = Path("/home/user/.config")
    mock_data.return_value = Path("/home/user/.local/share")
    mock_cache.return_value = Path("/home/user/.cache")
    mock_state.return_value = Path("/home/user/.local/state")

    # Create XDGPaths
    app_name = "test-app"
    paths = XDGPaths(app_name)

    # Check that paths are correct
    assert paths.config_dir == Path("/home/user/.config/test-app")
    assert paths.data_dir == Path("/home/user/.local/share/test-app")
    assert paths.cache_dir == Path("/home/user/.cache/test-app")
    assert paths.state_dir == Path("/home/user/.local/state/test-app")


@patch("pathlib.Path.mkdir")
def test_ensure_directories(mock_mkdir):
    """Test that ensure_directories creates all directories."""
    # Create XDGPaths with mocked base directories
    paths = XDGPaths("test-app")

    # Call ensure_directories
    paths.ensure_directories()

    # Check that mkdir was called for each directory
    assert mock_mkdir.call_count == 4
    for call in mock_mkdir.call_args_list:
        kwargs = call[1]
        assert kwargs["parents"] is True
        assert kwargs["exist_ok"] is True


def test_get_all_paths():
    """Test that get_all_paths returns the correct dictionary."""
    # Create XDGPaths with attributes set directly
    paths = XDGPaths("test-app")
    paths._config_dir = Path("/config/test-app")
    paths._data_dir = Path("/data/test-app")
    paths._cache_dir = Path("/cache/test-app")
    paths._state_dir = Path("/state/test-app")

    # Get all paths
    all_paths = paths.get_all_paths()

    # Check dictionary
    assert all_paths["config"] == Path("/config/test-app")
    assert all_paths["data"] == Path("/data/test-app")
    assert all_paths["cache"] == Path("/cache/test-app")
    assert all_paths["state"] == Path("/state/test-app")
