import os
import typer
from pathlib import Path
import configparser
import base64

app = typer.Typer(help="Manage JIRA configuration")

CONFIG_DIR = Path.home() / ".jiaz"
CONFIG_FILE = CONFIG_DIR / "config"

def validate_config(config):
    changed = False
    for section in config.sections():
        keys_to_remove = [k for k, v in config.items(section) if not v.strip()]
        for k in keys_to_remove:
            config.remove_option(section, k)
            changed = True
    if changed:
        save_config(config)

def prompt_with_fallback(
    prompt_text: str,
    fallback_prompt_text: str,
    config: configparser.ConfigParser,
    key: str,
    section: str = 'default'
) -> str:
    value = typer.prompt(prompt_text, type=str, default="")
    if not value:
        if config.has_option(section, key):
            return config.get(section, key)
        else:
            return prompt_required_with_retries([fallback_prompt_text])
    return value


def prompt_required_with_retries(prompt_texts: list[str], max_attempts: int = 3) -> str:
    for attempt in range(max_attempts):
        prompt_text = prompt_texts[min(attempt, len(prompt_texts) - 1)]
        value = typer.prompt(prompt_text, type=str, default="")
        if value.strip():
            return value
    typer.echo("Required field not provided after 3 attempts. Exiting.")
    raise typer.Exit(code=1)


def load_config():
    config = configparser.ConfigParser()
    if CONFIG_FILE.exists():
        config.read(CONFIG_FILE)
    validate_config(config)
    return config


def save_config(config):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, 'w') as f:
        config.write(f)


def get_active_config(config):
    if config.has_section('meta') and config.has_option('meta', 'active_config'):
        return config.get('meta', 'active_config')
    return 'default'


def set_active_config(config, config_name: str):
    if 'meta' not in config:
        config['meta'] = {}
    config['meta']['active_config'] = config_name


def encode_token(token: str) -> str:
    return base64.b64encode(token.encode('utf-8')).decode('utf-8')


def decode_token(encoded_token: str) -> str:
    return base64.b64decode(encoded_token.encode('utf-8')).decode('utf-8')


@app.command()
def init():
    """Initialize the configuration with required and optional fields."""
    config = load_config()

    if 'meta' not in config:
        config['meta'] = {}

    if not [sec for sec in config.sections() if sec != 'meta']:
        typer.echo("Config file does not exist or contains no blocks. Creating default configuration.")

        server_url = prompt_required_with_retries([
            "Enter server URL (required)",
            "Server URL is required. Please enter it.",
            "Cannot proceed without Server URL. Please enter a valid URL."
        ])

        user_token = prompt_required_with_retries([
            "Enter user token (required)",
            "User token is required. Please enter it.",
            "Cannot proceed without user token. Please enter a valid token."
        ])

        encoded_token = encode_token(user_token)

        default_config = {
            'server_url': server_url,
            'user_token': encoded_token,
        }

        for key in ['jira_project', 'jira_backlog_name', 'jira_sprintboard_name']:
            value = typer.prompt(f"Enter {key.replace('_', ' ')} (optional)", type=str, default="")
            if value.strip():
                default_config[key] = value

        config['default'] = default_config

        set_active_config(config, 'default')
        save_config(config)
        typer.echo("Default configuration set and active.")
    else:
        typer.echo("Config file already exists. Adding a new configuration block.")
        new_config_name = typer.prompt("Enter a new config name")

        if new_config_name in config:
            typer.echo(f"Config name '{new_config_name}' already exists. Please choose a different name.")
            raise typer.Exit(code=1)

        server_url = prompt_with_fallback(
            "Enter server URL (leave empty to use value from default)",
            "Server URL is required. Please enter it.",
            config,
            key="server_url",
            section="default"
        )

        user_token_input = typer.prompt(
            "Enter user token (leave empty to use value from default)",
            type=str,
            default=""
        )

        if user_token_input.strip():
            encoded_token = encode_token(user_token_input)
        elif config.has_option("default", "user_token"):
            encoded_token = config.get("default", "user_token")
        else:
            user_token_raw = prompt_required_with_retries([
                "User token is required. Please enter it.",
                "Please enter a valid user token.",
                "Cannot proceed without a user token."
            ])
            encoded_token = encode_token(user_token_raw)

        new_config = {
            'server_url': server_url,
            'user_token': encoded_token,
        }

        for key in ['jira_project', 'jira_backlog_name', 'jira_sprintboard_name']:
            value = typer.prompt(f"Enter {key.replace('_', ' ')} (optional)", type=str, default="")
            if value.strip():
                new_config[key] = value

        config[new_config_name] = new_config
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
def set(
    key: str,
    value: str,
    name: str = typer.Option(None, "--name", "-n", help="Target config block")
):
    """Set a configuration key-value pair."""
    if name is None:
        typer.echo("Error: --name/-n option is required.")
        raise typer.Exit(code=1)

    config = load_config()

    if name in config:
        section = config[name]
        is_update = key in section

        if key == 'user_token':
            value = encode_token(value)

        section[key] = value
        save_config(config)

        if is_update:
            typer.echo(f"Config updated in '{name}': {key}={value}")
        else:
            typer.echo(f"Config added in '{name}': {key}={value}")
    else:
        typer.echo(f"Config '{name}' not found. Use 'list' to view available configs.")


@app.command()
def get(
    key: str,
    name: str = typer.Option(None, "--name", "-n", help="Target config block")
):
    """Get a configuration value."""
    if name is None:
        typer.echo("Error: --name/-n option is required.")
        raise typer.Exit(code=1)

    config = load_config()

    if name in config and key in config[name]:
        value = config[name][key]
        if key == "user_token":
            value = decode_token(value)
        typer.echo(value)
    else:
        typer.echo(f"Key '{key}' not found in config '{name}'.")


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
                if key == 'user_token':
                    value = decode_token(value)
                typer.echo(f"{key} = {value}")
        else:
            typer.echo(f"Config '{name}' not found.")


if __name__ == "__main__":
    app()
