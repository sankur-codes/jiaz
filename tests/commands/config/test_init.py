import pytest
import configparser
from typer.testing import CliRunner
from pathlib import Path

from jiaz.cli import app as main_cli_app
from jiaz.core.config_utils import encode_token, decode_token, prepend_warning_to_config
from tests.conftest import read_config_file_content, create_config_file_manually


def test_init_no_existing_config(runner: CliRunner, isolated_config_file: Path, monkeypatch):
    # Prompts: server_url, user_token, jira_project, jira_backlog_name, jira_sprintboard_name
    inputs = iter(["http://myjira.com", "test_token", "projA", "", "sprintX"])
    monkeypatch.setattr("typer.prompt", lambda *args, **kwargs: next(inputs))

    result = runner.invoke(main_cli_app, ["config", "init"])

    assert result.exit_code == 0
    assert "Default configuration set and active." in result.stdout
    assert isolated_config_file.exists()

    cfg = configparser.ConfigParser()
    cfg.read(isolated_config_file)
    assert 'default' in cfg
    assert cfg['default']['server_url'] == 'http://myjira.com'
    assert decode_token(cfg['default']['user_token']) == 'test_token'
    assert cfg['default']['jira_project'] == 'projA'
    assert 'jira_backlog_name' not in cfg['default']
    assert cfg['default']['jira_sprintboard_name'] == 'sprintX'
    assert cfg['meta']['active_config'] == 'default'
    
def test_init_existing_config_add_new_block(runner: CliRunner, isolated_config_file: Path, monkeypatch):
    create_config_file_manually(isolated_config_file, {
        'default': {'server_url': 'http://default.com', 'user_token': encode_token('default_token')},
        'meta': {'active_config': 'default'}
    })
    initial_content = read_config_file_content(isolated_config_file) 

    # Prompts: new_config_name, server_url, user_token, jira_project, jira_backlog_name, jira_sprintboard_name
    inputs = iter(["new_config", "http://newjira.com", "new_token", "projB", "backlogY", ""])
    monkeypatch.setattr("typer.prompt", lambda *args, **kwargs: next(inputs))

    result = runner.invoke(main_cli_app, ["config", "init"])

    assert result.exit_code == 0
    assert "New configuration block 'new_config' added." in result.stdout

    cfg = configparser.ConfigParser()
    cfg.read(isolated_config_file)
    assert 'new_config' in cfg
    assert cfg['new_config']['server_url'] == 'http://newjira.com'
    assert decode_token(cfg['new_config']['user_token']) == 'new_token'
    assert 'default' in cfg 

    final_content = read_config_file_content(isolated_config_file)
    assert "# WARNING: Do not edit this config file manually." in final_content
    assert initial_content.splitlines()[0] in final_content

def test_init_config_name_conflict(runner: CliRunner, isolated_config_file: Path, monkeypatch):
    create_config_file_manually(isolated_config_file, {
        'default': {'server_url': 'http://default.com'},
        'meta': {'active_config': 'default'}
    })
    # Only one prompt for config name needed before exit
    prompt_values = iter(["default"]) 
    monkeypatch.setattr("typer.prompt", lambda *args, **kwargs: next(prompt_values))

    result = runner.invoke(main_cli_app, ["config", "init"])
    assert result.exit_code == 1
    assert "Config name 'default' already exists." in result.stdout

def test_init_fallback_and_required_prompts(runner: CliRunner, isolated_config_file: Path, monkeypatch):
    create_config_file_manually(isolated_config_file, {
        'default': {'server_url': 'http://default.com', 'user_token': encode_token('default_token_val')},
        'meta': {'active_config': 'default'}
    })

    # Prompts: config_name, server_url, user_token, (3 optional fields)
    inputs_fallback_server = iter(["fallback_server_test", "", "new_specific_token", "", "", ""]) 
    monkeypatch.setattr("typer.prompt", lambda *args, **kwargs: next(inputs_fallback_server))
    result = runner.invoke(main_cli_app, ["config", "init"])
    assert result.exit_code == 0 # Check this first
    if result.exception: # Add this to see the exception if exit_code is non-zero
        print(f"Exception in test_init_fallback_and_required_prompts (fallback_server): {result.exception}")
        raise result.exception


    cfg = configparser.ConfigParser()
    cfg.read(isolated_config_file)
    assert cfg['fallback_server_test']['server_url'] == 'http://default.com'
    assert decode_token(cfg['fallback_server_test']['user_token']) == 'new_specific_token'

    # Prompts: config_name, server_url, user_token, (3 optional fields)
    inputs_fallback_token = iter(["fallback_token_test", "http://new_server.com", "", "", "", ""]) 
    monkeypatch.setattr("typer.prompt", lambda *args, **kwargs: next(inputs_fallback_token))
    result = runner.invoke(main_cli_app, ["config", "init"])
    assert result.exit_code == 0
    if result.exception:
        print(f"Exception in test_init_fallback_and_required_prompts (fallback_token): {result.exception}")
        raise result.exception

    cfg.read(isolated_config_file) 
    assert cfg['fallback_token_test']['server_url'] == 'http://new_server.com'
    assert decode_token(cfg['fallback_token_test']['user_token']) == 'default_token_val'

    create_config_file_manually(isolated_config_file, { 
        'default': {'server_url': 'http://another.com'}, # No user_token in default for this part
        'meta': {'active_config': 'default'}
    })
    # Prompts: config_name, server_url, user_token (empty, triggers required), required_token, (3 optional fields)
    prompts_required = iter(["required_token_block", "", "", "actual_required_token_val", "", "", ""])
    monkeypatch.setattr("typer.prompt", lambda *args, **kwargs: next(prompts_required))
    result = runner.invoke(main_cli_app, ["config", "init"])
    assert result.exit_code == 0
    if result.exception:
        print(f"Exception in test_init_fallback_and_required_prompts (prompts_required): {result.exception}")
        raise result.exception
        
    cfg.read(isolated_config_file)
    assert cfg['required_token_block']['server_url'] == 'http://another.com'
    assert decode_token(cfg['required_token_block']['user_token']) == 'actual_required_token_val'