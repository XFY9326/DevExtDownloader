from pathlib import Path
from typing import Any

import aiofile
from jinja2 import Template

from .utils import iter_meta_data, get_download_file_path

_TEMPLATE_XML_PATH: Path = Path(__file__).parent / "assets" / "updatePlugins.xml.j2"


async def _load_plugin_render_params(
        base_url: str,
        download_dir: Path,
        is_flatten: bool = False,
) -> list[dict[str, Any]]:
    results: list = []
    async for plugin_meta_data in iter_meta_data(download_dir, is_flatten):
        latest_version: dict[str, Any] | None = None
        for plugin_version in plugin_meta_data.versions:
            file_path = get_download_file_path(download_dir, is_flatten, plugin_meta_data, plugin_version)
            if file_path.is_file():
                file_url = (
                        base_url.rstrip("/")
                        + "/"
                        + str(file_path.relative_to(download_dir).as_posix()).lstrip("/")
                )
                latest_version = {
                    "version": plugin_version.version,
                    "notes": plugin_version.change_notes,
                    "since": plugin_version.since_build,
                    "until": plugin_version.until_build,
                    "depends": plugin_version.depends,
                    "url": file_url,
                }
                break
            else:
                print(f"Warning: file {file_path} not found.")
        if latest_version is None:
            print(f"Warning: plugin {plugin_meta_data.id} has no available version.")
        else:
            results.append(
                {
                    "id": plugin_meta_data.id,
                    "name": plugin_meta_data.name,
                    "description": plugin_meta_data.description,
                    "version": latest_version,
                }
            )
        results.sort(key=lambda i: i["name"])

    return results


async def generate_update_plugins_xml(
        base_url: str, download_dir: Path, is_flatten: bool = False
) -> Path:
    if not download_dir.is_dir():
        raise NotADirectoryError(download_dir)
    async with aiofile.async_open(_TEMPLATE_XML_PATH, "r", encoding="utf-8") as f:
        template = Template(await f.read(), autoescape=True, enable_async=True)

    render_params = await _load_plugin_render_params(base_url, download_dir, is_flatten)
    xml_content = await template.render_async(plugins=render_params)
    update_plugins_path = download_dir / "updatePlugins.xml"
    async with aiofile.async_open(update_plugins_path, "w", encoding="utf-8") as f:
        await f.write(xml_content)
    return update_plugins_path
