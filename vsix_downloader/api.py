import httpx

from . import iso8601
from .data import VSCodeExtension, VSCodeExtensionVersion, VSCodeExtensionFile, VSCodeExtensionProprety


class VSCodeExtensionAPI:
    _SERVER: str = "https://marketplace.visualstudio.com"
    # noinspection SpellCheckingInspection
    _EXTENSION_QUERY_URL: str = f"{_SERVER}/_apis/public/gallery/extensionquery"

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    @staticmethod
    def _build_query(ext_name: str, page_number: int = 1, page_size: int = 1) -> dict:
        return {
            "assetTypes": ["Microsoft.VisualStudio.Services.VSIXPackage"],
            "filters": [
                {
                    "criteria": [
                        {
                            "filterType": 7,
                            "value": ext_name
                        }
                    ],
                    "pageSize": page_size,
                    "pageNumber": page_number,
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

    async def get_extension(self, ext_name: str) -> VSCodeExtension | None:
        response = await self._client.post(
            self._EXTENSION_QUERY_URL,
            json=self._build_query(ext_name),
            headers=self._build_headers()
        )
        data = response.json()
        if len(data["results"]) > 0 and len(data["results"][0]["extensions"]) > 0:
            extension = data["results"][0]["extensions"][0]
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
                        propreties=tuple(
                            VSCodeExtensionProprety(
                                key=prop["key"],
                                value=prop["value"],
                            )
                            for prop in version["properties"]
                        ) if "properties" in version else tuple(),
                    )
                    for version in extension["versions"]
                ),
            )
        else:
            return None
