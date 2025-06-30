from typing import Collection

import httpx

from . import iso8601
from .data import VSCodeExtension, VSCodeExtensionVersion, VSCodeExtensionFile, VSCodeExtensionProperty


class VSCodeExtensionAPI:
    _SERVER: str = "https://marketplace.visualstudio.com"
    # noinspection SpellCheckingInspection
    _EXTENSION_QUERY_URL: str = f"{_SERVER}/_apis/public/gallery/extensionquery"

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    @staticmethod
    def _build_query(ext_name: Collection[str]) -> dict:
        return {
            "assetTypes": ["Microsoft.VisualStudio.Services.VSIXPackage"],
            "filters": [
                {
                    "criteria": [
                        {
                            "filterType": 7,
                            "value": name
                        } for name in ext_name
                    ],
                    "pageSize": len(ext_name),
                    "pageNumber": 1,
                    "sortBy": 0,
                    "sortOrder": 0
                }
            ],
            "flags": 439
        }

    @staticmethod
    def _build_headers(api_version: str = "3.0-preview.1") -> dict:
        headers = {
            "Accept": f"application/json;api-version={api_version}",
            "Content-Type": "application/json"
        }
        return headers

    @staticmethod
    def _parse_extension_json(extension: dict) -> VSCodeExtension:
        return VSCodeExtension(
            extension_id=extension["extensionId"],
            extension_name=extension["extensionName"],
            display_name=extension["displayName"],
            versions=tuple(
                VSCodeExtensionVersion(
                    version=version["version"],
                    target_platform=version["targetPlatform"] if "targetPlatform" in version else None,
                    last_updated=iso8601.parse_iso8601(version["lastUpdated"]),
                    files=tuple(
                        VSCodeExtensionFile(
                            asset_type=file["assetType"],
                            source=file["source"],
                        )
                        for file in version["files"]
                    ),
                    properties=tuple(
                        VSCodeExtensionProperty(
                            key=prop["key"],
                            value=prop["value"],
                        )
                        for prop in version["properties"]
                    ) if "properties" in version else tuple(),
                )
                for version in extension["versions"]
            ),
        )

    async def get_extensions(self, ext_names: Collection[str]) -> dict[str, VSCodeExtension]:
        ext_names = set(ext_names)
        response = await self._client.post(
            self._EXTENSION_QUERY_URL,
            json=self._build_query(ext_names),
            headers=self._build_headers()
        )
        response.raise_for_status()
        data = response.json()

        result = {}
        if len(data["results"]) > 0:
            for extension in data["results"][0]["extensions"]:
                ext_name = f"{extension['publisher']['publisherName']}.{extension['extensionName']}"
                if ext_name in ext_names:
                    result[ext_name] = self._parse_extension_json(extension)
        return result
