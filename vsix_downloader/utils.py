import hashlib
import os
import re
from pathlib import Path

import aiofile
import aioshutil
import httpx
import semantic_version

from vsix_downloader.data import VSCodeExtension, VSCodeExtensionVersion, VersionFilterOptions


def get_latest_extension_version(
        extension: VSCodeExtension,
        version_filter_options: VersionFilterOptions
) -> VSCodeExtensionVersion | None:
    for version in extension.versions:
        if not version_filter_options.include_prerelease and version.prerelease:
            continue
        if version_filter_options.target_platform and \
                version.target_platform and \
                version.target_platform != version_filter_options.target_platform:
            continue
        if version_filter_options.vscode_version and version.code_engine:
            target_vscode_version = semantic_version.Version(version_filter_options.vscode_version)
            if not semantic_version.NpmSpec(version.code_engine).match(target_vscode_version):
                continue
        return version
    return None


def _get_file_name_from_header(headers: httpx.Headers) -> str | None:
    content_disposition = headers.get("Content-Disposition")
    if content_disposition:
        match = re.search(r'filename="(.+)"', content_disposition)
        if match:
            return match.group(1)
    return None


def _get_file_name_from_response(response: httpx.Response) -> str | None:
    result = _get_file_name_from_header(response.headers)
    if result is None:
        url_path = response.request.url.path
        if url_path.endswith("/"):
            return None
        else:
            result: str = os.path.basename(url_path)
    return result.strip()


async def download_file(
        client: httpx.AsyncClient,
        url: str | httpx.URL,
        target_dir: Path,
        file_name: str | None = None,
        temp_dir: Path | None = None
) -> Path:
    temp_dir = target_dir if temp_dir is None else temp_dir
    temp_dir.mkdir(parents=True, exist_ok=True)
    target_dir.mkdir(parents=True, exist_ok=True)

    async with client.stream("GET", url) as response:
        file_name = _get_file_name_from_response(response.headers) if file_name is None else file_name.strip()
        if file_name is None or len(file_name) == 0:
            raise ValueError("No file name")

        target_tmp_path = temp_dir.joinpath(hashlib.sha1(str(url).encode("utf-8")).hexdigest())
        target_final_path = target_dir.joinpath(file_name)
        async with aiofile.async_open(target_tmp_path, mode="wb") as f:
            async for chunk in response.aiter_bytes():
                await f.write(chunk)

        await aioshutil.move(target_tmp_path, target_final_path)
        return target_final_path
