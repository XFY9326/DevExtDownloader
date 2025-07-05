import hashlib
import re
from pathlib import Path
from typing import AsyncGenerator, Any

import aiofile

from dev_ext_downloader.common.tools import iter_meta_data_json
from .data import JetbrainsDownloadPlugin, JetbrainsDownloadVersion, JetbrainsPlugin


async def iter_meta_data(
        download_dir: Path, is_flatten: bool
) -> AsyncGenerator[JetbrainsDownloadPlugin, Any]:
    for meta_path in iter_meta_data_json(download_dir, is_flatten):
        async with aiofile.async_open(meta_path, "r", encoding="utf-8") as f:
            try:
                yield JetbrainsDownloadPlugin.from_json(await f.read())
            except Exception as e:
                print(f"Warning: meta file {meta_path} could not be read.", e)


def get_download_file_name(plugin: JetbrainsPlugin, extension: str) -> str:
    name = re.sub(r"\s+", "-", plugin.name.lower())
    prefix = f"{name}_{plugin.version.version}"
    suffix_text = f"{prefix}-{plugin.version.since_build}-{plugin.version.until_build}"
    suffix = hashlib.sha256(suffix_text.encode("utf-8")).hexdigest()[:8]
    return f"{prefix}_{suffix}{extension}"


def get_download_file_path(
        download_dir: Path,
        is_flatten: bool,
        plugin_meta_data: JetbrainsDownloadPlugin,
        plugin_version: JetbrainsDownloadVersion
) -> Path:
    if is_flatten:
        file_path = download_dir / plugin_version.download_file_name
    else:
        file_path = (
                download_dir
                / plugin_meta_data.id
                / plugin_version.download_file_name
        )
    return file_path
