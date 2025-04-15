import asyncio
import shutil
from pathlib import Path

from vsix_downloader import download_extensions

DOWNLOAD_DIR: Path = Path("./downloads")
TEMP_DIR: Path = DOWNLOAD_DIR.joinpath("./.temp")
TARGET_PLATFORM: str | None = "win32-x64"
VSCODE_VERSION: str | None = "1.92.0"
INCLUDE_PRERELEASE: bool = False
VSIX_LIST: list[str] = [
    "ms-python.python"
]


async def main() -> None:
    await download_extensions(
        DOWNLOAD_DIR,
        TEMP_DIR,
        VSIX_LIST,
        TARGET_PLATFORM,
        VSCODE_VERSION,
        INCLUDE_PRERELEASE
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    finally:
        shutil.rmtree(TEMP_DIR)
