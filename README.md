# VSIX Downloader

## Requirements

Python 3.10+

## Usage

Install `uv`:

```shell
pip install pipx

pipx ensurepath

pipx install uv
```

Init project venv:

```shell
uv sync
```

Set VSIX packages (Modify `main.py`):

```python
# Target platform or None
TARGET_PLATFORM: str | None = "win32-x64"

# Required VSCode version or None
VSCODE_VERSION: str | None = "1.92.0"

# Include prerelease or not
INCLUDE_PRERELEASE: bool = False

# VSIX packages id list
# Example: https://marketplace.visualstudio.com/items?itemName=ms-python.python
VSIX_LIST: list[str] = [
    "ms-python.python"
]
```

Run script:

```shell
uv run main.py
```
