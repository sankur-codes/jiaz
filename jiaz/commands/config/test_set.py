import configparser
from pathlib import Path

from typer.testing import CliRunner

from jiaz.cli import app as main_cli_app  # Import the main Typer app
from jiaz.commands.conftest import create_config_file_manually
from jiaz.core.config_utils import (
    decode_secure_value,
)  # CONFIG_FILE not directly used here


def test_set_new_key(runner: CliRunner, isolated_config_file: Path):
    create_config_file_manually(
        isolated_config_file,
        {
            "default": {"server_url": "http://original.com"},
            "meta": {"active_config": "default"},
        },
    )
    result = runner.invoke(
        main_cli_app, ["config", "set", "new_key", "new_value", "--name", "default"]
    )
    assert result.exit_code == 0
    assert "Config added in 'default': new_key=new_value" in result.stdout
    cfg = configparser.ConfigParser()
    cfg.read(isolated_config_file)
    assert cfg["default"]["new_key"] == "new_value"


def test_set_update_key_active_config_confirm(
    runner: CliRunner, isolated_config_file: Path
):
    create_config_file_manually(
        isolated_config_file,
        {
            "default": {"server_url": "http://original.com"},
            "meta": {"active_config": "default"},
        },
    )
    result = runner.invoke(
        main_cli_app,
        ["config", "set", "server_url", "http://updated.com", "--name", "default"],
        input="y\n",
    )
    assert result.exit_code == 0
    assert "Config updated in 'default': server_url=http://updated.com" in result.stdout
    cfg = configparser.ConfigParser()
    cfg.read(isolated_config_file)
    assert cfg["default"]["server_url"] == "http://updated.com"


def test_set_update_key_active_config_abort(
    runner: CliRunner, isolated_config_file: Path
):
    create_config_file_manually(
        isolated_config_file,
        {
            "default": {"server_url": "http://original.com"},
            "meta": {"active_config": "default"},
        },
    )
    result = runner.invoke(
        main_cli_app,
        ["config", "set", "server_url", "http://updated.com", "--name", "default"],
        input="n\n",
    )
    assert result.exit_code != 0
    assert "Update aborted by user." in result.stdout
    cfg = configparser.ConfigParser()
    cfg.read(isolated_config_file)
    assert cfg["default"]["server_url"] == "http://original.com"


def test_set_update_key_non_active_config_no_confirm(
    runner: CliRunner, isolated_config_file: Path
):
    create_config_file_manually(
        isolated_config_file,
        {
            "default": {"server_url": "http://default.com"},
            "custom": {"server_url": "http://custom_original.com"},
            "meta": {"active_config": "default"},
        },
    )
    result = runner.invoke(
        main_cli_app,
        [
            "config",
            "set",
            "server_url",
            "http://custom_updated.com",
            "--name",
            "custom",
        ],
    )
    assert result.exit_code == 0
    assert (
        "Config updated in 'custom': server_url=http://custom_updated.com"
        in result.stdout
    )
    cfg = configparser.ConfigParser()
    cfg.read(isolated_config_file)
    assert cfg["custom"]["server_url"] == "http://custom_updated.com"


def test_set_user_token_encoded(runner: CliRunner, isolated_config_file: Path):
    create_config_file_manually(
        isolated_config_file, {"default": {}, "meta": {"active_config": "default"}}
    )
    result = runner.invoke(
        main_cli_app, ["config", "set", "user_token", "mysecret", "--name", "default"]
    )
    assert result.exit_code == 0
    cfg = configparser.ConfigParser()
    cfg.read(isolated_config_file)
    assert cfg["default"]["user_token"] != "mysecret"
    assert decode_secure_value(cfg["default"]["user_token"]) == "mysecret"


def test_set_no_name_uses_active_config(runner: CliRunner, isolated_config_file: Path):
    create_config_file_manually(
        isolated_config_file,
        {
            "activeconf": {"existing_key": "val1"},
            "otherconf": {"existing_key": "val2"},
            "meta": {"active_config": "activeconf"},
        },
    )
    result = runner.invoke(
        main_cli_app, ["config", "set", "existing_key", "new_val_active"], input="y\n"
    )
    assert result.exit_code == 0
    assert (
        "Config updated in 'activeconf': existing_key=new_val_active" in result.stdout
    )
    cfg = configparser.ConfigParser()
    cfg.read(isolated_config_file)
    assert cfg["activeconf"]["existing_key"] == "new_val_active"
    assert cfg["otherconf"]["existing_key"] == "val2"


def test_set_config_not_found(runner: CliRunner, isolated_config_file: Path):
    result = runner.invoke(
        main_cli_app, ["config", "set", "key", "value", "--name", "nonexistent"]
    )
    assert result.exit_code == 0
    assert "Config 'nonexistent' not found." in result.stdout


def test_set_cannot_modify_meta(runner: CliRunner, isolated_config_file: Path):
    create_config_file_manually(
        isolated_config_file, {"meta": {"active_config": "default"}}
    )
    result = runner.invoke(
        main_cli_app, ["config", "set", "some_key", "some_value", "--name", "meta"]
    )
    assert result.exit_code == 1
    assert "Cannot modify 'meta' block." in result.stdout
