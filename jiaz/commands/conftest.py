import pytest
import tempfile
from pathlib import Path
import configparser
from typer.testing import CliRunner

# Import the module where CONFIG_DIR and CONFIG_FILE are defined
from jiaz.core import config_utils as core_config_utils_module
from jiaz.commands.config import init as config_init_module # For prepend_warning_to_config

@pytest.fixture
def runner():
    return CliRunner()

@pytest.fixture
def mock_config_parser(monkeypatch):
    """Fixture to mock configparser.ConfigParser methods if needed directly."""
    mock_cp = configparser.ConfigParser()
    # If you need to mock its instantiation:
    # monkeypatch.setattr(configparser, 'ConfigParser', lambda: mock_cp)
    return mock_cp

@pytest.fixture(autouse=True)
def isolated_config_file(monkeypatch):
    """
    Fixture to create an isolated config directory and file for each test.
    It patches CONFIG_DIR and CONFIG_FILE in jiaz.core.config_utils.
    """
    with tempfile.TemporaryDirectory() as temp_dir_name:
        temp_dir_path = Path(temp_dir_name)
        temp_config_file_path = temp_dir_path / "config"

        # Patch the constants in the core.config_utils module
        monkeypatch.setattr(core_config_utils_module, "CONFIG_DIR", temp_dir_path)
        monkeypatch.setattr(core_config_utils_module, "CONFIG_FILE", temp_config_file_path)
        
        # Also patch for prepend_warning_to_config if it uses a different import path,
        # though it should rely on core_config_utils.
        # Ensure prepend_warning_to_config in init module also sees the patched path
        # This might not be strictly necessary if it correctly uses the patched core_config_utils.CONFIG_FILE
        # but good for robustness if there are direct references.
        # monkeypatch.setattr(config_init_module, "CONFIG_FILE", temp_config_file_path) # If init.py had its own CONFIG_FILE

        yield temp_config_file_path

# Helper function to create a config file for testing
def create_config_file_manually(config_path: Path, content: dict):
    parser = configparser.ConfigParser()
    for section, options in content.items():
        parser[section] = options
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, 'w') as f:
        parser.write(f)

# Helper to read config file content for assertions
def read_config_file_content(config_path: Path) -> str:
    if not config_path.exists():
        return ""
    with open(config_path, 'r') as f:
        return f.read()
