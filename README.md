<h1 align="center">
  <img src="https://raw.githubusercontent.com/sankur-codes/jiaz/main/utils/asset/jiaz_logo.jpg" width="100" />
  <br/>
  An AI backed CLI tool for analyzing JIRA data
</h1>

<p align="center">
  <img src="https://img.shields.io/github/issues/sankur-codes/jiaz?style=flat-square&logo=firebase&logoColor=C8332D" alt="Issues"/>
  <img src="https://img.shields.io/github/forks/sankur-codes/jiaz?style=flat-square&logo=transmission&logoColor=897BFF" alt="Forks"/>
  <img src="https://img.shields.io/github/stars/sankur-codes/jiaz?style=flat-square&logo=trustpilot&logoColor=FFFF66" alt="Stars"/>
  <img src="https://img.shields.io/github/license/sankur-codes/jiaz?style=flat-square&logo=open-source-initiative" alt="License"/>
  <img src="https://img.shields.io/github/actions/workflow/status/sankur-codes/jiaz/ci.yaml?branch=main&logo=githubactions" alt="CI Status"/>
</p>


# jiaz

**jiaz** is a command-line software designed for analyzing JIRA data with speed and flexibility. Whether you are a developer, project manager, or data analyst, JIAZ empowers you to extract insights, automate reporting, and streamline your workflow with minimal setup.

jiaz helps streamline JIRA hygiene by automating routine tasks—such as grooming story descriptions or validating epic summaries—turning hours of manual effort into just minutes.

## 🤖 AI-Powered Analysis

jiaz integrates with both **local Ollama models** and **Google's Gemini** for intelligent JIRA data analysis with an automatic fallback to Ollama if Gemini isn’t configured.

- **☁️ Cloud Power**: Leverages Google's Gemini for faster, more capable analysis if key is configured.
- **🏠 Local Processing**: Uses Ollama for privacy-focused, offline analysis.

---

## 🚀 Installation Methods

You can install and use `jiaz` in **two ways**:

---

### 📦 1. Using Prebuilt Binaries (Recommended for End Users)

- #### ✅ Steps:
  1. Go to **[GitHub Actions](https://github.com/sankur-codes/jiaz/actions)** tab of this repo.
  2. Find the latest successful `CI` workflow run for the `main` branch.
  3. Click on the workflow run.
  4. Check the `Artifacts` tab.
  5. Download the zip file for your OS:
    - `jiaz-macos-latest.zip` (macOS)
    - `jiaz-linux-latest.zip` (Linux)
    - `jiaz-windows-latest.zip` (Windows)

  6. After downloading the appropriate zip file for your OS, follow these platform-specific steps:

      - ##### 🍎 macOS Installation:

        - Extract directly to /opt/jiaz (adjust download path as needed)
          ```bash
          sudo unzip ~/Downloads/jiaz-macos-latest.zip -d /opt/jiaz
          ```

        - Make executable
          ```bash
          sudo chmod +x /opt/jiaz/jiaz
          ```

        - Remove macOS quarantine attribute
          ```bash
          sudo xattr -dr com.apple.quarantine /opt/jiaz
          ```
          > **Note** : To re-apply quarantine, run `xattr -w com.apple.quarantine "0002;..." /opt/jiaz`

        - Add to PATH (temporary)
          ```bash
          export PATH="/opt/jiaz:$PATH"
          ```

        - Add to PATH (permanent) for zsh (default on macOS Catalina+)
          ```bash
          echo 'export PATH="/opt/jiaz:$PATH"' >> ~/.zshrc
          ```

        - Verify installation
          ```bash
          jiaz --help
          ```

      - ##### 🐧 Linux Installation:

        
        - Extract directly to /opt/jiaz (adjust download path as needed)
          ```bash
          sudo unzip ~/Downloads/jiaz-linux-latest.zip -d /opt/jiaz
          ```

        - Make executable
          ```bash
          sudo chmod +x /opt/jiaz/jiaz
          ```

        - Add to PATH (temporary)
          ```bash
          export PATH="/opt/jiaz:$PATH"
          ```

        - Add to PATH (permanent) for bash
          ```bash
          echo 'export PATH="/opt/jiaz:$PATH"' >> ~/.bashrc
          ```

        - Verify installation
          ```bash
          jiaz --help
          ```

      - ##### 🪟 Windows Installation:

        - **Using PowerShell (Run as Administrator):**
          - Extract to Program Files (adjust download path as needed)
            ```powershell
            Expand-Archive -Path "$env:USERPROFILE\Downloads\jiaz-windows-latest.zip" -DestinationPath "C:\Program Files\jiaz"
            ```

          - Add to PATH permanently
            ```powershell
            $env:PATH += ";C:\Program Files\jiaz"
            [Environment]::SetEnvironmentVariable("PATH", $env:PATH, [EnvironmentVariableTarget]::Machine)
            ```

          - Verify installation (open new PowerShell/CMD)
            ```powershell
            jiaz --help
            ```

        - **Using UI:**
            - Extract using built-in tools or 7-zip at `C:\Program Files\jiaz`
            - Then go to PATH via System Properties > Environment Variables
            - Add `C:\Program Files\jiaz` to the PATH variable

            - Verify installation (open new CMD)
            ```cmd
            jiaz --help
            ```

> **📝 Note**: Download paths may vary depending on your browser settings. Adjust the paths in the commands above to match your actual download location.

---

### 🧑‍💻 2. Build Binary locally using pip and pyinstaller

- ##### ✅ Prerequisites:
  - Python 3.8+
  - [`pyenv`](https://github.com/pyenv/pyenv) (recommended)
  - `make`

- ##### ✅ Steps:

  - Fork the repository from [upstream](https://github.com/sankur-codes/jiaz)
  - Clone the forked repository
      ```bash
      git clone <url_for_your_fork>
      ```
  - Change directory
      ```bash
      cd </path/to/jiaz>
      ```
  - [Optional] Create a virtual env with Python >= 3.10 and activate it.
  - Run the `make` target to build
      ```bash
      make build
      ```
      > If you do not have `make` installed, check on the commands for the target in the makefile for build


> After running `make build`, `jiaz` directory will be created in `dist/` folder. You can either run the jiaz binary from within jiaz folder or have it setup system-wide.
> To install it system-wide, proceed with the OS specific installation steps provided above.

---

## 🧹 Cleaning Up

```bash
make clean  # Removes build/dist folders, pycache, and spec files
```

---

## 🧪 Usage


- ### 📋 Configuration Management
  > **Note** : For `jiaz` to be able to extract data from JIRA, config setup is must. 

  - Use `jiaz config init` command to create first block of configuration.

      ```bash
      jiaz config [SUBCOMMAND] [OPTIONS]
      ```

  - **📖 Visit [here](jiaz/commands/config/README.md), for detailed configuration documentation.**

- ### 📊 Data Analysis  

  - Use `jiaz analyze` commands to analyze JIRA data with AI-powered features.

      ```bash
      jiaz analyze [SUBCOMMAND] [OPTIONS]
      ```

  - **📖 Visit [here](jiaz/commands/analyze/README.md), for detailed configuration documentation.**

> **💡 Tip**: Use `--help` with any command to see detailed usage information
