import os
from pathlib import Path
import configparser
import base64
import typer
import requests

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

def prompt_api_key_with_retries(max_attempts=3):
    """
    Prompt for Gemini API key with validation and retries.
    
    Args:
        max_attempts: Maximum number of attempts
        
    Returns:
        str: Valid API key, or None if user wants to skip
    """
    prompts = [
        "Enter Gemini API key (optional, leave empty to use Ollama only)",
        "Invalid API key. Please enter a valid Gemini API key (or leave empty to skip)",
        "API key validation failed again. Please enter a valid Gemini API key (or leave empty to skip)"
    ]
    
    for attempt in range(max_attempts):
        prompt_text = prompts[min(attempt, len(prompts) - 1)]
        api_key = typer.prompt(prompt_text, type=str, default="")
        
        if not api_key.strip():
            # User wants to skip
            return None
            
        if validate_gemini_api_key(api_key.strip()):
            return api_key.strip()
    
    typer.echo("⚠️  Maximum attempts reached. Proceeding without Gemini API key.")
    return None

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

def get_active_config(config=None):
    if config is None:
        config = load_config()
    if config.has_section('meta') and config.has_option('meta', 'active_config'):
        return config.get('meta', 'active_config')
    return 'default'

def set_active_config(config, config_name):
    if 'meta' not in config:
        config['meta'] = {}
    config['meta']['active_config'] = config_name

def get_specific_config(config_name, config=load_config()):
    if config_name in config:
        return config[config_name]
    else:
        typer.echo(f"Configuration '{config_name}' not found.")
        raise typer.Exit(code=1)

def encode_secure_value(value):
    """Encode sensitive values (tokens, API keys) for storage."""
    return base64.b64encode(value.encode('utf-8')).decode('utf-8')

def decode_secure_value(encoded_value):
    """Decode sensitive values (tokens, API keys) from storage."""
    return base64.b64decode(encoded_value.encode('utf-8')).decode('utf-8')

# Backward compatibility aliases
def encode_token(token):
    return encode_secure_value(token)

def decode_token(encoded_token):
    return decode_secure_value(encoded_token)

def encode_api_key(api_key):
    return encode_secure_value(api_key)

def decode_api_key(encoded_api_key):
    return decode_secure_value(encoded_api_key)

def validate_gemini_api_key(api_key):
    """
    Validate Gemini API key by making a test request.
    
    Args:
        api_key: The Gemini API key to validate
        
    Returns:
        bool: True if API key is valid, False otherwise
    """
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        
        # Create a test instance with the API key
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-pro",
            google_api_key=api_key,
            temperature=0,
            max_retries=1
        )
        
        # Try a simple test message
        test_messages = [("human", "Hello")]
        response = llm.invoke(test_messages)
        
        # If we get here without exception, the API key is valid
        return True
        
    except Exception as e:
        typer.echo(f"API key validation failed: {str(e)}")
        return False

def get_gemini_api_key(config=None):
    """
    Get Gemini API key from config, checking both meta block and active config.
    
    Args:
        config: Optional config object (loads if None)
        
    Returns:
        str: Decoded API key if found and valid, None otherwise
    """
    if config is None:
        config = load_config()
    
    api_key = None
    
    # First check meta block
    if config.has_section('meta') and config.has_option('meta', 'gemini_api_key'):
        api_key = decode_api_key(config.get('meta', 'gemini_api_key'))
    
    # If not in meta, check active config block
    if not api_key:
        active_config = get_active_config(config)
        if config.has_section(active_config) and config.has_option(active_config, 'gemini_api_key'):
            api_key = decode_api_key(config.get(active_config, 'gemini_api_key'))
    
    return api_key

def should_use_gemini(config=None):
    """
    Determine if Gemini should be used based on API key availability and validity.
    
    Args:
        config: Optional config object (loads if None)
        
    Returns:
        bool: True if Gemini should be used, False if Ollama should be used
    """
    api_key = get_gemini_api_key(config)
    if api_key:
        # For performance, we assume the key is valid if it exists
        # You could add validation here if needed
        return True
    return False

def collect_required_fields(fallback_config=None):
    """
    Collect required configuration fields from user input.
    
    Args:
        fallback_config: Optional config to use for fallback values
        
    Returns:
        dict: Dictionary with server_url and encoded user_token
    """
    if fallback_config:
        server_url = prompt_with_fallback(
            "Enter server URL (leave empty to use value from default)",
            "Server URL is required. Please enter it.",
            fallback_config,
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
        elif fallback_config.has_option("default", "user_token"):
            encoded_token = fallback_config.get("default", "user_token")
        else:
            user_token_raw = prompt_required_with_retries([
                "User token is required. Please enter it.",
                "Please enter a valid user token.",
                "Cannot proceed without a user token."
            ])
            encoded_token = encode_token(user_token_raw)
    else:
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
    
    return {
        'server_url': server_url,
        'user_token': encoded_token,
    }

def collect_optional_fields():
    """
    Collect optional JIRA configuration fields from user input.
    
    Returns:
        dict: Dictionary with optional field values
    """
    optional_config = {}
    
    # Optional fields for JIRA configuration
    for key in ['jira_project', 'jira_backlog_name', 'jira_sprintboard_name', 'jira_sprintboard_id', 'jira_board_name']:
        value = typer.prompt(f"Enter {key.replace('_', ' ')} (optional)", type=str, default="")
        if value.strip():
            optional_config[key] = value
    
    return optional_config

def handle_gemini_api_key_input(config):
    """
    Handle Gemini API key input with validation and retry logic.
    
    Args:
        config: Config object to update with API key
        
    Returns:
        dict: Dictionary with gemini_api_key if provided and valid
    """
    gemini_config = {}
    
    # Use the new retry function
    api_key = prompt_api_key_with_retries()
    
    if api_key:
        encoded_api_key = encode_api_key(api_key)
        gemini_config['gemini_api_key'] = encoded_api_key
        
        # Also store in meta block for global access
        if 'meta' not in config:
            config['meta'] = {}
        config['meta']['gemini_api_key'] = encoded_api_key
        typer.echo("✅ Gemini API key validated and saved.")
    else:
        typer.echo("No Gemini API key provided. Will use Ollama for LLM queries.")
    
    return gemini_config
