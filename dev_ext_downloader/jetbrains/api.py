import datetime
import urllib.parse as urlparser

import httpx
from lxml import etree

from .data import JetbrainsPlugin, JetbrainsPluginVersion


class JetbrainsPluginAPI:
    _SERVER: str = "https://plugins.jetbrains.com"
    _PLUGIN_LIST_URL: str = f"{_SERVER}/plugins/list"
    _PLUGIN_DOWNLOAD_URL: str = f"{_SERVER}/plugin/download"

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    def _get_plugin_download_url(self, plugin_id: str, plugin_version: str) -> str:
        download_params = {"pluginId": plugin_id, "version": plugin_version}
        return f"{self._PLUGIN_DOWNLOAD_URL}?{urlparser.urlencode(download_params)}"

    def _parse_plugins_xml(self, plugins_xml: etree._Element) -> list[JetbrainsPlugin]:
        plugins: list[JetbrainsPlugin] = []
        for category in plugins_xml.findall("category"):
            category_name = category.get("name", "")
            for plugin_el in category.findall("idea-plugin"):
                plugin_id = plugin_el.findtext("id")
                plugin_version = plugin_el.findtext("version")

                if plugin_id is None or plugin_version is None:
                    continue

                plugin_size = plugin_el.get("size")
                plugin_update_date = plugin_el.get("updatedDate")
                idea_version_el = plugin_el.find("idea-version")

                plugin = JetbrainsPlugin(
                    id=plugin_id,
                    name=(plugin_el.findtext("name") or "").strip(),
                    description=(plugin_el.findtext("description") or "").strip(),
                    vendor=(plugin_el.findtext("vendor") or "").strip(),
                    category=category_name,
                    version=JetbrainsPluginVersion(
                        version=plugin_version,
                        change_notes=(plugin_el.findtext("change-notes") or "").strip(),
                        size=int(plugin_size) if plugin_size else None,
                        updated_date=datetime.datetime.fromtimestamp(
                            int(plugin_update_date) / 1000.0
                        ) if plugin_update_date else None,
                        since_build=idea_version_el.get("since-build") if idea_version_el is not None else None,
                        until_build=idea_version_el.get("until-build") if idea_version_el is not None else None,
                        download_url=self._get_plugin_download_url(
                            plugin_id, plugin_version
                        ),
                        depends=tuple(
                            d.text.strip()
                            for d in plugin_el.findall("depends")
                            if d.text
                        ),
                    ),
                    tags=tuple(t.text.strip() for t in plugin_el.findall("tags") if t.text),
                )
                plugins.append(plugin)

        return plugins

    async def list_plugins(
            self, plugin_id: str, build: str | None = None
    ) -> list[JetbrainsPlugin]:
        params = {"pluginId": plugin_id}
        if build:
            params["build"] = build
        response = await self._client.get(url=self._PLUGIN_LIST_URL, params=params)
        response.raise_for_status()

        root = etree.fromstring(response.content)
        return self._parse_plugins_xml(root)
