from django.conf import settings

from .data import load_json, dump_json

import requests
import logging


logger = logging.getLogger(__name__)


class InvalidPortalError(Exception):
    pass

class PortalConnectionError(Exception):
    pass


class Portal(object):

    @classmethod
    def iterate(cls, command, name_only = True):
        for name in settings.PORTAL.keys():
            yield name if name_only else cls(command, name)


    def __init__(self, command, name):
        self.command = command
        self.name = name

        if name not in settings.PORTAL:
            raise InvalidPortalError("Portal {} not found in options: {}".format(name, ", ".join(settings.PORTAL.keys())))

        self.base_url = settings.PORTAL[name]['host']
        self.headers = {
            'Authorization': "Token {}".format(settings.PORTAL[name]['token']),
            'Content-type': 'application/json'
        }


    def _get(self, path, params = None):
        return requests.get(
            "{}/{}/".format(self.base_url, path),
            headers = self.headers,
            params = params
        )

    def _post(self, path, data, files = None):
        return requests.post(
            "{}/{}/".format(self.base_url, path),
            headers = self.headers,
            data = dump_json(data),
            files = files
        )

    def _put(self, path, data, files = None):
        return requests.put(
            "{}/{}/".format(self.base_url, path),
            headers = self.headers,
            data = dump_json(data),
            files = files
        )

    def _patch(self, path, data, files = None):
        return requests.patch(
            "{}/{}/".format(self.base_url, path),
            headers = self.headers,
            data = dump_json(data),
            files = files
        )

    def _delete(self, path):
        return requests.delete(
            "{}/{}/".format(self.base_url, path),
            headers = self.headers
        )


    def _parse_response(self, response, warn = True):
        if response.status_code < 300:
            return load_json(response.content) if response.content else True
        else:
            try:
                error = dump_json(load_json(response.content), indent = 2)
            except Exception:
                error = response.content

            if warn:
                self.command.warning("Request to {} failed with {}: {}".format(response.url, response.status_code, error))
            return False


    def list(self, data_type, operation = None, warn = True, **filters):
        path = "{}/{}".format(data_type, operation) if operation else data_type
        return self._parse_response(self._get(path, filters), warn = warn)

    def retrieve(self, data_type, id, warn = True):
        return self._parse_response(self._get("{}/{}".format(data_type, id)), warn = warn)

    def create(self, data_type, **data):
        return self._parse_response(self._post(data_type, data))

    def update(self, data_type, id, **data):
        return self._parse_response(self._patch("{}/{}".format(data_type, id), data))

    def delete(self, data_type, id):
        return self._parse_response(self._delete("{}/{}".format(data_type, id)))