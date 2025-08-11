import configparser
from typer.testing import CliRunner
from pathlib import Path

from jiaz.cli import app as main_cli_app
from jiaz.core.config_utils import encode_secure_value, decode_secure_value
from jiaz.commands.conftest import read_config_file_content, create_config_file_manually

def test_init_no_existing_config(runner: CliRunner, isolated_config_file: Path, monkeypatch):
    # Prompts: server_url, user_token, jira_project, jira_backlog_name, jira_sprintboard_name, jira_sprintboard_id, jira_board_name, gemini_api_key
    inputs = iter([
        "http://myjira.com", "test_token", "projA", "", "sprintX", "", "", ""  # Empty string for Gemini API key
    ])
    monkeypatch.setattr("typer.prompt", lambda *args, **kwargs: next(inputs))
    result = runner.invoke(main_cli_app, ["config", "init"])
    assert result.exit_code == 0
    assert "Default configuration set and active." in result.stdout
    assert isolated_config_file.exists()
    cfg = configparser.ConfigParser()
    cfg.read(isolated_config_file)
    assert 'default' in cfg
    assert cfg['default']['server_url'] == 'http://myjira.com'
    assert decode_secure_value(cfg['default']['user_token']) == 'test_token'
    assert cfg['default']['jira_project'] == 'projA'
    assert 'jira_backlog_name' not in cfg['default']
    assert cfg['default']['jira_sprintboard_name'] == 'sprintX'
    assert cfg['meta']['active_config'] == 'default'

def test_init_existing_config_add_new_block(runner: CliRunner, isolated_config_file: Path, monkeypatch):
    create_config_file_manually(isolated_config_file, {
        'default': {'server_url': 'http://default.com', 'user_token': encode_secure_value('default_token')},
        'meta': {'active_config': 'default'}
    })
    initial_content = read_config_file_content(isolated_config_file)
    # Prompts: new_config_name, server_url, user_token, jira_project, jira_backlog_name, jira_sprintboard_name, jira_sprintboard_id, jira_board_name, gemini_api_key
    inputs = iter([
        "new_config", "http://newjira.com", "new_token", "projB", "backlogY", "", "", "", ""  # Empty string for Gemini API key
    ])
    monkeypatch.setattr("typer.prompt", lambda *args, **kwargs: next(inputs))
    result = runner.invoke(main_cli_app, ["config", "init"])
    assert result.exit_code == 0
    assert "New configuration block 'new_config' added." in result.stdout
    cfg = configparser.ConfigParser()
    cfg.read(isolated_config_file)
    assert 'new_config' in cfg
    assert cfg['new_config']['server_url'] == 'http://newjira.com'
    assert decode_secure_value(cfg['new_config']['user_token']) == 'new_token'
    assert 'default' in cfg
    final_content = read_config_file_content(isolated_config_file)
    assert "# WARNING: Do not edit this config file manually." in final_content
    assert initial_content.splitlines()[0] in final_content

def test_init_config_name_conflict(runner: CliRunner, isolated_config_file: Path, monkeypatch):
    create_config_file_manually(isolated_config_file, {
        'default': {'server_url': 'http://default.com'},
        'meta': {'active_config': 'default'}
    })
    prompt_values = iter(["default"])
    monkeypatch.setattr("typer.prompt", lambda *args, **kwargs: next(prompt_values))
    result = runner.invoke(main_cli_app, ["config", "init"])
    assert result.exit_code == 1
    assert "Config name 'default' already exists." in result.stdout

def test_init_fallback_and_required_prompts(runner: CliRunner, isolated_config_file: Path, monkeypatch):
    create_config_file_manually(isolated_config_file, {
        'default': {'server_url': 'http://default.com', 'user_token': encode_secure_value('default_token_val')},
        'meta': {'active_config': 'default'}
    })
    # Fallback for server_url
    inputs_fallback_server = iter([
        "fallback_server_test", "", "new_specific_token", "", "", "", "", "", ""  # Empty string for Gemini API key
    ])
    monkeypatch.setattr("typer.prompt", lambda *args, **kwargs: next(inputs_fallback_server))
    result = runner.invoke(main_cli_app, ["config", "init"])
    assert result.exit_code == 0
    cfg = configparser.ConfigParser()
    cfg.read(isolated_config_file)
    assert cfg['fallback_server_test']['server_url'] == 'http://default.com'
    assert decode_secure_value(cfg['fallback_server_test']['user_token']) == 'new_specific_token'
    # Fallback for token
    inputs_fallback_token = iter([
        "fallback_token_test", "http://new_server.com", "", "", "", "", "", "", ""  # Empty string for Gemini API key
    ])
    monkeypatch.setattr("typer.prompt", lambda *args, **kwargs: next(inputs_fallback_token))
    result = runner.invoke(main_cli_app, ["config", "init"])
    assert result.exit_code == 0
    cfg.read(isolated_config_file)
    assert cfg['fallback_token_test']['server_url'] == 'http://new_server.com'
    assert decode_secure_value(cfg['fallback_token_test']['user_token']) == 'default_token_val'
    # Required prompt for token (no fallback)
    create_config_file_manually(isolated_config_file, {
        'default': {'server_url': 'http://another.com'},
        'meta': {'active_config': 'default'}
    })
    # Prompts: config_name, server_url (empty, fallback), user_token (empty, triggers required), required prompt 1 (empty), required prompt 2 (empty), required prompt 3 (actual value), jira_project, jira_backlog_name, jira_sprintboard_name, jira_sprintboard_id, jira_board_name, gemini_api_key
    prompts_required = iter([
        "required_token_block",  # config_name
        "",                      # server_url (empty, fallback)
        "",                      # user_token (empty, triggers required)
        "",                      # required prompt 1 (empty)
        "",                      # required prompt 2 (empty)
        "actual_required_token_val",  # required prompt 3 (actual value)
        "", "", "", "", "",      # optional fields
        ""                       # gemini_api_key (empty)
    ])
    monkeypatch.setattr("typer.prompt", lambda *args, **kwargs: next(prompts_required))
    result = runner.invoke(main_cli_app, ["config", "init"])
    assert result.exit_code == 0
    cfg.read(isolated_config_file)
    assert cfg['required_token_block']['server_url'] == 'http://another.com'
    assert decode_secure_value(cfg['required_token_block']['user_token']) == 'actual_required_token_val'
