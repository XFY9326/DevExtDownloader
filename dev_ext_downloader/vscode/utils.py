from pathlib import Path

import semantic_version

from .data import (
    TargetPlatformType,
    VSCodeExtension,
    VSCodeExtensionVersion,
    VSCodeExtFilterOptions,
)


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
    if is_flatten:
        return download_dir
    else:
        return download_dir / extension.unified_name


def get_latest_extension_versions(
    extension: VSCodeExtension, version_filter_options: VSCodeExtFilterOptions
) -> list[VSCodeExtensionVersion]:
    result: dict[TargetPlatformType, VSCodeExtensionVersion] = {}
    fallback_version: VSCodeExtensionVersion | None = None
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
        if version_filter_options.vscode_version and version.code_engine:
            target_vscode_version = semantic_version.Version(
                version_filter_options.vscode_version
            )
            if not semantic_version.NpmSpec(version.code_engine).match(
                target_vscode_version
            ):
                continue

        new_version = semantic_version.Version(version.version)
        if is_fallback and not is_requested:
            if fallback_version is None or version.sort_key > fallback_version.sort_key:
                fallback_version = version
            continue

        if version_platform in result:
            old_version = semantic_version.Version(result[version_platform].version)
            new_version = semantic_version.Version(version.version)
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
