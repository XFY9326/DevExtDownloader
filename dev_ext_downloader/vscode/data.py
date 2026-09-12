import dataclasses
import datetime
import enum
import functools

import semantic_version
from dataclasses_json import DataClassJsonMixin, config

from dev_ext_downloader.common.models import DownloadOptions


class TargetPlatformType(enum.StrEnum):
    UNIVERSAL = "universal"
    WIN32_IA32 = "win32-ia32"
    WIN32_X64 = "win32-x64"
    WIN32_ARM64 = "win32-arm64"
    LINUX_X64 = "linux-x64"
    LINUX_ARM64 = "linux-arm64"
    LINUX_ARMHF = "linux-armhf"
    ALPINE_X64 = "alpine-x64"
    ALPINE_ARM64 = "alpine-arm64"
    DARWIN_X64 = "darwin-x64"
    DARWIN_ARM64 = "darwin-arm64"
    WEB = "web"


@dataclasses.dataclass(frozen=True)
class VSCodeExtensionFile(DataClassJsonMixin):
    asset_type: str
    source: str


@dataclasses.dataclass(frozen=True)
class VSCodeExtensionProperty(DataClassJsonMixin):
    key: str
    value: str


@dataclasses.dataclass(frozen=True)
class VSCodeExtensionVersion(DataClassJsonMixin):
    version: str
    target_platform: TargetPlatformType | None = dataclasses.field(
        metadata=config(
            encoder=lambda s: str(s) if s else TargetPlatformType.UNIVERSAL,
            decoder=lambda s: TargetPlatformType(s)
            if s
            else TargetPlatformType.UNIVERSAL,
        )
    )
    last_updated: datetime.datetime = dataclasses.field(
        metadata=config(
            encoder=lambda dt: dt.isoformat(),
            decoder=lambda s: datetime.datetime.fromisoformat(s),
        )
    )
    files: tuple[VSCodeExtensionFile, ...]
    properties: tuple[VSCodeExtensionProperty, ...]

    @functools.cached_property
    def _file_sources(self) -> dict[str, str]:
        return {item.asset_type: item.source for item in self.files}

    @functools.cached_property
    def _property_values(self) -> dict[str, str]:
        return {item.key: item.value for item in self.properties}

    @functools.cached_property
    def _semantic_version(self) -> semantic_version.Version:
        return semantic_version.Version(self.version)

    def get_file_source(self, asset_type: str) -> str | None:
        return self._file_sources.get(asset_type)

    def get_property_value(self, key: str) -> str | None:
        return self._property_values.get(key)

    @property
    def package_url(self) -> str:
        package_url = self.get_file_source(
            "Microsoft.VisualStudio.Services.VSIXPackage"
        )
        assert package_url is not None, "No package url"
        return package_url

    @property
    def code_engine(self) -> str | None:
        return self.get_property_value("Microsoft.VisualStudio.Code.Engine")

    @property
    def prerelease(self) -> bool:
        value = self.get_property_value("Microsoft.VisualStudio.Code.PreRelease")
        return value is not None and value.strip().lower() == "true"

    @property
    def sort_key(self) -> tuple:
        """Return a deterministic key without mutating semantic-version internals."""
        version = self._semantic_version
        return (
            version.precedence_key,
            not self.prerelease,
            self.last_updated.timestamp(),
            str(self.target_platform or TargetPlatformType.UNIVERSAL),
        )


@dataclasses.dataclass(frozen=True)
class VSCodeExtension(DataClassJsonMixin):
    extension_id: str
    extension_name: str
    display_name: str
    publisher_id: str
    publisher_name: str
    publisher_display_name: str
    short_description: str
    categories: tuple[str, ...]
    versions: tuple[VSCodeExtensionVersion, ...]

    @property
    def unified_name(self) -> str:
        return f"{self.publisher_name}.{self.extension_name}"


@dataclasses.dataclass(frozen=True)
class VSCodeExtFilterOptions(DataClassJsonMixin):
    target_platform: tuple[TargetPlatformType, ...] | None = None
    target_platform_fallback: TargetPlatformType | None = None
    vscode_version: str | None = None
    include_prerelease: bool = False


@dataclasses.dataclass(frozen=True)
class VSCodeExt(DataClassJsonMixin):
    ext_id: str
    download_options: DownloadOptions | None = None
    filter_options: VSCodeExtFilterOptions | None = None
