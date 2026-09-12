import hashlib
import re
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

from dev_ext_downloader.common.render import iter_json_metadata
from dev_ext_downloader.common.tools import get_download_dir

from .data import JetbrainsDownloadPlugin, JetbrainsDownloadVersion, JetbrainsPlugin


async def iter_meta_data(
    download_dir: Path, is_flatten: bool
) -> AsyncGenerator[JetbrainsDownloadPlugin, Any]:
    async for metadata in iter_json_metadata(
        download_dir, is_flatten, JetbrainsDownloadPlugin.from_json
    ):
        yield metadata


def get_download_file_name(plugin: JetbrainsPlugin, extension: str) -> str:
    name = re.sub(r"\s+", "-", plugin.name.lower())
    prefix = f"{name}_{plugin.version.version}"
    suffix_text = f"{prefix}-{plugin.version.since_build}-{plugin.version.until_build}"
    suffix = hashlib.sha256(suffix_text.encode("utf-8")).hexdigest()[:8]
    return f"{prefix}_{suffix}{extension}"


def get_download_file_dir(download_dir: Path, is_flatten: bool, plugin_id: str) -> Path:
    return get_download_dir(download_dir, is_flatten, plugin_id)


def get_download_file_path(
    download_dir: Path,
    is_flatten: bool,
    plugin_meta_data: JetbrainsDownloadPlugin,
    plugin_version: JetbrainsDownloadVersion,
) -> Path:
    return (
        get_download_file_dir(download_dir, is_flatten, plugin_meta_data.id)
        / plugin_version.download_file_name
    )
