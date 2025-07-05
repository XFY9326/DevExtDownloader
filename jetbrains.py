import asyncio
import shutil
from pathlib import Path

from dev_ext_downloader.common.models import DownloadOptions
from dev_ext_downloader.jetbrains import (
    download_latest_extensions,
    generate_update_plugins_xml,
    JetbrainsDef, generate_index_html,
)

# Download dir
DOWNLOAD_DIR: Path = Path("./downloads/jetbrains")

# Download temp dir
TEMP_DIR: Path = DOWNLOAD_DIR.joinpath("./.temp")

# Task spec path
TASK_SPEC_PATH: Path = DOWNLOAD_DIR.joinpath("task-spec.json")

# Skip if exists or not
# If exists, skip download
SKIP_IF_EXISTS: bool = True

# Only keep latest version
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

# Target build version or None for latest
# Example: IC-243.22562.13 or IC-243 or 243
TARGET_BUILD_VERSION: str | None = "IC-243.22562.13"

# Jetbrains plugin id list
# Example: https://plugins.jetbrains.com/plugin/7495--ignore
# [ext_id] is '7495'
PLUGINS_LIST: list[str | JetbrainsDef] = ["7495"]

# For generating updatePlugins.xml
PLUGINS_DOWNLOAD_BASE_URL: str | None = "http://localhost:8080"


async def main() -> None:
    await download_latest_extensions(
        plugins_def=PLUGINS_LIST,
        target_dir=DOWNLOAD_DIR,
        temp_dir=TEMP_DIR,
        concurrency=DOWNLOAD_CONCURRENCY,
        task_spec_path=TASK_SPEC_PATH,
        default_target_build_version=TARGET_BUILD_VERSION,
        default_download_options=DownloadOptions(
            skip_if_exists=SKIP_IF_EXISTS,
            no_metadata=NO_METADATA,
            flatten_dir=FLATTEN_DIR,
            keep_only_latest=KEEP_ONLY_LATEST,
        ),
    )
    if not NO_METADATA:
        await generate_index_html(
            download_dir=DOWNLOAD_DIR,
            is_flatten=FLATTEN_DIR,
        )
    if not NO_METADATA and PLUGINS_DOWNLOAD_BASE_URL is not None:
        await generate_update_plugins_xml(
            base_url=PLUGINS_DOWNLOAD_BASE_URL,
            download_dir=DOWNLOAD_DIR,
            is_flatten=FLATTEN_DIR,
        )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    finally:
        shutil.rmtree(TEMP_DIR, ignore_errors=True)
