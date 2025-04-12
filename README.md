<p align="center">
  <img src="https://img.shields.io/badge/jiaz-CLI-blueviolet?style=for-the-badge&logo=python&logoColor=white" alt="jiaz CLI Badge"/>
</p>

# jiaz

**`jiaz`** is a cross-platform Python CLI assistant for analyzing JIRA data.

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

You can build and run `jiaz` locally from source using two approaches:

---

#### 🅰️ A. Using Python (Direct Setup)

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

#### 🅱️ B. Build Binary Locally using pip and pyinstaller


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

#### 🅲 C. Build Binary Using Container - Only for Linux based OS

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

## 🧪 Usage

After installation, run:

```bash
jiaz config set api_token abc123
jiaz config get api_token
jiaz config list
```

Or from Python env:

```bash
python -m jiaz config list
```

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
