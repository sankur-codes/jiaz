import pytest
import configparser
from typer.testing import CliRunner
from pathlib import Path

from jiaz.cli import app as main_cli_app # Import the main Typer app
# CONFIG_FILE is not directly used here, core_config_utils is patched by conftest
from tests.conftest import read_config_file_content, create_config_file_manually


def test_use_set_active_config(runner: CliRunner, isolated_config_file: Path):
    create_config_file_manually(isolated_config_file, {
        'default': {'server_url': 'http://default.com'},
        'custom': {'server_url': 'http://custom.com'},
        'meta': {'active_config': 'default'}
    })
    result = runner.invoke(main_cli_app, ["config", "use", "custom"])
    assert result.exit_code == 0
    assert "Active configuration set to 'custom'." in result.stdout
    cfg = configparser.ConfigParser()
    cfg.read(isolated_config_file)
    assert cfg['meta']['active_config'] == 'custom'

def test_use_config_not_found(runner: CliRunner, isolated_config_file: Path):
    create_config_file_manually(isolated_config_file, {
        'default': {'server_url': 'http://default.com'},
        'meta': {'active_config': 'default'}
    })
    result = runner.invoke(main_cli_app, ["config", "use", "nonexistent"])
    assert result.exit_code == 0 
    assert "Config 'nonexistent' not found." in result.stdout
    cfg = configparser.ConfigParser()
    cfg.read(isolated_config_file)
    assert cfg['meta']['active_config'] == 'default' 