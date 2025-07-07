from pathlib import Path

import semantic_version

from .data import VSCodeExtension, VSCodeExtensionVersion, VSCodeExtFilterOptions


def get_download_file_name(
        extension: VSCodeExtension, version: VSCodeExtensionVersion
) -> str:
    if version.target_platform:
        return (
            f"{extension.unified_name}-{version.version}@{version.target_platform}.vsix"
        )
    else:
        return f"{extension.unified_name}-{version.version}.vsix"


def get_download_file_dir(
        download_dir: Path,
        is_flatten: bool,
        extension: VSCodeExtension
) -> Path:
    if is_flatten:
        return download_dir
    else:
        return download_dir / extension.unified_name


def get_latest_extension_version(
        extension: VSCodeExtension, version_filter_options: VSCodeExtFilterOptions
) -> VSCodeExtensionVersion | None:
    for version in extension.versions:
        if not version_filter_options.include_prerelease and version.prerelease:
            continue
        if (
                version_filter_options.target_platform
                and version.target_platform
                and version.target_platform != version_filter_options.target_platform
        ):
            continue
        if version_filter_options.vscode_version and version.code_engine:
            target_vscode_version = semantic_version.Version(
                version_filter_options.vscode_version
            )
            if not semantic_version.NpmSpec(version.code_engine).match(
                    target_vscode_version
            ):
                continue
        return version
    return None
