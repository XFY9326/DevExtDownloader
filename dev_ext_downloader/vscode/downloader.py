import asyncio
from pathlib import Path
from typing import Collection

import aiofile
import httpx
from tqdm.asyncio import tqdm

from dev_ext_downloader.common.models import DownloadOptions
from dev_ext_downloader.common.token_locker import TokenLock
from dev_ext_downloader.common.tools import download_file
from .api import VSCodeExtensionAPI
from .data import (
    VSCodeExt,
    VSCodeExtension,
    VSCodeExtensionVersion,
    VSCodeExtFilterOptions,
)
from .utils import get_download_file_name, get_latest_extension_versions, get_download_file_dir

_DOWNLOAD_META_TOKEN_LOCK = TokenLock()


def _merge_versions(
        new_version: VSCodeExtensionVersion,
        old_versions: tuple[VSCodeExtensionVersion, ...]
) -> list[VSCodeExtensionVersion]:
    old_versions = [
        i
        for i in old_versions
        if i.version != new_version.version or i.target_platform != new_version.target_platform
    ]
    return [new_version] + old_versions


async def _run_download_task(
        client: httpx.AsyncClient,
        target_dir: Path,
        temp_dir: Path,
        extension: VSCodeExtension,
        version: VSCodeExtensionVersion,
        download_options: DownloadOptions,
) -> None:
    extension_dir = get_download_file_dir(target_dir, download_options.flatten_dir, extension)
    extension_dir.mkdir(parents=True, exist_ok=True)

    await download_file(
        client=client,
        url=version.package_url,
        target_dir=extension_dir,
        file_name=get_download_file_name(extension, version),
        temp_dir=temp_dir,
        skip_if_exists=download_options.skip_if_exists,
    )

    meta_data_path = extension_dir / f"{extension.unified_name}.json"
    if download_options.no_metadata:
        if meta_data_path.is_file():
            meta_data_path.unlink(missing_ok=True)
    else:
        async with _DOWNLOAD_META_TOKEN_LOCK.lock(str(meta_data_path)):
            async with aiofile.async_open(meta_data_path, "a+", encoding="utf-8") as f:
                has_old_meta_data = meta_data_path.is_file()
                version_list: list[VSCodeExtensionVersion]
                if not has_old_meta_data:
                    version_list = [version]
                else:
                    try:
                        f.seek(0)
                        exists_extension = VSCodeExtension.from_json(await f.read())
                        version_list = _merge_versions(version, exists_extension.versions)
                    except Exception as e:
                        print(f"Downloader warning: Can't load old meta data for {extension.unified_name}.", e)
                        exists_extension = None
                        version_list = [version]
                    if exists_extension and download_options.keep_only_latest:
                        outdated_versions: list[VSCodeExtensionVersion] = sorted([
                            v
                            for v in version_list
                            if v.target_platform == version.target_platform
                        ], key=lambda i: i.sort_key, reverse=True)[1:]
                        for v in outdated_versions:
                            old_file_path = extension_dir / get_download_file_name(exists_extension, v)
                            old_file_path.unlink(missing_ok=True)
                            version_list.remove(v)

                version_list.sort(key=lambda i: i.sort_key, reverse=True)
                download_meta = VSCodeExtension(
                    extension_id=extension.extension_id,
                    extension_name=extension.extension_name,
                    display_name=extension.display_name,
                    publisher_id=extension.publisher_id,
                    publisher_name=extension.publisher_name,
                    publisher_display_name=extension.publisher_display_name,
                    short_description=extension.short_description,
                    categories=extension.categories,
                    versions=tuple(version_list),
                )
                await f.file.truncate(0)
                f.seek(0)
                await f.write(download_meta.to_json(indent=2, ensure_ascii=False))
                await f.flush(sync_metadata=True)


async def _download_task(
        semaphore: asyncio.Semaphore,
        client: httpx.AsyncClient,
        target_dir: Path,
        temp_dir: Path,
        extension: VSCodeExtension,
        version: VSCodeExtensionVersion,
        download_options: DownloadOptions,
) -> None:
    async with semaphore:
        await _run_download_task(
            client, target_dir, temp_dir, extension, version, download_options
        )


async def download_latest_extensions(
        query_ext: Collection[str | VSCodeExt],
        target_dir: Path = Path("./downloads/vscode"),
        temp_dir: Path | None = None,
        concurrency: int = 4,
        task_spec_path: Path | None = None,
        default_download_options: DownloadOptions = DownloadOptions(),
        default_filter_options: VSCodeExtFilterOptions = VSCodeExtFilterOptions(),
) -> None:
    if len(query_ext) == 0:
        return

    ext_spec_dict: dict[str, VSCodeExt] = {}
    for q in query_ext:
        ext_spec_dict[q.ext_id if isinstance(q, VSCodeExt) else str(q)] = (
            VSCodeExt(
                ext_id=q.ext_id,
                download_options=q.download_options or default_download_options,
                filter_options=q.filter_options or default_filter_options,
            )
            if isinstance(q, VSCodeExt)
            else VSCodeExt(
                ext_id=q,
                download_options=default_download_options,
                filter_options=default_filter_options,
            )
        )

    temp_dir = temp_dir if temp_dir is not None else (target_dir / ".temp")
    target_dir.mkdir(parents=True, exist_ok=True)
    temp_dir.mkdir(parents=True, exist_ok=True)

    async with httpx.AsyncClient(timeout=httpx.Timeout(15.0)) as client:
        api = VSCodeExtensionAPI(client)

        extensions: dict[str, VSCodeExtension] = await api.get_extensions(
            ext_spec_dict.keys()
        )
        missing_ext_set = set([i.lower() for i in ext_spec_dict.keys()]) - set(
            [i.lower() for i in extensions.keys()]
        )
        if len(missing_ext_set) > 0:
            print(f"Downloader warning: No extension found for {', '.join(missing_ext_set)}")

        download_tasks = []
        semaphore = asyncio.Semaphore(concurrency)
        for ext_name, extension in extensions.items():
            versions = get_latest_extension_versions(
                extension=extension,
                version_filter_options=ext_spec_dict[ext_name].filter_options,
            )
            if len(versions) > 0:
                for version in versions:
                    download_tasks.append(
                        asyncio.create_task(
                            _download_task(
                                semaphore=semaphore,
                                client=client,
                                target_dir=target_dir,
                                temp_dir=temp_dir,
                                extension=extension,
                                version=version,
                                download_options=ext_spec_dict[ext_name].download_options,
                            )
                        )
                    )
            else:
                print(f"Downloader warning: No matched version found for {extension.unified_name}")
        if len(download_tasks) > 0:
            await tqdm.gather(*download_tasks, desc="Downloading")

    if task_spec_path:
        task_spec_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofile.async_open(task_spec_path, "w", encoding="utf-8") as f:
            schema = VSCodeExt.schema(many=True)
            await f.write(
                schema.dumps(ext_spec_dict.values(), indent=2, ensure_ascii=False)
            )
