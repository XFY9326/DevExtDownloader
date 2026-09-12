from datetime import datetime
from pathlib import Path
from typing import Any

from dev_ext_downloader.common.render import render_template_to_file
from dev_ext_downloader.common.tools import build_url, is_valid_http_url, pretty_bytes

from .utils import get_download_file_path, iter_meta_data

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
            file_path = get_download_file_path(
                download_dir, is_flatten, plugin_meta_data, plugin_version
            )
            if file_path.is_file():
                versions.append(
                    {
                        "version": plugin_version.version,
                        "size": pretty_bytes(plugin_version.size)
                        if plugin_version.size
                        else None,
                        "updated_date": plugin_version.updated_date.strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )
                        if plugin_version.updated_date
                        else None,
                        "since_build": plugin_version.since_build,
                        "until_build": plugin_version.until_build,
                        "file_url": str(file_path.relative_to(download_dir).as_posix()),
                    }
                )
            else:
                print(f"HTML generator warning: file {file_path} not found.")
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


async def generate_index_html(
    base_url: str | None,
    download_dir: Path,
    is_flatten: bool = False,
    generation_parameters: dict[str, str] | None = None,
) -> Path:
    if base_url is not None and not is_valid_http_url(base_url):
        raise ValueError(f"Invalid http base url: {base_url}")
    if not download_dir.is_dir():
        raise NotADirectoryError(download_dir)

    render_params = await load_plugin_render_params(download_dir, is_flatten)
    update_url = (
        build_url(
            base=base_url if base_url.endswith("/") else f"{base_url}/",
            path="updatePlugins.xml",
        )
        if base_url is not None
        else None
    )
    index_html_path = download_dir / "index.html"
    return await render_template_to_file(
        _TEMPLATE_INDEX_PATH,
        _TEMPLATE_FAVICON_PATH,
        index_html_path,
        items=render_params,
        update_plugins_xml_url=update_url,
        page_info={
            "generated_at": datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z"),
            "download_dir": str(download_dir),
            "is_flatten": is_flatten,
            "base_url": base_url,
            "plugin_count": len(render_params),
            "version_count": sum(len(item["versions"]) for item in render_params),
            "parameters": generation_parameters
            or {
                "base_url": str(base_url),
                "download_dir": str(download_dir),
                "is_flatten": str(is_flatten),
            },
        },
    )
