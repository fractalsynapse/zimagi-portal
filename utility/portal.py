from django.conf import settings

from .data import Collection, load_json, dump_json

import time
import requests
import logging


logger = logging.getLogger(__name__)


class InvalidPortalError(Exception):
    pass

class PortalConnectionError(Exception):
    pass


class Portal(object):

    @classmethod
    def iterate(cls, command):
        for name in settings.PORTAL.keys():
            yield cls(command, name)


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

        self._config = Collection(**settings.PORTAL[name])


    @property
    def config(self):
        return self._config


    def _request(self, method, path, *args, **kwargs):
        wait_sec = 1
        while True:
            response = getattr(requests, method)(path, *args, **kwargs)
            if response.status_code != 429:
                return response
            time.sleep(min((wait_sec * 2), 300))


    def _get(self, path, params = None):
        return self._request('get',
            "{}/{}/".format(self.base_url, path),
            headers = self.headers,
            params = params
        )

    def _post(self, path, data, files = None):
        return self._request('post',
            "{}/{}/".format(self.base_url, path),
            headers = self.headers,
            data = dump_json(data),
            files = files
        )

    def _put(self, path, data, files = None):
        return self._request('put',
            "{}/{}/".format(self.base_url, path),
            headers = self.headers,
            data = dump_json(data),
            files = files
        )

    def _patch(self, path, data, files = None):
        return self._request('patch',
            "{}/{}/".format(self.base_url, path),
            headers = self.headers,
            data = dump_json(data),
            files = files
        )

    def _delete(self, path):
        return self._request('delete',
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
