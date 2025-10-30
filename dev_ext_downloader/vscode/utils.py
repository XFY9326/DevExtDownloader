from pathlib import Path

import semantic_version

from .data import VSCodeExtension, VSCodeExtensionVersion, VSCodeExtFilterOptions, TargetPlatformType


def get_download_file_name(
        extension: VSCodeExtension, version: VSCodeExtensionVersion
) -> str:
    version_platform = version.target_platform if version.target_platform else TargetPlatformType.UNIVERSAL
    return f"{extension.unified_name}-{version.version}@{version_platform}.vsix"


def get_download_file_dir(
        download_dir: Path,
        is_flatten: bool,
        extension: VSCodeExtension
) -> Path:
    if is_flatten:
        return download_dir
    else:
        return download_dir / extension.unified_name


def get_latest_extension_versions(
        extension: VSCodeExtension, version_filter_options: VSCodeExtFilterOptions
) -> list[VSCodeExtensionVersion]:
    result: dict[str, VSCodeExtensionVersion] = {}
    fallback_version: VSCodeExtensionVersion | None = None
    for version in extension.versions:
        version_platform: TargetPlatformType = version.target_platform if version.target_platform else TargetPlatformType.UNIVERSAL
        if not version_filter_options.include_prerelease and version.prerelease:
            continue
        if (
                version_filter_options.target_platform
                and len(version_filter_options.target_platform) > 0
                and version.target_platform
        ):
            if version_platform not in version_filter_options.target_platform:
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
        if version_platform in result:
            old_version = semantic_version.Version(result[version_platform].version)
            new_version = semantic_version.Version(version.version)
            if new_version > old_version:
                result[version_platform] = version
        else:
            result[version_platform] = version

        if version_filter_options.target_platform_fallback == version_platform:
            if fallback_version is None:
                fallback_version = version
            else:
                old_version = semantic_version.Version(fallback_version.version)
                if new_version > old_version:
                    fallback_version = version

    if len(result) > 0:
        return list(result.values())
    elif fallback_version is not None:
        return [fallback_version]
    else:
        return []
