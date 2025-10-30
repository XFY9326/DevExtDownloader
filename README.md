# Dev ext downloader

Download extensions from Visual Studio Marketplace and Jetbrains Marketplace

## Requirements

Python 3.10+

## Features

- Simply configure to download the latest extension
- Improving download speed using asyncio
- Supports incremental download and complete file download
- Supports generating metadata for downloaded files
- Generate simple static html page for downloaded extensions

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

## VSIX Downloader

Download VSIX packages from Visual Studio Marketplace

**Only support Visual Studio Code Extensions**

### Features

- Support custom download platforms and compatible VSCode versions
- Support for filtering pre-release versions

### Usage

Set VSIX packages (Modify `vsix.py`):

```python
from pathlib import Path

from dev_ext_downloader.vscode import TargetPlatformType, VSCodeExt

# Download dir
DOWNLOAD_DIR: Path = Path("./downloads/VSCode")

# Download temp dir
TEMP_DIR: Path = DOWNLOAD_DIR / ".temp"

# Task spec path
TASK_SPEC_PATH: Path = DOWNLOAD_DIR / "task-spec.json"

# Skip if exists or not
# If exists, skip download
SKIP_IF_EXISTS: bool = True

# Only keep latest version
# Depends on metadata
KEEP_ONLY_LATEST: bool = True

# Download concurrency
DOWNLOAD_CONCURRENCY: int = 8

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
TARGET_PLATFORM: tuple[TargetPlatformType, ...] | None = (
    TargetPlatformType.UNIVERSAL,
    TargetPlatformType.WIN32_X64,
    TargetPlatformType.LINUX_X64
)

# Target platform fallback or None
TARGET_PLATFORM_FALLBACK: TargetPlatformType | None = TargetPlatformType.UNIVERSAL

# Required VSCode version or None
# It will download the latest version if not set
VSCODE_VERSION: str | None = "1.92.0"

# Include prerelease or not
# If not set, it will download the latest prerelease version
INCLUDE_PRERELEASE: bool = True

# VSIX packages ext id list
# Example: https://marketplace.visualstudio.com/items?itemName=ms-python.python
# [ext_id] is ms-python.python
VSIX_LIST: list[str | VSCodeExt] = [
    "ms-python.python"
]
```

Run script to download all latest compatible extensions:

```shell
uv run vscode.py
```

## Jetbrains Downloader

Download Jetbrains plugins from Jetbrains Marketplace

### Features

- Support custom download compatible Jetbrains IDE versions
- Support generating `updatePlugins.xml` file

### Usage

Set Jetbrains plugins (Modify `jetbrains.py`):

```python
from pathlib import Path
from dev_ext_downloader.jetbrains import JetbrainsDef

# Download dir
DOWNLOAD_DIR: Path = Path("./downloads/Jetbrains")

# Download temp dir
TEMP_DIR: Path = DOWNLOAD_DIR / ".temp"

# Task spec path
TASK_SPEC_PATH: Path = DOWNLOAD_DIR / "task-spec.json"

# Skip if exists or not
# If exists, skip download
SKIP_IF_EXISTS: bool = True

# Only keep latest version
# Depends on metadata
KEEP_ONLY_LATEST: bool = True

# Download concurrency
DOWNLOAD_CONCURRENCY: int = 8

# No metadata or not
# Generate [ext_id.json] before download
NO_METADATA: bool = False

# Flatten dir or not
# No flatten dir:
# [download_dir]
#     └── [plugin_id]
#         ├── [plugin_id_fixed.zip]
#         └── [plugin_id.json]
# Flatten dir:
# [download_dir]
#     ├── [plugin_id_fixed.zip]
#     └── [plugin_id.json]
FLATTEN_DIR: bool = False

# Target build version or None for latest
# Example: IC-243.22562.13 or IC-243 or 243
TARGET_BUILD_VERSION: str | None = "IC-243.22562.13"

# Jetbrains plugin id list
# Example: https://plugins.jetbrains.com/plugin/7495--ignore
# [ext_id] is '7495'
PLUGINS_LIST: list[str | JetbrainsDef] = ["7495"]

# For generating updatePlugins.xml
PLUGINS_DOWNLOAD_BASE_URL: str | None = "http://localhost:8080"
```

Run script to download all latest compatible extensions:

```shell
uv run jetbrains.py
```
