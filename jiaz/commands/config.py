import os
import typer
from pathlib import Path
import configparser


app = typer.Typer(help="Manage JIRA configuration")

CONFIG_DIR = Path.home() / ".jiaz"
CONFIG_FILE = CONFIG_DIR / "config"


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

def get_active_config():
    """Get the active configuration name from the environment variable."""
    return os.getenv('JIAZ_ACTIVE_CONFIG', 'default')  # Default to 'default' if no active config is set

def set_active_config(config_name: str):
    """Set the active configuration name in the environment variable."""
    os.environ['JIAZ_ACTIVE_CONFIG'] = config_name

@app.command()
def init():
    """Initialize the configuration with required and optional fields."""
    config = load_config()

    # If the config file is empty, we need to create a default configuration
    if not config.sections():
        typer.echo("Config file does not exist. Creating default configuration.")
        server_url = typer.prompt("Enter server URL (required)", type=str)
        user_token = typer.prompt("Enter user token (required)", type=str)
        jira_project = typer.prompt("Enter Jira project (optional)", type=str, default="")
        jira_backlog_name = typer.prompt("Enter Jira backlog name (optional)", type=str, default="")
        jira_sprintboard_name = typer.prompt("Enter Jira sprintboard name (optional)", type=str, default="")

        # Create the default block
        config['default'] = {
            'server_url': server_url,
            'user_token': user_token,
            'jira_project': jira_project,
            'jira_backlog_name': jira_backlog_name,
            'jira_sprintboard_name': jira_sprintboard_name,
        }

        save_config(config)
        set_active_config('default')  # Automatically set the default config as active
        typer.echo("Default configuration set and active.")
    else:
        # If config file exists, prompt user to create a new config block
        typer.echo("Config file already exists. Adding a new configuration block.")
        new_config_name = typer.prompt("Enter a new config name")
        server_url = typer.prompt("Enter server URL (leave empty to use default)", type=str, default="")
        user_token = typer.prompt("Enter user token (leave empty to use default)", type=str, default="")
        jira_project = typer.prompt("Enter Jira project (optional)", type=str, default="")
        jira_backlog_name = typer.prompt("Enter Jira backlog name (optional)", type=str, default="")
        jira_sprintboard_name = typer.prompt("Enter Jira sprintboard name (optional)", type=str, default="")

        # Use values from the default block if no new values are provided
        if not server_url:
            server_url = config['default'].get('server_url', '')
        if not user_token:
            user_token = config['default'].get('user_token', '')

        # Add the new config block
        config[new_config_name] = {
            'server_url': server_url,
            'user_token': user_token,
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
        set_active_config(config_name)
        typer.echo(f"Active configuration set to '{config_name}'.")
    else:
        typer.echo(f"Config '{config_name}' not found.")

@app.command()
def set(key: str, value: str):
    """Set a configuration key-value pair in the active config block."""
    active_config = get_active_config()
    config = load_config()

    if active_config in config:
        config[active_config][key] = value
        save_config(config)
        typer.echo(f"Config set in '{active_config}': {key}={value}")
    else:
        typer.echo(f"Config '{active_config}' not found. Please run 'use <config_name>' first.")

@app.command()
def get(key: str):
    """Get a configuration value by key from the active config block."""
    active_config = get_active_config()
    config = load_config()

    if active_config in config and key in config[active_config]:
        typer.echo(config[active_config][key])
    else:
        typer.echo(f"Key '{key}' not found in config '{active_config}'.")

@app.command()
def list(name: str = typer.Option(None, '--name', '-n', help="List key-value pairs for a specific config name")):
    """List all configurations or key-value pairs for a specific config."""
    config = load_config()
    
    if name is None:
        # If no config name is provided, list only the config names (section names)
        if config.sections():
            for section in config.sections():
                typer.echo(section)
        else:
            typer.echo("No configuration found.")
    else:
        # If config name is provided, list the key-value pairs for that config
        if name in config:
            typer.echo(f"Configuration for '{name}':")
            for key, value in config.items(name):
                typer.echo(f"{key} = {value}")
        else:
            typer.echo(f"Config '{name}' not found.")
