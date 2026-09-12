from collections.abc import AsyncGenerator, Callable
from pathlib import Path
from typing import Any, TypeVar

import aiofile
import aioshutil
from jinja2 import Template

from .tools import iter_meta_data_json

T = TypeVar("T")


async def iter_json_metadata(
    download_dir: Path,
    is_flatten: bool,
    parser: Callable[[str], T],
    warning_prefix: str = "Metadata read warning",
) -> AsyncGenerator[T, None]:
    """Read and parse metadata files without coupling common code to a model."""
    for meta_path in iter_meta_data_json(download_dir, is_flatten):
        async with aiofile.async_open(meta_path, "r", encoding="utf-8") as f:
            try:
                yield parser(await f.read())
            except Exception as exc:
                print(
                    f"{warning_prefix}: meta file {meta_path} could not be read.",
                    exc,
                )


async def render_template_to_file(
    template_path: Path,
    favicon_path: Path,
    output_path: Path,
    **context: Any,
) -> Path:
    """Render an async Jinja template and copy its favicon beside the output."""
    async with aiofile.async_open(template_path, "r", encoding="utf-8") as f:
        template = Template(await f.read(), autoescape=True, enable_async=True)
    content = await template.render_async(**context)
    async with aiofile.async_open(output_path, "w", encoding="utf-8") as f:
        await f.write(content)
    await aioshutil.copyfile(favicon_path, output_path.with_name(favicon_path.name))
    return output_path
