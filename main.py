import asyncio
import shutil
from pathlib import Path

from vsix_downloader import download_latest_extensions
from vsix_downloader.data import VSCodeExt, VersionFilterOptions, DownloadOptions
from vsix_downloader.html import generate_index_html

# Download dir
DOWNLOAD_DIR: Path = Path("./downloads")

# Download temp dir
TEMP_DIR: Path = DOWNLOAD_DIR.joinpath("./.temp")

# Task spec path
TASK_SPEC_PATH: Path = DOWNLOAD_DIR.joinpath("task-spec.json")

# Skip if exists or not
# If exists, skip download
SKIP_IF_EXISTS: bool = True

# Only keep latest version
KEEP_ONLY_LATEST: bool = False

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
TARGET_PLATFORM: str | None = "win32-x64"

# Required VSCode version or None
# It will download the latest version if not set
VSCODE_VERSION: str | None = "1.97.2"

# Include prerelease or not
# If not set, it will download the latest prerelease version
INCLUDE_PRERELEASE: bool = True

# VSIX packages id list
# Example: https://marketplace.visualstudio.com/items?itemName=ms-python.python
# [ext_id] is ms-python.python
VSIX_LIST: list[str | VSCodeExt] = [
    "MS-CEINTL.vscode-language-pack-zh-hans",
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-python.debugpy"
]


async def main() -> None:
    await download_latest_extensions(
        query_ext=VSIX_LIST,
        target_dir=DOWNLOAD_DIR,
        temp_dir=TEMP_DIR,
        concurrency=DOWNLOAD_CONCURRENCY,
        task_spec_path=TASK_SPEC_PATH,
        default_download_options=DownloadOptions(
            skip_if_exists=SKIP_IF_EXISTS,
            no_metadata=NO_METADATA,
            flatten_dir=FLATTEN_DIR,
            keep_only_latest=KEEP_ONLY_LATEST
        ),
        default_version_filter_options=VersionFilterOptions(
            target_platform=TARGET_PLATFORM,
            vscode_version=VSCODE_VERSION,
            include_prerelease=INCLUDE_PRERELEASE,
        ),
    )
    if not NO_METADATA:
        await generate_index_html(download_dir=DOWNLOAD_DIR, is_flatten=FLATTEN_DIR)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    finally:
        shutil.rmtree(TEMP_DIR, ignore_errors=True)
