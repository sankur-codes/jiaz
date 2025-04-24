import os
import typer
from pathlib import Path
import configparser
import base64

app = typer.Typer(help="Manage JIRA configuration")

CONFIG_DIR = Path.home() / ".jiaz"
CONFIG_FILE = CONFIG_DIR / "config"


def prompt_with_fallback(
    prompt_text: str,
    fallback_prompt_text: str,
    config: dict,
    key: str,
    section: str = 'default'
) -> str:
    value = typer.prompt(prompt_text, type=str, default="")
    if not value:
        fallback_value = config.get(section, {}).get(key, '')
        if not fallback_value:
            value = typer.prompt(fallback_prompt_text, type=str)
        else:
            value = fallback_value
    return value

def load_config():
    """Load the configuration file if it exists."""
    config = configparser.ConfigParser()
    if CONFIG_FILE.exists():
        config.read(CONFIG_FILE)
    return config

def save_config(config):
    """Save the configuration to the file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, 'w') as f:
        config.write(f)

def get_active_config(config):
    """Retrieve the active configuration name from the config file."""
    return config['meta'].get('active_config', 'default')

def set_active_config(config, config_name: str):
    """Set the active configuration in the config file under [meta] section."""
    if 'meta' not in config:
        config['meta'] = {}
    config['meta']['active_config'] = config_name

def encode_token(token: str) -> str:
    """Encode the token using base64."""
    return base64.b64encode(token.encode('utf-8')).decode('utf-8')

def decode_token(encoded_token: str) -> str:
    """Decode the token from base64."""
    return base64.b64decode(encoded_token.encode('utf-8')).decode('utf-8')

@app.command()
def init():
    """Initialize the configuration with required and optional fields."""
    config = load_config()

    if 'meta' not in config:
        config['meta'] = {}

    if not [sec for sec in config.sections() if sec != 'meta']:
        typer.echo("Config file does not exist or contains no blocks. Creating default configuration.")
        server_url = typer.prompt("Enter server URL (required)", type=str)
        user_token = typer.prompt("Enter user token (required)", type=str)
        encoded_token = encode_token(user_token)
        jira_project = typer.prompt("Enter Jira project (optional)", type=str, default="")
        jira_backlog_name = typer.prompt("Enter Jira backlog name (optional)", type=str, default="")
        jira_sprintboard_name = typer.prompt("Enter Jira sprintboard name (optional)", type=str, default="")

        config['default'] = {
            'server_url': server_url,
            'user_token': encoded_token,
            'jira_project': jira_project,
            'jira_backlog_name': jira_backlog_name,
            'jira_sprintboard_name': jira_sprintboard_name,
        }

        set_active_config(config, 'default')
        save_config(config)
        typer.echo("Default configuration set and active.")
    else:
        typer.echo("Config file already exists. Adding a new configuration block.")
        new_config_name = typer.prompt("Enter a new config name")
    
        # server_url = typer.prompt("Enter server URL (leave empty to use default)", type=str, default="")
        # if not server_url:
        #     default_server_url = config['default'].get('server_url', '')
        #     if not default_server_url:
        #         server_url = typer.prompt("No server_url in [default] config , Enter server URL (required)", type=str)
        #     else:
        #         server_url = default_server_url
        # user_token = typer.prompt("Enter user token (leave empty to use default)", type=str, default="")
        # if not user_token:
        #     default_user_token = config['default'].get('user_token', '')
        #     if not default_user_token:
        #         user_token = typer.prompt("No user_token in [default] config , Enter user_token (required)", type=str)
        #         encoded_token = encode_token(user_token)
        #     else:
        #         user_token = default_user_token

        # Usage for server_url
        server_url = prompt_with_fallback(
            prompt_text="Enter server URL (leave empty to use default)",
            fallback_prompt_text="No server_url in [default] config, Enter server URL (required)",
            config=config,
            key="server_url"
        )

        # Usage for user_token
        user_token = prompt_with_fallback(
            prompt_text="Enter user token (leave empty to use default)",
            fallback_prompt_text="No user_token in [default] config, Enter user token (required)",
            config=config,
            key="user_token"
        )

        encoded_token = encode_token(user_token) if user_token else ''

        jira_project = typer.prompt("Enter Jira project (optional)", type=str, default="")
        jira_backlog_name = typer.prompt("Enter Jira backlog name (optional)", type=str, default="")
        jira_sprintboard_name = typer.prompt("Enter Jira sprintboard name (optional)", type=str, default="")

        config[new_config_name] = {
            'server_url': server_url,
            'user_token': encoded_token,
            'jira_project': jira_project,
            'jira_backlog_name': jira_backlog_name,
            'jira_sprintboard_name': jira_sprintboard_name,
        }

        save_config(config)
        typer.echo(f"New configuration block '{new_config_name}' added.")

@app.command()
def use(config_name: str):
    """Set the active configuration for future commands."""
    config = load_config()
    if config_name in config:
        set_active_config(config, config_name)
        save_config(config)
        typer.echo(f"Active configuration set to '{config_name}'.")
    else:
        typer.echo(f"Config '{config_name}' not found.")

@app.command()
def set(key: str, value: str):
    """Set a configuration key-value pair in the active config block."""
    config = load_config()
    active_config = get_active_config(config)

    if active_config in config:
        if key == 'user_token':
            value = encode_token(value)
        config[active_config][key] = value
        save_config(config)
        typer.echo(f"Config set in '{active_config}': {key}={value}")
    else:
        typer.echo(f"Config '{active_config}' not found. Please run 'use <config_name>' first.")

@app.command()
def get(key: str):
    """Get a configuration value by key from the active config block."""
    config = load_config()
    active_config = get_active_config(config)

    if active_config in config and key in config[active_config]:
        typer.echo(config[active_config][key])
    else:
        typer.echo(f"Key '{key}' not found in config '{active_config}'.")

@app.command()
def list(name: str = typer.Option(None, '--name', '-n', help="List key-value pairs for a specific config name")):
    """List all configurations or key-value pairs for a specific config."""
    config = load_config()

    if name is None:
        sections = [s for s in config.sections() if s != 'meta']
        if sections:
            typer.echo("Available configurations:")
            for section in sections:
                typer.echo(section)
            active_config = get_active_config(config)
            typer.echo(f"\nActive configuration: {active_config}")
        else:
            typer.echo("No configuration found.")
    else:
        if name in config:
            typer.echo(f"Configuration for '{name}':")
            for key, value in config.items(name):
                typer.echo(f"{key} = {value}")
        else:
            typer.echo(f"Config '{name}' not found.")

# to add
# - active_config in config file
# - validate when use/set : server_url/token should be there
# - when executing jiaz command : give suggestion of init command if config file does not exist
