# jiaz analyze - JIRA Data Analysis

Analyze JIRA data with AI-powered features using `jiaz analyze` commands.

The main command structure is:

```bash
jiaz analyze [SUBCOMMAND] [OPTIONS]
```

---

## Commands

### `jiaz analyze sprint`

Analyze and display current active sprint data.

**Syntax:**

```bash
jiaz analyze sprint [OPTIONS]
```

**Options:**

- `--wrt, -w`: Display sprint data in specific perspective
  - Values: `issue`, `owner`, `status`, `epic`
  - Default: `status`
- `--show, -s`: Comma-separated columns to show (if not provided, all columns are shown)
- `--output, -o`: Display format
  - Values: `json`, `table`, `csv`
  - Default: `json`
- `--config-name, -c`: Configuration name to use (default: active config)
- `--mine, -m`: Show only issues assigned to the current user

**Examples:**

```bash
# Show sprint data grouped by status
jiaz analyze sprint --wrt status

# Show only specific columns in table format
jiaz analyze sprint --show "key,summary,status" --output table

# Show only my assigned issues
jiaz analyze sprint --mine

# Use specific configuration
jiaz analyze sprint --config-name myconfig
```

---

### `jiaz analyze issue`

Analyze and display detailed data for a specific JIRA issue.

**Syntax:**

```bash
jiaz analyze issue ISSUE_ID [OPTIONS]
```

**Arguments:**

- `ISSUE_ID`: Valid ID of the issue to be analyzed (required)

**Options:**

- `--show, -s`: Field names to show (comma-separated exact names)
- `--output, -o`: Display format
  - Values: `json`, `table`
  - Default: `json`
- `--config-name, -c`: Configuration name to use (default: active config)
- `--rundown, -r`: Generate AI-powered progress summary
- `--marshal-description, -m`: Standardize issue description using AI

**Examples:**

```bash
# Basic issue analysis
jiaz analyze issue PROJ-123

# Show specific fields in table format
jiaz analyze issue PROJ-123 --show "key,summary,status,assignee" --output table

# Generate AI-powered progress summary
jiaz analyze issue PROJ-123 --rundown

# Standardize issue description with AI
jiaz analyze issue PROJ-123 --marshal-description

# Use specific configuration
jiaz analyze issue PROJ-123 --config-name myconfig
```

**⚠️ Note:** `--rundown` and `--marshal-description` options are mutually exclusive.

---

## AI-Powered Features

### 🤖 Progress Summary (`--rundown`)
- Generates intelligent analysis of issue progress
- Provides insights into completion status and blockers
- Uses either local Ollama models or Google Gemini (based on configuration)

### 📝 Description Standardization (`--marshal-description`)
- Converts JIRA markup to standardized format
- Improves readability and consistency
- AI-powered content enhancement

---

## Output Formats

### JSON Format
- Structured data output
- Easy to parse programmatically
- Default format for most commands

### Table Format
- Human-readable tabular display
- Great for terminal viewing
- Supports column selection with `--show`

### CSV Format (Sprint only)
- Comma-separated values
- Export-friendly format
- Useful for data analysis and reporting

---

## Configuration

All analyze commands respect the active configuration set via `jiaz config use`. You can override this with the `--config-name` option.

Required configuration fields:
- `server_url`: JIRA server URL
- `user_token`: JIRA authentication token
- `jira_project`: Project key (optional but recommended)
- `jira_sprintboard_name`: Sprint board name (for sprint analysis)

---

## Examples Workflow

```bash
# Analyze current sprint status
jiaz analyze sprint --wrt status --output table

# Get detailed issue information
jiaz analyze issue PROJ-123 --output table

# Generate AI summary for an issue
jiaz analyze issue PROJ-123 --rundown

# Analyze sprint for specific user
jiaz analyze sprint --mine --output csv

# Standardize issue description
jiaz analyze issue PROJ-456 --marshal-description
```

---

## LLM Integration

The analyze commands integrate with AI models for enhanced analysis:

- **🏠 Local Processing**: Uses Ollama for privacy-focused analysis
- **☁️ Cloud Power**: Optionally uses Google Gemini for faster responses
- **🔀 Automatic Fallback**: Seamlessly switches between providers
- **⚙️ Configuration**: Set Gemini API key via `jiaz config set gemini_api_key`