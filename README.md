<h1 align="center">
  <img src="https://raw.githubusercontent.com/sankur-codes/jiaz/main/utils/assets/jiaz_logo.jpg" width="100" />
  <br/>
  JIAZ
</h1>

  ![CI](https://github.com/sankur-codes/jiaz/actions/workflows/ci.yml/badge.svg)
  ![Issues](https://img.shields.io/github/issues/sankur-codes/jiaz?style=flat-square)
  ![Forks](https://img.shields.io/github/forks/sankur-codes/jiaz?style=flat-square)
  ![Stars](https://img.shields.io/github/stars/sankur-codes/jiaz?style=flat-square)
  ![License](https://img.shields.io/github/license/sankur-codes/jiaz?style=flat-square)
  ![GitHub top language](https://img.shields.io/github/languages/top/sankur-codes/jiaz)
  ![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/sankur-codes/jiaz/ci.yaml)

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
1. Go to **GitHub Actions** tab of this repo.
2. Find the latest successful `CI` workflow run for the `main` branch.
3. Click on the workflow run.
4. Check the `Artifacts` tab.
5. Download the zip file for your OS:
   - `jiaz-macos-latest.zip` (macOS)
   - `jiaz-linux-latest.zip` (Linux)
   - `jiaz-windows-latest.zip` (Windows)

#### 💻 Platform-Specific Installation:

After downloading the appropriate zip file for your OS, follow these platform-specific steps:

##### 🍎 macOS Installation:

```bash
# Extract directly to /opt/jiaz (adjust download path as needed)
sudo unzip ~/Downloads/jiaz-macos-latest.zip -d /opt/jiaz

# Make executable
sudo chmod +x /opt/jiaz/jiaz

# Remove macOS quarantine attribute
sudo xattr -dr com.apple.quarantine /opt/jiaz

# Add to PATH (temporary)
export PATH="/opt/jiaz:$PATH"

# Add to PATH (permanent) for zsh (default on macOS Catalina+)
echo 'export PATH="/opt/jiaz:$PATH"' >> ~/.zshrc

# Verify installation
jiaz --help
```

##### 🐧 Linux Installation:

```bash
# Extract directly to /opt/jiaz (adjust download path as needed)
sudo unzip ~/Downloads/jiaz-linux-latest.zip -d /opt/jiaz

# Make executable
sudo chmod +x /opt/jiaz/jiaz

# Add to PATH (temporary)
export PATH="/opt/jiaz:$PATH"

# Add to PATH (permanent) for bash
echo 'export PATH="/opt/jiaz:$PATH"' >> ~/.bashrc

# Verify installation
jiaz --help
```

##### 🪟 Windows Installation:

**Using PowerShell (Run as Administrator):**
```powershell
# Extract to Program Files (adjust download path as needed)
Expand-Archive -Path "$env:USERPROFILE\Downloads\jiaz-windows-latest.zip" -DestinationPath "C:\Program Files\jiaz"

# Add to PATH permanently
$env:PATH += ";C:\Program Files\jiaz"
[Environment]::SetEnvironmentVariable("PATH", $env:PATH, [EnvironmentVariableTarget]::Machine)

# Verify installation (open new PowerShell/CMD)
jiaz --help
```

**Using Command Prompt (Run as Administrator):**
```cmd
# Extract using built-in tools or 7-zip
# Then add to PATH via System Properties > Environment Variables
# Add "C:\Program Files\jiaz" to the PATH variable

# Verify installation (open new CMD)
jiaz --help
```

> **📝 Note**: Download paths may vary depending on your browser settings. Adjust the paths in the commands above to match your actual download location.

---

### 🧑‍💻 2. Build Binary locally using pip and pyinstaller

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

##### ✅ Installation Steps:

After running `make build`, the binary will be created in `dist/jiaz`. To install it system-wide:

```bash
# Create installation directory
sudo mkdir -p /opt/jiaz

# Copy the built binary
sudo cp -r dist/jiaz/* /opt/jiaz

# Make it executable
sudo chmod +x /opt/jiaz/jiaz

# Add to PATH (add this to your shell profile for persistence)
export PATH="/opt/jiaz:$PATH"

# Verify installation
jiaz --help
```

---

## 🧹 Cleaning Up

```bash
make clean  # Removes build/dist folders, pycache, and spec files
```

---

## 🧪 Usage

jiaz provides two main command groups for managing JIRA data:

### 📋 Configuration Management
Use `jiaz config` commands to manage your JIRA configurations and API settings.

```bash
jiaz config [SUBCOMMAND] [OPTIONS]
```

**📖 For detailed configuration documentation, see:** [jiaz/commands/config/README.md](jiaz/commands/config/README.md)

### 📊 Data Analysis  
Use `jiaz analyze` commands to analyze JIRA data with AI-powered features.

```bash
jiaz analyze [SUBCOMMAND] [OPTIONS]
```

**📖 For detailed analysis documentation, see:** [jiaz/commands/analyze/README.md](jiaz/commands/analyze/README.md)

**💡 Tip**: Use `--help` with any command to see detailed usage information:

```bash
jiaz --help
jiaz config --help
jiaz analyze --help
jiaz config init --help
jiaz analyze sprint --help
jiaz analyze issue --help
```
