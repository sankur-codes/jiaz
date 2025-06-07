import os
from pathlib import Path
import configparser
import base64
import typer

CONFIG_DIR = Path.home() / ".jiaz"
CONFIG_FILE = CONFIG_DIR / "config"

def prepend_warning_to_config():
    """Prepend a warning comment to the config file."""
    # Check if the file exists before proceeding
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r+') as config_file:
            content = config_file.read()
            warning_message = (
                "# WARNING: Do not edit this config file manually. \n"
                "# Any manual changes may cause commands to behave improperly. \n"
                "# If manually edited & code malfunctions, \n"
                "# you will need to run 'jiaz config init' again after deleting this file.\n"
            )
            config_file.seek(0, 0)  # Move to the top of the file
            config_file.write(warning_message + content)  # Prepend warning followed by existing content

def validate_config(config):
    changed = False
    for section in config.sections():
        keys_to_remove = [k for k, v in config.items(section) if not v.strip()]
        for k in keys_to_remove:
            config.remove_option(section, k)
            changed = True
    if changed:
        save_config(config)

def prompt_with_fallback(prompt_text, fallback_prompt_text, config, key, section='default'):
    value = typer.prompt(prompt_text, type=str, default="")
    if not value:
        if config.has_option(section, key):
            return config.get(section, key)
        else:
            return prompt_required_with_retries([fallback_prompt_text])
    return value

def prompt_required_with_retries(prompt_texts, max_attempts=3):
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

def get_active_config(config=load_config()):
    if config.has_section('meta') and config.has_option('meta', 'active_config'):
        return config.get('meta', 'active_config')
    return 'default'

def set_active_config(config, config_name):
    if 'meta' not in config:
        config['meta'] = {}
    config['meta']['active_config'] = config_name

def encode_token(token):
    return base64.b64encode(token.encode('utf-8')).decode('utf-8')

def decode_token(encoded_token):
    return base64.b64decode(encoded_token.encode('utf-8')).decode('utf-8')
