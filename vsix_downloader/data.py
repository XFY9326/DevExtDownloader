import dataclasses
import datetime

from dataclasses_json import config, DataClassJsonMixin


@dataclasses.dataclass(frozen=True)
class VSCodeExtensionFile(DataClassJsonMixin):
    asset_type: str
    source: str


@dataclasses.dataclass(frozen=True)
class VSCodeExtensionProprety(DataClassJsonMixin):
    key: str
    value: str


@dataclasses.dataclass(frozen=True)
class VSCodeExtensionVersion(DataClassJsonMixin):
    version: str
    target_platform: str | None
    last_updated: datetime.datetime = dataclasses.field(metadata=config(
        encoder=lambda dt: dt.isoformat(),
        decoder=lambda s: datetime.datetime.fromisoformat(s)
    ))
    files: tuple[VSCodeExtensionFile, ...]
    propreties: tuple[VSCodeExtensionProprety, ...]

    def get_file_source(self, asset_type: str) -> str | None:
        return next((i.source for i in self.files if i.asset_type == asset_type), None)

    def get_proprety_value(self, key: str) -> str | None:
        return next((i.value for i in self.propreties if i.key == key), None)

    @property
    def package_url(self) -> str:
        package_url = self.get_file_source("Microsoft.VisualStudio.Services.VSIXPackage")
        assert package_url is not None, "No package url"
        return package_url

    @property
    def code_engine(self) -> str | None:
        return self.get_proprety_value("Microsoft.VisualStudio.Code.Engine")

    @property
    def prerelease(self) -> bool:
        return bool(self.get_proprety_value("Microsoft.VisualStudio.Code.PreRelease"))


@dataclasses.dataclass(frozen=True)
class VSCodeExtension(DataClassJsonMixin):
    extension_id: str
    extension_name: str
    display_name: str
    versions: tuple[VSCodeExtensionVersion, ...]
