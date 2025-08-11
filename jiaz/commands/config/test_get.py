from typer.testing import CliRunner
from pathlib import Path

from jiaz.cli import app as main_cli_app # Import the main Typer app
from jiaz.core.config_utils import encode_secure_value # CONFIG_FILE is not directly used here
from jiaz.commands.conftest import create_config_file_manually

# Remove the local definition of create_config_file_manually as it's imported from conftest

def test_get_existing_key(runner: CliRunner, isolated_config_file: Path):
    create_config_file_manually(isolated_config_file, {
        'default': {'server_url': 'http://getme.com'},
        'meta': {'active_config': 'default'}
    })
    result = runner.invoke(main_cli_app, ["config", "get", "server_url", "--name", "default"])
    assert result.exit_code == 0
    assert "http://getme.com" in result.stdout.strip()

def test_get_user_token_decoded(runner: CliRunner, isolated_config_file: Path):
    encoded = encode_secure_value("mysecrettoken")
    create_config_file_manually(isolated_config_file, {
        'default': {'user_token': encoded},
        'meta': {'active_config': 'default'}
    })
    result = runner.invoke(main_cli_app, ["config", "get", "user_token", "--name", "default"])
    assert result.exit_code == 0
    assert "mysecrettoken" == result.stdout.strip()

def test_get_key_not_found(runner: CliRunner, isolated_config_file: Path):
    create_config_file_manually(isolated_config_file, {
        'default': {'server_url': 'http://getme.com'},
        'meta': {'active_config': 'default'}
    })
    result = runner.invoke(main_cli_app, ["config", "get", "nonexistentkey", "--name", "default"])
    assert result.exit_code == 0 # Command echoes, doesn't fail
    assert "Key 'nonexistentkey' not found in config 'default'." in result.stdout

def test_get_config_not_found(runner: CliRunner, isolated_config_file: Path):
    # No need to create a file if we're testing a non-existent config block
    result = runner.invoke(main_cli_app, ["config", "get", "server_url", "--name", "nonexistent"])
    assert result.exit_code == 0
    assert "Key 'server_url' not found in config 'nonexistent'." in result.stdout

def test_get_no_name_uses_active_config(runner: CliRunner, isolated_config_file: Path):
    create_config_file_manually(isolated_config_file, {
        'activeconf': {'the_key': 'active_value'},
        'otherconf': {'the_key': 'other_value'},
        'meta': {'active_config': 'activeconf'}
    })
    result = runner.invoke(main_cli_app, ["config", "get", "the_key"]) # No --name
    assert result.exit_code == 0
    assert "active_value" == result.stdout.strip()

    # Check it doesn't get from otherconf
    create_config_file_manually(isolated_config_file, { # Recreate for a clean state
        'activeconf': {'another_key': 'val'}, # the_key not in active
        'otherconf': {'the_key': 'other_value'},
        'meta': {'active_config': 'activeconf'}
    })
    result = runner.invoke(main_cli_app, ["config", "get", "the_key"]) # No --name
    assert result.exit_code == 0
    assert "Key 'the_key' not found in config 'activeconf'." in result.stdout
