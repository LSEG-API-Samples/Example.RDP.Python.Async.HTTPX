# HTTPX Python — Project Setup Instructions

## Overview

This file contains step-by-step instructions for setting up an HTTPX-based Python project that connects to the Refinitiv Data Platform (RDP) REST API. Follow every step in order. All steps are mandatory unless marked optional.

**AI Assistant Note:** Execute each step sequentially. Do not skip steps or combine steps unless explicitly told to do so. All file paths are relative to the project root directory.

---

## Prerequisites

Verify the following are available before starting:

- Python 3.9 or higher (verify with `python --version`)
- Git (verify with `git --version`)
- Network access to PyPI

---

## Expected Project Structure

After completing all steps, the project root should look like this:

```
RDP_HTTPX/
├── .github/
│   └── copilot-instruction.md
├── .venv/                  # virtual environment (not committed to Git)
├── src/
│   ├── .env                # local secrets (not committed to Git)
│   └── .env.example        # template committed to Git
├── .gitignore
├── LICENSE.md
└── requirements.txt
```

---

## Part 1: Set Up the Python Virtual Environment

### Step 1 — Create the virtual environment

Run in the project root directory:

```bash
python -m venv .venv
```

> This creates a `.venv/` folder containing an isolated Python environment.

---

### Step 2 — Activate the virtual environment

Choose the command that matches the current OS and shell:

| OS / Shell | Command |
|---|---|
| Windows — PowerShell | `.\.venv\Scripts\Activate.ps1` |
| Windows — CMD | `.venv\Scripts\activate.bat` |
| macOS / Linux — bash/zsh | `source .venv/bin/activate` |

After activation, the terminal prompt should show `(.venv)`.

---

### Step 3 — Update pip inside the virtual environment

Use the virtual environment's Python binary directly to avoid using a system-level pip:

- **Windows:**
  ```powershell
  .\.venv\Scripts\python.exe -m pip install --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --trusted-host pypi.org --no-cache-dir --upgrade pip
  ```
- **macOS / Linux:**
  ```bash
  .venv/bin/python -m pip install --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --trusted-host pypi.org --no-cache-dir --upgrade pip
  ```

---

### Step 4 — Install required packages

Install `httpx` and `python-dotenv` into the virtual environment:

- **Windows:**
  ```powershell
  .\.venv\Scripts\pip.exe install --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --trusted-host pypi.org --no-cache-dir httpx python-dotenv
  ```
- **macOS / Linux:**
  ```bash
  .venv/bin/pip install --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --trusted-host pypi.org --no-cache-dir httpx python-dotenv
  ```

---

### Step 5 — Save dependencies to `requirements.txt`

Generate `requirements.txt` in UTF-8 encoding at the project root:

- **Windows (PowerShell):**
  ```powershell
  .\.venv\Scripts\pip.exe freeze | Out-File -Encoding utf8 requirements.txt
  ```
- **Windows (CMD):**
  ```cmd
  .venv\Scripts\pip.exe freeze > requirements.txt
  ```
- **macOS / Linux:**
  ```bash
  .venv/bin/pip freeze > requirements.txt
  ```

---

### Step 6 — Create the `src` folder

Create the `src/` directory in the project root:

```bash
mkdir src
```

---

### Step 7 — Create `.env` and `.env.example` files

Create both files inside the `src/` folder with exactly the following content:

**File path:** `src/.env` and `src/.env.example`

```env
RDP_BASE_URL=https://api.refinitiv.com
RDP_AUTH_URL=/auth/oauth2/v1/token
RDP_AUTH_REVOKE_URL=/auth/oauth2/v1/revoke


MACHINEID_RDP=<RDP Machine-ID>
PASSWORD_RDP=<RDP Password>
APPKEY_RDP=<RDP AppKey>
```

> **Important:** `src/.env` holds real credentials and must not be committed to Git. `src/.env.example` is a template and will be committed.

### Step 8 -- Create VS Code launch.json file

Create the `.vscode/` directory in the project root:

```bash
mkdir .vscode
```

Next, create file name `launch.json` in `.vscode/` folder with the following content.

```json
{
    // Use IntelliSense to learn about possible attributes.
    // Hover to view descriptions of existing attributes.
    // For more information, visit: https://go.microsoft.com/fwlink/?linkid=830387
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python Debugger: Current File",
            "type": "debugpy",
            "request": "launch",
            "program": "${file}",
            "console": "integratedTerminal"
        }
    ]
}
```

> **Important:** `.vscode/launch.json` must be committed to Git.

---

## Part 2: Initialize the Git Repository

### Step 8 — Add `LICENSE.md`

Create `LICENSE.md` in the project root containing the full [Apache 2.0 license text](https://www.apache.org/licenses/LICENSE-2.0):

Then change the `Copyright [yyyy] [name of copyright owner]` line to `Copyright 2026 LSEG`.

---

### Step 9 — Add `.gitignore`

Create a `.gitignore` file in the project root suitable for Python projects. Use the template from [gitignore.io for Python](https://www.toptal.com/developers/gitignore/api/python).

The `.gitignore` **must** include the following entries (add them if not already present):

```gitignore
# Virtual environment
.venv/

# Environment secrets
.env
```

---

### Step 10 — Initialize Git and create the initial commit

Run the following commands in order from the project root:

```bash
git init
git add .
git commit -m "init main"
```

---

### Step 11 — Rename the default branch to `main`

```bash
git branch -m master main
```

Verify the branch name:

```bash
git branch
```

Expected output: `* main`

---

## Part 3: Validation

### Step 12 — Run a package smoke test

Run a one-line Python check to confirm `httpx` and `python-dotenv` are installed and import correctly.

- **Windows (PowerShell/CMD):**
  ```powershell
  .\.venv\Scripts\python.exe -c "import httpx, dotenv, importlib.metadata as m; print('httpx', httpx.__version__); print('python-dotenv', m.version('python-dotenv')); print('dotenv module path', dotenv.__file__)"
  ```
- **macOS / Linux:**
  ```bash
  .venv/bin/python -c "import httpx, dotenv, importlib.metadata as m; print('httpx', httpx.__version__); print('python-dotenv', m.version('python-dotenv')); print('dotenv module path', dotenv.__file__)"
  ```

If successful, output should include:

- `httpx` followed by a version number
- `python-dotenv` followed by a version number
- `dotenv module path` pointing to the virtual environment site-packages directory

