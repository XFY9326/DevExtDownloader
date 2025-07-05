from pathlib import Path
from typing import Any

import aiofile
import aioshutil
from jinja2 import Template

from .utils import iter_meta_data, get_download_file_path
from ..common.tools import pretty_bytes

_TEMPLATE_INDEX_PATH: Path = Path(__file__).parent / "assets" / "index.html.j2"
_TEMPLATE_FAVICON_PATH: Path = Path(__file__).parent / "assets" / "favicon.ico"


async def load_plugin_render_params(
        download_dir: Path,
        is_flatten: bool = False,
) -> list[dict[str, Any]]:
    results: list = []
    async for plugin_meta_data in iter_meta_data(download_dir, is_flatten):
        versions: list[dict[str, Any]] = []
        for plugin_version in plugin_meta_data.versions:
            file_path = get_download_file_path(download_dir, is_flatten, plugin_meta_data, plugin_version)
            if file_path.is_file():
                versions.append(
                    {
                        "version": plugin_version.version,
                        "size": pretty_bytes(plugin_version.size) if plugin_version.size else None,
                        "updated_date": plugin_version.updated_date.strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ) if plugin_version.updated_date else None,
                        "since_build": plugin_version.since_build,
                        "until_build": plugin_version.until_build,
                        "file_url": str(file_path.relative_to(download_dir).as_posix()),
                    }
                )
            else:
                print(f"Warning: file {file_path} not found.")
        results.append(
            {
                "id": plugin_meta_data.id,
                "name": plugin_meta_data.name,
                "description": plugin_meta_data.description,
                "vendor": plugin_meta_data.vendor,
                "category": plugin_meta_data.category,
                "tags": plugin_meta_data.tags,
                "versions": versions,
            }
        )
    results.sort(key=lambda i: i["name"])
    return results


async def generate_index_html(download_dir: Path, is_flatten: bool = False) -> Path:
    if not download_dir.is_dir():
        raise NotADirectoryError(download_dir)
    async with aiofile.async_open(_TEMPLATE_INDEX_PATH, "r", encoding="utf-8") as f:
        template = Template(await f.read(), autoescape=True, enable_async=True)

    render_params = await load_plugin_render_params(download_dir, is_flatten)
    xml_content = await template.render_async(items=render_params)
    index_html_path = download_dir / "index.html"
    async with aiofile.async_open(index_html_path, "w", encoding="utf-8") as f:
        await f.write(xml_content)
    await aioshutil.copyfile(_TEMPLATE_FAVICON_PATH, index_html_path.with_name(_TEMPLATE_FAVICON_PATH.name))
    return index_html_path
