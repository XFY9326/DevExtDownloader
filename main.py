import asyncio
import shutil
from pathlib import Path

from vsix_downloader import download_extensions
from vsix_downloader.data import VersionFilterOptions, DownloadOptions

DOWNLOAD_DIR: Path = Path("./downloads")
TEMP_DIR: Path = DOWNLOAD_DIR.joinpath("./.temp")
SKIP_IF_EXISTS: bool = True
NO_METADATA: bool = True
FLATTEN_DIR: bool = True

TARGET_PLATFORM: str | None = "win32-x64"
VSCODE_VERSION: str | None = "1.97.2"
INCLUDE_PRERELEASE: bool = False

VSIX_LIST: list[str] = [
    "ms-python.python"
]


async def main() -> None:
    await download_extensions(
        ext_names=VSIX_LIST,
        download_options=DownloadOptions(
            target_dir=DOWNLOAD_DIR,
            temp_dir=TEMP_DIR,
            skip_if_exists=SKIP_IF_EXISTS,
            no_metadata=NO_METADATA,
            flatten_dir=FLATTEN_DIR,
        ),
        version_filter_options=VersionFilterOptions(
            target_platform=TARGET_PLATFORM,
            vscode_version=VSCODE_VERSION,
            include_prerelease=INCLUDE_PRERELEASE,
        ),
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    finally:
        shutil.rmtree(TEMP_DIR, ignore_errors=True)
