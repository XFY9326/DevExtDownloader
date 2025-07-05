import asyncio
from pathlib import Path
from typing import Collection

import aiofile
import httpx
from tqdm.asyncio import tqdm

from dev_ext_downloader.common.models import DownloadOptions
from dev_ext_downloader.common.tools import download_file
from .api import JetbrainsPluginAPI
from .data import (
    JetbrainsDef,
    JetbrainsPlugin,
    JetbrainsDownloadPlugin,
    JetbrainsDownloadVersion,
)


async def _run_download_task(
        client: httpx.AsyncClient,
        target_dir: Path,
        temp_dir: Path,
        plugin: JetbrainsPlugin,
        download_options: DownloadOptions,
) -> None:
    if download_options.flatten_dir:
        plugin_dir = target_dir
    else:
        plugin_dir = target_dir / plugin.id
    plugin_dir.mkdir(parents=True, exist_ok=True)

    download_file_path = await download_file(
        client=client,
        url=plugin.version.download_url,
        target_dir=plugin_dir,
        temp_dir=temp_dir,
        skip_if_exists=download_options.skip_if_exists,
    )

    if not download_options.no_metadata:
        meta_data_path = plugin_dir / f"{plugin.id}.json"
        has_old_meta_data = meta_data_path.is_file()
        async with aiofile.async_open(meta_data_path, "w+", encoding="utf-8") as f:
            version = JetbrainsDownloadVersion(
                version=plugin.version.version,
                change_notes=plugin.version.change_notes,
                size=plugin.version.size,
                updated_date=plugin.version.updated_date,
                since_build=plugin.version.since_build,
                until_build=plugin.version.until_build,
                download_url=plugin.version.download_url,
                download_file_name=download_file_path.name,
                depends=plugin.version.depends,
            )
            if not has_old_meta_data or download_options.keep_only_latest:
                version_list = [version]
            else:
                try:
                    version_list = [
                        version,
                        *JetbrainsDownloadPlugin.from_json(await f.read()).versions,
                    ]
                except Exception as e:
                    print(
                        f"Warning: Can't load old meta data from {plugin.id}.",
                        e,
                    )
                    version_list = [version]
            version_list.sort(key=lambda i: i.updated_date, reverse=True)
            download_meta = JetbrainsDownloadPlugin(
                id=plugin.id,
                name=plugin.name,
                description=plugin.description,
                vendor=plugin.vendor,
                category=plugin.category,
                tags=plugin.tags,
                versions=tuple(version_list),
            )
            await f.write(download_meta.to_json(indent=2, ensure_ascii=True))

    if download_options.keep_only_latest:
        for f in plugin_dir.iterdir():
            if f.is_file() and f.suffix != ".json" and f != download_file_path:
                f.unlink()


async def _download_task(
        semaphore: asyncio.Semaphore,
        client: httpx.AsyncClient,
        target_dir: Path,
        temp_dir: Path,
        plugin: JetbrainsPlugin,
        download_options: DownloadOptions,
) -> None:
    async with semaphore:
        await _run_download_task(client, target_dir, temp_dir, plugin, download_options)


async def _load_data_task(
        semaphore: asyncio.Semaphore, api: JetbrainsPluginAPI, plugin_def: JetbrainsDef
) -> tuple[str, JetbrainsPlugin] | None:
    async with semaphore:
        plugins = await api.list_plugins(
            plugin_def.plugin_id, plugin_def.target_build_version
        )
    if len(plugins) == 0:
        print(
            f"No plugin '{plugin_def.plugin_id}' found for build '{plugin_def.target_build_version}'"
        )
        return None
    return plugin_def.plugin_id, plugins[0]


async def download_latest_extensions(
        plugins_def: Collection[str | JetbrainsDef],
        target_dir: Path = Path("./downloads/jetbrains/"),
        temp_dir: Path = Path("./downloads/jetbrains/.temp"),
        concurrency: int = 4,
        task_spec_path: Path | None = None,
        default_target_build_version: str | None = None,
        default_download_options: DownloadOptions = DownloadOptions(),
) -> None:
    if len(plugins_def) == 0:
        return

    plugins_spec_dict: dict[str, JetbrainsDef] = {}
    for d in plugins_def:
        plugins_spec_dict[d.plugin_id if isinstance(d, JetbrainsDef) else str(d)] = (
            JetbrainsDef(
                plugin_id=d.plugin_id,
                target_build_version=d.target_build_version
                                     or default_target_build_version,
                download_options=d.download_options or default_download_options,
            )
            if isinstance(d, JetbrainsDef)
            else JetbrainsDef(
                plugin_id=d,
                target_build_version=default_target_build_version,
                download_options=default_download_options,
            )
        )

    target_dir.mkdir(parents=True, exist_ok=True)
    temp_dir.mkdir(parents=True, exist_ok=True)

    async with httpx.AsyncClient(timeout=httpx.Timeout(15.0)) as client:
        api = JetbrainsPluginAPI(client)
        semaphore = asyncio.Semaphore(concurrency)

        load_data_tasks = [
            asyncio.create_task(
                _load_data_task(semaphore=semaphore, api=api, plugin_def=plugin_def)
            )
            for plugin_def in plugins_spec_dict.values()
        ]

        loaded_data: dict[str, JetbrainsPlugin] = {
            i[0]: i[1]
            for i in await tqdm.gather(*load_data_tasks, desc="Loading data")
            if i is not None
        }

        download_tasks = [
            asyncio.create_task(
                _download_task(
                    semaphore=semaphore,
                    client=client,
                    target_dir=target_dir,
                    temp_dir=temp_dir,
                    plugin=v,
                    download_options=plugins_spec_dict[k].download_options,
                )
            )
            for k, v in loaded_data.items()
        ]
        if len(download_tasks) > 0:
            await tqdm.gather(*download_tasks, desc="Downloading")

    if task_spec_path:
        task_spec_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofile.async_open(task_spec_path, "w", encoding="utf-8") as f:
            schema = JetbrainsDef.schema(many=True)
            await f.write(
                schema.dumps(
                    [v for k, v in plugins_spec_dict.items() if k in loaded_data],
                    indent=2,
                    ensure_ascii=False,
                )
            )
