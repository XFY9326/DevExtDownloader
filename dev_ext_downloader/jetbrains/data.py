import dataclasses
import datetime

from dataclasses_json import DataClassJsonMixin, config

from dev_ext_downloader.common.models import DownloadOptions


@dataclasses.dataclass(frozen=True)
class JetbrainsPluginVersion(DataClassJsonMixin):
    version: str
    change_notes: str
    size: int | None
    updated_date: datetime.datetime | None = dataclasses.field(
        metadata=config(
            encoder=lambda dt: dt.isoformat() if dt else None,
            decoder=lambda s: datetime.datetime.fromisoformat(s) if s else None,
        )
    )
    since_build: str | None
    until_build: str | None
    download_url: str | None
    depends: tuple[str, ...]


@dataclasses.dataclass(frozen=True)
class JetbrainsPlugin(DataClassJsonMixin):
    id: str
    name: str
    description: str
    vendor: str
    category: str
    version: JetbrainsPluginVersion
    tags: tuple[str, ...]


@dataclasses.dataclass(frozen=True)
class JetbrainsDownloadVersion(DataClassJsonMixin):
    version: str
    change_notes: str
    size: int | None
    updated_date: datetime.datetime | None = dataclasses.field(
        metadata=config(
            encoder=lambda dt: dt.isoformat() if dt else None,
            decoder=lambda s: datetime.datetime.fromisoformat(s) if s else None,
        )
    )
    since_build: str | None
    until_build: str | None
    download_url: str | None
    download_file_name: str
    depends: tuple[str, ...]


@dataclasses.dataclass(frozen=True)
class JetbrainsDownloadPlugin(DataClassJsonMixin):
    id: str
    name: str
    description: str
    vendor: str
    category: str
    tags: tuple[str, ...]
    versions: tuple[JetbrainsDownloadVersion, ...]


@dataclasses.dataclass(frozen=True)
class JetbrainsDef(DataClassJsonMixin):
    plugin_id: str
    target_build_version: str | None
    download_options: DownloadOptions | None = None
