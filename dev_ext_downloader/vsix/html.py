from pathlib import Path
from typing import Any, AsyncGenerator

import aiofile
from jinja2 import Template

from dev_ext_downloader.common.tools import iter_meta_data_json
from .data import VSCodeExtension
from .utils import get_download_file_name

_TEMPLATE_INDEX_PATH: Path = Path(__file__).parent / "assets" / "index.html.j2"


async def _iter_meta_data(
        download_dir: Path, is_flatten: bool
) -> AsyncGenerator[VSCodeExtension, Any]:
    for meta_path in iter_meta_data_json(download_dir, is_flatten):
        async with aiofile.async_open(meta_path, "r", encoding="utf-8") as f:
            try:
                yield VSCodeExtension.from_json(await f.read())
            except Exception as e:
                print(f"Warning: meta file {meta_path} could not be read.", e)


async def _load_extensions_render_params(
        download_dir: Path, is_flatten: bool
) -> list[dict[str, Any]]:
    results: list = []
    async for ext_meta_data in _iter_meta_data(download_dir, is_flatten):
        versions: list[dict[str, Any]] = []
        for ext_version in ext_meta_data.versions:
            download_file_name = get_download_file_name(ext_meta_data, ext_version)
            if is_flatten:
                file_path = download_dir / download_file_name
            else:
                file_path = (
                        download_dir / ext_meta_data.unified_name / download_file_name
                )

            if file_path.is_file():
                versions.append(
                    {
                        "version": ext_version.version,
                        "prelease": ext_version.prerelease,
                        "target_platform": ext_version.target_platform or "universal",
                        "last_updated": ext_version.last_updated.strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                        "code_engine": ext_version.code_engine or "all",
                        "file_url": str(file_path.relative_to(download_dir).as_posix()),
                    }
                )
            else:
                print(f"Warning: file {file_path} not found.")
        results.append(
            {
                "extension_id": ext_meta_data.unified_name,
                "display_name": ext_meta_data.display_name,
                "publisher_name": ext_meta_data.publisher_display_name,
                "short_description": ext_meta_data.short_description,
                "categories": ext_meta_data.categories,
                "versions": versions,
            }
        )
    results.sort(key=lambda i: i["display_name"])
    return results


async def generate_index_html(download_dir: Path, is_flatten: bool = False) -> Path:
    if not download_dir.is_dir():
        raise NotADirectoryError(download_dir)
    async with aiofile.async_open(_TEMPLATE_INDEX_PATH, "r", encoding="utf-8") as f:
        template = Template(await f.read(), autoescape=True, enable_async=True)
    render_params = await _load_extensions_render_params(download_dir, is_flatten)
    html_content = await template.render_async(items=render_params)
    index_html_path = download_dir / "index.html"
    async with aiofile.async_open(index_html_path, "w", encoding="utf-8") as f:
        await f.write(html_content)
    return index_html_path
