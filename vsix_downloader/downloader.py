import asyncio
from typing import Collection

import aiofile
import httpx
from tqdm.asyncio import tqdm

from .api import VSCodeExtensionAPI
from .data import VSCodeExtension, VSCodeExtensionVersion, DownloadOptions, VersionFilterOptions
from .utils import download_file, get_latest_extension_version


async def _run_download_task(
        client: httpx.AsyncClient,
        ext_name: str,
        extension: VSCodeExtension,
        version: VSCodeExtensionVersion,
        download_options: DownloadOptions
) -> None:
    if download_options.flatten_dir:
        extension_dir = download_options.target_dir
    else:
        extension_dir = download_options.target_dir.joinpath(ext_name)
    extension_dir.mkdir(parents=True, exist_ok=True)

    if version.target_platform:
        download_name = f"{ext_name}-{version.version}@{version.target_platform}"
    else:
        download_name = f"{ext_name}-{version.version}"

    meta_data_path = extension_dir.joinpath(f"{download_name}.json")
    if not download_options.no_metadata and (not download_options.skip_if_exists or not meta_data_path.exists()):
        async with aiofile.async_open(meta_data_path, "w", encoding="utf-8") as f:
            download_meta = VSCodeExtension(
                extension_id=extension.extension_id,
                extension_name=extension.extension_name,
                display_name=extension.display_name,
                versions=(version,)
            )
            await f.write(download_meta.to_json(indent=2, ensure_ascii=True))
    if not download_options.skip_if_exists or not extension_dir.joinpath(f"{download_name}.vsix").exists():
        await download_file(
            client,
            version.package_url,
            extension_dir,
            f"{download_name}.vsix",
            download_options.temp_dir
        )


async def download_latest_extensions(
        ext_names: Collection[str],
        download_options: DownloadOptions,
        version_filter_options: VersionFilterOptions
):
    if len(ext_names) == 0:
        return

    download_options.target_dir.mkdir(parents=True, exist_ok=True)
    async with httpx.AsyncClient(timeout=httpx.Timeout(15.0)) as client:
        api = VSCodeExtensionAPI(client)
        extensions: dict[str, VSCodeExtension] = await api.get_extensions(ext_names)
        missing_extensions = set(ext_names) - set(extensions.keys())
        if len(missing_extensions) > 0:
            print(f"Warning: No extension found for {', '.join(missing_extensions)}")

        download_tasks = []
        for ext_name, extension in extensions.items():
            version = get_latest_extension_version(extension, version_filter_options)
            if version is not None:
                download_tasks.append(
                    asyncio.create_task(
                        _run_download_task(
                            client=client,
                            ext_name=ext_name,
                            extension=extension,
                            version=version,
                            download_options=download_options
                        )
                    )
                )
            else:
                print(f"Warning: No version found for {extension.extension_name}")
        if len(download_tasks) > 0:
            await tqdm.gather(*download_tasks, desc="Downloading")
