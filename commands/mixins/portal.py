from django.conf import settings

from systems.commands.index import CommandMixin
from utility.portal import Portal, PortalConnectionError
from utility.temp import temp_dir

import base64
import string


class PortalCommandMixin(CommandMixin("portal")):

    def get_portals(self, **filters):
        portals = []
        for portal in Portal.iterate(self):
            add_portal = True
            for key, value in filters.items():
                if key in portal.config and portal.config[key] != value:
                    add_portal = False

            if add_portal:
                portals.append(portal)
        return portals

    def get_portal(self, name=None):
        if not name:
            name = settings.DEFAULT_PORTAL
        return Portal(self, name)

    def portal_list(self, portal_name, data_type, operation=None, **filters):
        return self._transmit(
            portal_name, data_type, "list", {"operation": operation, "filters": filters}
        )

    def portal_retrieve(self, portal_name, data_type, id):
        return self._transmit(portal_name, data_type, "retrieve", {"id": id})

    def portal_create(self, portal_name, data_type, **fields):
        return self._transmit(portal_name, data_type, "create", {"fields": fields})

    def portal_update(self, portal_name, data_type, id, **fields):
        return self._transmit(
            portal_name, data_type, "update", {"id": id, "fields": fields}
        )

    def portal_delete(self, portal_name, data_type, id):
        return self._transmit(portal_name, data_type, "delete", {"id": id})

    def _transmit(self, portal_name, data_type, operation, params):
        result = self.submit(
            "agent:portal:transmitter",
            {
                "portal": portal_name,
                "data_type": data_type,
                "operation": operation,
                "params": params,
            },
        )
        if result["status"] == "error":
            raise PortalConnectionError(result["error"])
        return result["response"]

    def parse_file_text(self, portal_name, data_type, file_id):
        printable = set(string.printable)
        text = ""

        with temp_dir() as temp:
            file = self.portal_retrieve(portal_name, data_type, file_id)
            file_type = file["file"].split(".")[-1].lower()
            file_path = temp.save(base64.b64decode(file["content"]), binary=True)
            try:
                parser = self.manager.get_provider("file_parser", file_type)
                file_text = parser.parse(file_path)
                if file_text:
                    text = "".join(filter(lambda x: x in printable, file_text))

            except ProviderError as e:
                pass
        return text

    def parse_file_content(self, portal_name, data_type, file_id):
        file = self.portal_retrieve(portal_name, data_type, file_id)
        return base64.b64decode(file["content"])
