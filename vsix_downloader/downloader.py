import asyncio
from pathlib import Path
from typing import Collection

import aiofile
import httpx
from tqdm.asyncio import tqdm

from .api import VSCodeExtensionAPI
from .data import VSCodeExt, VSCodeExtension, VSCodeExtensionVersion, DownloadOptions, VersionFilterOptions
from .utils import download_file, get_latest_extension_version, get_download_file_name


async def _run_download_task(
        client: httpx.AsyncClient,
        target_dir: Path,
        temp_dir: Path,
        extension: VSCodeExtension,
        version: VSCodeExtensionVersion,
        download_options: DownloadOptions,

) -> None:
    if download_options.flatten_dir:
        extension_dir = target_dir
    else:
        extension_dir = target_dir / extension.unified_name
    extension_dir.mkdir(parents=True, exist_ok=True)

    meta_data_path = extension_dir / f"{extension.unified_name}.json"
    if not download_options.no_metadata and (not download_options.skip_if_exists or not meta_data_path.exists()):
        has_old_meta_data = meta_data_path.is_file()
        async with aiofile.async_open(meta_data_path, "w+", encoding="utf-8") as f:
            if not has_old_meta_data or download_options.keep_only_latest:
                version_list = [version]
            else:
                try:
                    version_list = [version, *VSCodeExtension.from_json(await f.read()).versions]
                except Exception as e:
                    print(f"Warning: Can't load old meta data from {extension.unified_name}.", e)
                    version_list = [version]
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
            await f.write(download_meta.to_json(indent=2, ensure_ascii=True))

    latest_package_path = extension_dir / get_download_file_name(extension, version)
    if not download_options.skip_if_exists or not latest_package_path.exists():
        await download_file(
            client,
            version.package_url,
            extension_dir,
            latest_package_path.name,
            temp_dir
        )
    if download_options.keep_only_latest:
        for old_package in extension_dir.glob("*.vsix"):
            if old_package.is_file() and old_package != latest_package_path:
                old_package.unlink()


async def _download_task(
        semaphore: asyncio.Semaphore,
        client: httpx.AsyncClient,
        target_dir: Path,
        temp_dir: Path,
        extension: VSCodeExtension,
        version: VSCodeExtensionVersion,
        download_options: DownloadOptions
) -> None:
    async with semaphore:
        await _run_download_task(client, target_dir, temp_dir, extension, version, download_options)


async def download_latest_extensions(
        query_ext: Collection[str | VSCodeExt],
        target_dir: Path = Path("./download"),
        temp_dir: Path = Path("./download/.temp"),
        concurrency: int = 4,
        task_spec_path: Path | None = None,
        default_download_options: DownloadOptions = DownloadOptions(),
        default_version_filter_options: VersionFilterOptions = VersionFilterOptions()
) -> None:
    if len(query_ext) == 0:
        return

    ext_spec_dict: dict[str, VSCodeExt] = {}
    for q in query_ext:
        ext_spec_dict[q] = VSCodeExt(
            ext_id=q.ext_id,
            download_options=q.download_options or default_download_options,
            version_filter_options=q.version_filter_options or default_version_filter_options
        ) if isinstance(q, VSCodeExt) else VSCodeExt(
            ext_id=q,
            download_options=default_download_options,
            version_filter_options=default_version_filter_options
        )

    target_dir.mkdir(parents=True, exist_ok=True)
    temp_dir.mkdir(parents=True, exist_ok=True)

    async with httpx.AsyncClient(timeout=httpx.Timeout(15.0)) as client:
        api = VSCodeExtensionAPI(client)

        extensions: dict[str, VSCodeExtension] = await api.get_extensions(ext_spec_dict.keys())
        missing_ext_set = set([i.lower() for i in ext_spec_dict.keys()]) - set([i.lower() for i in extensions.keys()])
        if len(missing_ext_set) > 0:
            print(f"Warning: No extension found for {', '.join(missing_ext_set)}")

        download_tasks = []
        semaphore = asyncio.Semaphore(concurrency)
        for ext_name, extension in extensions.items():
            version = get_latest_extension_version(
                extension=extension,
                version_filter_options=ext_spec_dict[ext_name].version_filter_options
            )
            if version is not None:
                download_tasks.append(
                    asyncio.create_task(
                        _download_task(
                            semaphore=semaphore,
                            client=client,
                            target_dir=target_dir,
                            temp_dir=temp_dir,
                            extension=extension,
                            version=version,
                            download_options=ext_spec_dict[ext_name].download_options
                        )
                    )
                )
            else:
                print(f"Warning: No matched version found for {extension.unified_name}")
        if len(download_tasks) > 0:
            await tqdm.gather(*download_tasks, desc="Downloading")

    if task_spec_path:
        task_spec_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofile.async_open(task_spec_path, "w", encoding="utf-8") as f:
            schema = VSCodeExt.schema(many=True)
            await f.write(schema.dumps(ext_spec_dict.values(), indent=2, ensure_ascii=False))
