from pathlib import Path

import semantic_version

from .data import (
    TargetPlatformType,
    VSCodeExtension,
    VSCodeExtensionVersion,
    VSCodeExtFilterOptions,
)
from dev_ext_downloader.common.tools import get_download_dir


def get_download_file_name(
    extension: VSCodeExtension, version: VSCodeExtensionVersion
) -> str:
    version_platform = (
        version.target_platform
        if version.target_platform
        else TargetPlatformType.UNIVERSAL
    )
    return f"{extension.unified_name}-{version.version}@{version_platform}.vsix"


def get_download_file_dir(
    download_dir: Path, is_flatten: bool, extension: VSCodeExtension
) -> Path:
    return get_download_dir(download_dir, is_flatten, extension.unified_name)


def get_latest_extension_versions(
    extension: VSCodeExtension, version_filter_options: VSCodeExtFilterOptions
) -> list[VSCodeExtensionVersion]:
    result: dict[TargetPlatformType, VSCodeExtensionVersion] = {}
    fallback_version: VSCodeExtensionVersion | None = None
    target_vscode_version = (
        semantic_version.Version(version_filter_options.vscode_version)
        if version_filter_options.vscode_version
        else None
    )
    parsed_versions: dict[str, semantic_version.Version] = {}
    parsed_engines: dict[str, semantic_version.NpmSpec] = {}

    def parse_version(value: str) -> semantic_version.Version:
        parsed = parsed_versions.get(value)
        if parsed is None:
            parsed = semantic_version.Version(value)
            parsed_versions[value] = parsed
        return parsed

    for version in extension.versions:
        version_platform: TargetPlatformType = (
            version.target_platform
            if version.target_platform
            else TargetPlatformType.UNIVERSAL
        )
        if not version_filter_options.include_prerelease and version.prerelease:
            continue
        requested_platforms = version_filter_options.target_platform
        is_requested = (
            not requested_platforms or version_platform in requested_platforms
        )
        is_fallback = (
            version_filter_options.target_platform_fallback is not None
            and version_platform == version_filter_options.target_platform_fallback
        )
        if not is_requested and not is_fallback:
            continue
        if target_vscode_version is not None and version.code_engine:
            engine = parsed_engines.get(version.code_engine)
            if engine is None:
                engine = semantic_version.NpmSpec(version.code_engine)
                parsed_engines[version.code_engine] = engine
            if not engine.match(target_vscode_version):
                continue

        new_version = parse_version(version.version)
        if is_fallback and not is_requested:
            if fallback_version is None or version.sort_key > fallback_version.sort_key:
                fallback_version = version
            continue

        if version_platform in result:
            old_version = parse_version(result[version_platform].version)
            if new_version > old_version:
                result[version_platform] = version
        else:
            result[version_platform] = version

    if len(result) > 0:
        return list(result.values())
    elif fallback_version is not None:
        return [fallback_version]
    else:
        return []
