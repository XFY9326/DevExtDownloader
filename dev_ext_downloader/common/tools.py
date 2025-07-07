import hashlib
import os
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any, Generator, Mapping
from urllib.parse import urljoin, urlparse, urlunparse, quote, urlencode

import aiofile
import aioshutil
import httpx
from tenacity import retry, stop_after_attempt, wait_incrementing, retry_if_exception_type


def get_file_name_from_header(headers: httpx.Headers) -> str | None:
    content_disposition = headers.get("Content-Disposition")
    if content_disposition:
        match = re.search(r'filename="(.+)"', content_disposition)
        if match:
            return match.group(1)
    return None


def get_file_name_from_response(response: httpx.Response) -> str | None:
    result = get_file_name_from_header(response.headers)
    if result is None:
        url_path = response.request.url.path
        if url_path.endswith("/"):
            return None
        else:
            result: str = os.path.basename(url_path)
    return result.strip()


@retry(
    stop=stop_after_attempt(5),
    wait=wait_incrementing(start=0, increment=2, max=30),
    retry=retry_if_exception_type(httpx.HTTPError),
    reraise=True
)
async def download_file(
        client: httpx.AsyncClient,
        url: str | httpx.URL,
        target_dir: Path,
        file_name: str | Callable[[str | None], str | None] | None = None,
        temp_dir: Path | None = None,
        skip_if_exists: bool = False,
) -> Path:
    temp_dir = target_dir if temp_dir is None else temp_dir
    temp_dir.mkdir(parents=True, exist_ok=True)
    target_dir.mkdir(parents=True, exist_ok=True)

    target_tmp_path = temp_dir / hashlib.sha1(str(url).encode("utf-8")).hexdigest()

    if file_name and isinstance(file_name, str):
        target_final_path = target_dir / file_name.strip()
        if skip_if_exists and target_final_path.is_file():
            return target_final_path

    async with client.stream("GET", url, follow_redirects=True) as response:
        response.raise_for_status()

        if file_name is None:
            file_name = get_file_name_from_response(response)
        elif isinstance(file_name, Callable):
            file_name = file_name(get_file_name_from_response(response))
        else:
            file_name = str(file_name).strip()

        if not file_name:
            raise ValueError(f"Unknown download file name: {url}")

        target_final_path = target_dir / file_name
        if skip_if_exists and target_final_path.is_file():
            return target_final_path

        async with aiofile.async_open(target_tmp_path, mode="wb") as f:
            async for chunk in response.aiter_bytes():
                await f.write(chunk)
            await f.flush(sync_metadata=True)

        await aioshutil.move(target_tmp_path, target_final_path)
        return target_final_path


def clean_dir(target_dir: Path, keep: set[Path]) -> None:
    for file_path in target_dir.rglob("*"):
        file_path: Path
        if file_path.is_file() and file_path not in keep:
            file_path.unlink()
    for dir_path in target_dir.rglob("*"):
        dir_path: Path
        if dir_path.is_dir() and not any(dir_path.iterdir()):
            dir_path.rmdir()


def iter_meta_data_json(
        download_dir: Path, is_flatten: bool
) -> Generator[Path, Any, None]:
    for p in download_dir.iterdir():
        if is_flatten:
            if p.is_file() and p.suffix == ".json":
                yield p
        else:
            if p.is_dir() and (p / f"{p.name}.json").is_file():
                yield p / f"{p.name}.json"


def pretty_bytes(num_bytes: int, precision: int = 2) -> str:
    if num_bytes < 0:
        raise ValueError("Num of bytes can't be negative: {}".format(num_bytes))

    units = ["B", "KB", "MB", "GB", "TB", "PB", "EB"]
    index = 0
    while num_bytes >= 1024 and index < len(units) - 1:
        num_bytes /= 1024.0
        index += 1
    return f"{num_bytes:.{precision}f} {units[index]}"


def get_file_name_last_extension(filename: str) -> str:
    return "".join(Path(filename).suffixes[-1])


def build_url(
        base: str,
        path: str = "",
        params: Mapping[str, Any] | None = None
) -> str:
    safe_path = quote(path, safe="/")

    url = urljoin(base, safe_path)

    if params:
        query = urlencode(params, doseq=True)
        parsed = urlparse(url)
        url = str(urlunparse(parsed._replace(query=query)))

    return url


# noinspection PyBroadException
def is_valid_http_url(url: str) -> bool:
    try:
        result = urlparse(url)
        return all([result.scheme in ("http", "https"), result.netloc])
    except:
        return False
