from datetime import datetime
from pathlib import Path
from typing import Any

from dev_ext_downloader.common.render import iter_json_metadata, render_template_to_file

from . import TargetPlatformType
from .data import VSCodeExtension
from .utils import get_download_file_dir, get_download_file_name

_TEMPLATE_INDEX_PATH: Path = Path(__file__).parent / "assets" / "index.html.j2"
_TEMPLATE_FAVICON_PATH: Path = Path(__file__).parent / "assets" / "favicon.ico"


async def _load_extensions_render_params(
    download_dir: Path, is_flatten: bool
) -> list[dict[str, Any]]:
    results: list = []
    async for ext_meta_data in iter_json_metadata(
        download_dir, is_flatten, VSCodeExtension.from_json, "HTML generator warning"
    ):
        versions: list[dict[str, Any]] = []
        for ext_version in ext_meta_data.versions:
            download_file_name = get_download_file_name(ext_meta_data, ext_version)
            download_file_dir = get_download_file_dir(
                download_dir, is_flatten, ext_meta_data
            )
            file_path = download_file_dir / download_file_name
            if file_path.is_file():
                versions.append(
                    {
                        "version": ext_version.version,
                        "prerelease": ext_version.prerelease,
                        "target_platform": ext_version.target_platform
                        or TargetPlatformType.UNIVERSAL,
                        "last_updated": ext_version.last_updated.strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                        "code_engine": ext_version.code_engine or "all",
                        "file_url": str(file_path.relative_to(download_dir).as_posix()),
                    }
                )
            else:
                print(f"HTML generator warning: file {file_path} not found.")
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


async def generate_index_html(
    download_dir: Path,
    is_flatten: bool = False,
    generation_parameters: dict[str, str] | None = None,
) -> Path:
    if not download_dir.is_dir():
        raise NotADirectoryError(download_dir)

    render_params = await _load_extensions_render_params(download_dir, is_flatten)
    index_html_path = download_dir / "index.html"
    return await render_template_to_file(
        _TEMPLATE_INDEX_PATH,
        _TEMPLATE_FAVICON_PATH,
        index_html_path,
        items=render_params,
        page_info={
            "generated_at": datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z"),
            "download_dir": str(download_dir),
            "is_flatten": is_flatten,
            "extension_count": len(render_params),
            "version_count": sum(len(item["versions"]) for item in render_params),
            "parameters": generation_parameters
            or {
                "download_dir": str(download_dir),
                "is_flatten": str(is_flatten),
            },
        },
    )
