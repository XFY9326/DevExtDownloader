# VSIX Downloader

Download VSIX packages from Visual Studio Marketplace

**Only support Vistual Studio Code Extensions**

## Requirements

Python 3.10+

## Features

 - Simply configure to download the latest extension
 - Support custom download platforms and compatible VSCode versions
 - Support for filtering pre-release versions
 - Improving download speed using asyncio
 - Supports incremental download and complete file download
 - Supports generating metadata for downloaded files

## Usage

Install `uv` according to the [official doc](https://docs.astral.sh/uv/getting-started/installation/)

Or maybe you don't want to read those documents:

```shell
pip install pipx

pipx ensurepath

pipx install uv
```

Init project venv (Optional):

```shell
uv sync
```

Set VSIX packages (Modify `main.py`):

```python
from pathlib import Path

# Download dir
DOWNLOAD_DIR: Path = Path("./downloads")

# Download temp dir
TEMP_DIR: Path = DOWNLOAD_DIR.joinpath("./.temp")

# Skip if exists or not
# If exists, skip download
SKIP_IF_EXISTS: bool = False

# No metadata or not
# Generate [ext_id.json] before download
NO_METADATA: bool = False

# Flatten dir or not
# No flatten dir:
# [download_dir]
#     └── [ext_id]
#         ├── [ext_id.vsix]
#         └── [ext_id.json]
# Flatten dir:
# [download_dir]
#     ├── [ext_id.vsix]
#     └── [ext_id.json]
FLATTEN_DIR: bool = False

# Target platform or None
# Currently available platforms are: win32-x64, win32-arm64, linux-x64, linux-arm64, linux-armhf, alpine-x64, alpine-arm64, darwin-x64, darwin-arm64 and web
TARGET_PLATFORM: str | None = "win32-x64"

# Required VSCode version or None
# It will download the latest version if not set
VSCODE_VERSION: str | None = "1.92.0"

# Include prerelease or not
# If not set, it will download the latest prerelease version
INCLUDE_PRERELEASE: bool = False

# VSIX packages ext id list
# Example: https://marketplace.visualstudio.com/items?itemName=ms-python.python
# [ext_id] is ms-python.python
VSIX_LIST: list[str] = [
    "ms-python.python"
]
```

Run script to download all latest compatible extensions:

```shell
uv run main.py
```
