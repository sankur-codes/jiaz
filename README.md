<p align="center">
  <img src="https://img.shields.io/badge/jiaz-CLI-blueviolet?style=for-the-badge&logo=python&logoColor=white" alt="jiaz CLI Badge"/>
</p>

# jiaz

**`jiaz`** is a cross-platform Python CLI assistant for analyzing JIRA data with AI-powered features.

## 🤖 AI-Powered Analysis

jiaz integrates with both **local Ollama models** and **Google's Gemini** for intelligent JIRA data analysis:

- **🏠 Local Processing**: Uses Ollama for privacy-focused, offline analysis
- **☁️ Cloud Power**: Optionally leverages Google's Gemini for faster, more capable analysis
- **🔀 Automatic Fallback**: Seamlessly switches between providers based on availability
- **⚙️ Easy Configuration**: Simple API key setup enables Gemini integration

---

## 🚀 Installation Methods

You can install and use `jiaz` in **two ways**:

---

### 📦 1. Using Prebuilt Binaries (Recommended for End Users)

> ✅ Quickest way to use `jiaz` without Python or containers.

#### ✅ Steps:
1. Go to **GitHub Actions** tab of this repo (later: check **Releases**).
2. Find the latest successful workflow run for the `main` branch.
3. Download the zip file for your OS:
   - `jiaz-macos.zip` (macOS)
   - `jiaz-linux.zip` (Linux)
   - `jiaz-windows.zip` (Windows)

#### 📁 Recommended Extraction Path:
- Extract to:
  - macOS/Linux: `~/bin/jiaz` or `/usr/local/bin/jiaz`
  - Windows: `C:\Program Files\jiaz`

Make sure the binary is in your **system PATH** or reference it with full path.

---

#### ⚙️ One-Time Post Setup (Mandatory):

After extraction, run:

```bash
make prepare
```

> This ensures platform-specific fixes like:
- macOS: Removing quarantine attribute (`xattr -d`)
- Linux/Windows: Unzipping and marking binary as executable (if needed)

> 💡 You must have `make` installed:
- macOS: via `brew install make`
- Windows: via Git Bash, or `choco install make`
- Linux: via `sudo apt install make` or `sudo yum install make`

---

### 🧑‍💻 2. Build from Source (Recommended for Developers)

You can build and run `jiaz` locally from source using three approaches:

---

#### 1️⃣ 1. Using Python (Direct Setup)

##### ✅ Prerequisites:
- Python 3.8+
- [`pyenv`](https://github.com/pyenv/pyenv) (recommended)
- `make` (optional, for convenience)

##### ✅ Setup:

```bash
# Setup Python env
pyenv install 3.11.7  # or use your system Python >= 3.8
pyenv virtualenv 3.11.7 jiaz-env
pyenv activate jiaz-env

# Install dependencies
pip install -r requirements.txt

# Run the CLI
python -m jiaz --help
```

---

#### 2️⃣ 2. Build Binary locally using pip and pyinstaller


##### ✅ Prerequisites:
- Python 3.8+
- [`pyenv`](https://github.com/pyenv/pyenv) (recommended)
- `make` (optional, for convenience)

##### ✅ Steps:

```bash
# Setup Python env - [Optional]
pyenv install 3.11.7  # or use your system Python >= 3.8
pyenv virtualenv 3.11.7 jiaz-env
pyenv activate jiaz-env

# Run make build command
make build 
```

##### ✅ Post-requisites:
- Binary will be created in directory : [`dist/jiaz`]
- Can be moved to desired path where it can be detected directly and you can perform Usage step mentioned below

---

#### 3️⃣ 3. Build Binary Using Container - Only for Linux based OS 🐧

> Uses Podman/Docker to build binary in a clean environment.

##### ✅ Prerequisites:
- Docker or Podman
- `make`

##### ✅ Steps:

```bash
make docker-build
```

This:
- Builds the container image
- Installs dependencies inside container
- Uses `pyinstaller` to generate a binary inside `./dist/`

---

## 📎 Notes & Tips

- **macOS Gatekeeper Warning:**  
  If macOS prevents execution, run:
  ```bash
  xattr -d com.apple.quarantine ./jiaz
  ```
  To re-apply the quarantine:
  ```bash
  xattr -w com.apple.quarantine "0002;..." ./jiaz
  ```

- **PATH Recommendation:**
  - Add to PATH via:
    - `export PATH="$HOME/bin:$PATH"` (Linux/macOS)
    - Add folder to Environment Variables (Windows)

---

## 🧹 Cleaning Up

```bash
make clean  # Removes build/dist folders, pycache, and spec files
```

---

## 🧪 Usage - JIAZ Config Manager

Manage your JIRA configurations easily using `jiaz config` commands.

The main command is:

```bash
jiaz config [SUBCOMMAND] [OPTIONS]
```

You can manage multiple configurations (blocks) for different JIRA instances.

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

If the key is `user_token`, it automatically decodes it before displaying.

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

## Notes

- Empty key-values are automatically **removed** from the config file when `jiaz` is run.
- `user_token` is stored **encoded** (base64) internally for simple obfuscation.
- Default config is used for fallbacks when creating new blocks.

---

## Example Workflow

```bash
jiaz config init
jiaz config set jira_project ABC --name default
jiaz config get jira_project --name default
jiaz config use myconfig
jiaz config list
```




