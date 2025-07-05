import dataclasses

from dataclasses_json import DataClassJsonMixin


@dataclasses.dataclass(frozen=True)
class DownloadOptions(DataClassJsonMixin):
    skip_if_exists: bool = False
    no_metadata: bool = False
    flatten_dir: bool = False
    keep_only_latest: bool = False
