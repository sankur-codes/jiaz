import pytest
import configparser
from typer.testing import CliRunner
from pathlib import Path

from jiaz.cli import app as main_cli_app # Import the main Typer app
from jiaz.core.config_utils import encode_token, decode_token # decode_token is used by the list command itself
from tests.conftest import read_config_file_content, create_config_file_manually


def test_list_all_configs(runner: CliRunner, isolated_config_file: Path):
    create_config_file_manually(isolated_config_file, {
        'default': {'server_url': 'http://list.com'},
        'custom1': {'key': 'val1'},
        'meta': {'active_config': 'custom1'}
    })
    result = runner.invoke(main_cli_app, ["config", "list"])
    assert result.exit_code == 0
    assert "Available configurations:" in result.stdout
    assert "default" in result.stdout
    assert "custom1" in result.stdout
    assert "Active configuration: custom1" in result.stdout

def test_list_specific_config(runner: CliRunner, isolated_config_file: Path):
    token = "list_token"
    encoded_token = encode_token(token)
    create_config_file_manually(isolated_config_file, {
        'default': {'server_url': 'http://specific.com', 'user_token': encoded_token, 'project': 'XYZ'},
        'meta': {'active_config': 'default'}
    })
    result = runner.invoke(main_cli_app, ["config", "list", "--name", "default"])
    assert result.exit_code == 0
    assert "Configuration for 'default':" in result.stdout
    assert "server_url = http://specific.com" in result.stdout
    assert f"user_token = {token}" in result.stdout 
    assert "project = XYZ" in result.stdout

def test_list_specific_config_not_found(runner: CliRunner, isolated_config_file: Path):
    result = runner.invoke(main_cli_app, ["config", "list", "--name", "nonexistent"])
    assert result.exit_code == 0
    assert "Config 'nonexistent' not found." in result.stdout

def test_list_no_configs_found(runner: CliRunner, isolated_config_file: Path):
    create_config_file_manually(isolated_config_file, {
        'meta': {'active_config': 'default'}
    })
    result = runner.invoke(main_cli_app, ["config", "list"])
    assert result.exit_code == 0
    assert "No configuration found." in result.stdout

    if isolated_config_file.exists():
        isolated_config_file.unlink()
    result_no_file = runner.invoke(main_cli_app, ["config", "list"])
    assert result_no_file.exit_code == 0
    assert "No configuration found." in result_no_file.stdout