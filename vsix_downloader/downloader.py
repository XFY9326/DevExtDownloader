import asyncio
from collections.abc import Collection
from pathlib import Path

import aiofile
import httpx
from tqdm.asyncio import tqdm

from .api import VSCodeExtensionAPI
from .data import VSCodeExtension, VSCodeExtensionVersion
from .utils import download_file, get_latest_extension_version


async def _run_download_task(
        client: httpx.AsyncClient,
        extension: VSCodeExtension,
        version: VSCodeExtensionVersion,
        target_dir: Path,
        temp_dir: Path,
) -> None:
    extension_dir = target_dir.joinpath(extension.extension_name)
    extension_meta_name = f"{extension.extension_name}_{version.version}_{version.target_platform}.json"
    async with aiofile.async_open(extension_dir.joinpath(extension_meta_name), "w", encoding="utf-8") as f:
        download_meta = VSCodeExtension(
            extension_id=extension.extension_id,
            extension_name=extension.extension_name,
            display_name=extension.display_name,
            versions=(version,)
        )
        await f.write(download_meta.to_json(indent=2, ensure_ascii=True))
    await download_file(
        client,
        version.package_url,
        extension_dir,
        f"{extension.extension_name}_{version.version}_{version.target_platform}.vsix",
        temp_dir
    )


async def download_extensions(
        target_dir: Path,
        temp_dir: Path,
        ext_names: Collection[str],
        target_platform: str | None,
        vscode_version: str | None,
        include_prerelease: bool = False,
):
    if len(ext_names) == 0:
        return

    target_dir.mkdir(parents=True, exist_ok=True)
    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
        api = VSCodeExtensionAPI(client)
        tasks = [
            asyncio.create_task(api.get_extension(ext_name))
            for ext_name in ext_names
        ]
        extensions: list[VSCodeExtension] = await tqdm.gather(*tasks, desc="Loading")

        download_tasks = []
        for extension in extensions:
            version = get_latest_extension_version(extension, target_platform, vscode_version, include_prerelease)
            if version is not None:
                download_tasks.append(
                    asyncio.create_task(
                        _run_download_task(
                            client=client,
                            extension=extension,
                            version=version,
                            target_dir=target_dir,
                            temp_dir=temp_dir
                        )
                    )
                )
            else:
                print(f"Warning: No version found for {extension.extension_name}")
        if len(download_tasks) > 0:
            await tqdm.gather(*download_tasks, desc="Downloading")
