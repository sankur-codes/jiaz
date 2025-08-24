# jiaz config - Configuration Management

Manage your jiaz configurations easily using `jiaz config` commands.

The main command is:

```bash
jiaz config [SUBCOMMAND] [OPTIONS]
```

You can manage multiple configurations (blocks) for different JIRA instances.

**💡 Tip**: Use `--help` with any command to see detailed usage information:

```bash
jiaz config --help
jiaz config init --help
jiaz config set --help
jiaz config get --help
jiaz config use --help
jiaz config list --help
```

---

## Commands

### `jiaz config init`

Initialize a new configuration.

- If no config file exists, it will create a default one.
- If config already exists, it allows adding a new configuration block.

**Example:**

```bash
jiaz config init
```

You will be prompted for:

- Server URL (required)
- User token (required)
- Optional fields: `jira_project`, `jira_backlog_name`, `jira_sprintboard_name`
- **Gemini API key** (optional) - For enhanced AI-powered analysis using Google's Gemini models

If you leave required fields empty, it will fallback to the `default` block (or ask you again if missing).

> **🔗 LLM Provider Selection**: jiaz now supports both local Ollama models and Google's Gemini. If a valid Gemini API key is provided, it will be used for faster responses. Otherwise, the system falls back to Ollama.

---

### `jiaz config set`

Update or add a key-value pair in a specific config block.

**Syntax:**

```bash
jiaz config set KEY VALUE --name CONFIG_NAME
```

**Example:**

```bash
jiaz config set jira_project MYPROJECT --name myconfig
jiaz config set gemini_api_key YOUR_GEMINI_API_KEY --name myconfig
```

- If the key exists, it updates the value.
- If the key doesn't exist, it adds it.
- For `gemini_api_key`, the system will validate the API key before saving it.

---

### `jiaz config get`

Retrieve a value from a config block.

**Syntax:**

```bash
jiaz config get KEY --name CONFIG_NAME
```

**Example:**

```bash
jiaz config get server_url --name default
```

If the key is `user_token` or `gemini_api_key`, it automatically decodes it before displaying.

---

### `jiaz config use`

Set the active configuration to use by default.

**Syntax:**

```bash
jiaz config use CONFIG_NAME
```

**Example:**

```bash
jiaz config use myconfig
```

The active config will be stored in the `meta` section of your config file.

---

### `jiaz config list`

List available configs or key-value pairs for a specific config.

**List all config names:**

```bash
jiaz config list
```

**List key-value pairs for a config block:**

```bash
jiaz config list --name CONFIG_NAME
```

**Example:**

```bash
jiaz config list --name default
```

---

## Configuration Notes

- Empty key-values are automatically **removed** from the config file when `jiaz` is run.
- `user_token` and `gemini_api_key` is stored **encoded** (base64) internally for simple obfuscation.
- Default config is used for fallbacks when creating new blocks.
- Configuration file location: `~/.jiaz/config`
- Multiple configuration blocks supported for different teams or JIRA instances.

---

## Examples

```bash
# Initialize a new configuration
jiaz config init

# Set project for default config
jiaz config set jira_project ABC --name default

# Get the project value
jiaz config get jira_project --name default

# Switch to a different config
jiaz config use myconfig

# List all available configurations
jiaz config list
```
