
# The follwing code is taken from
# https://github.com/msabramo/requests-unixsocket/blob/master/
# requests_unixsocket/adapters.py
from __future__ import (absolute_import, division, print_function)

import socket
try:
    import requests
    from requests.adapters import HTTPAdapter
    from requests.compat import urlparse, unquote, quote
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    from requests.packages import urllib3
    HAS_URLLIB3 = True
except ImportError:
    try:
        import urllib3
        HAS_URLLIB3 = True
    except ImportError:
        HAS_URLLIB3 = False

try:
    import http.client as httplib
except ImportError:
    import httplib

import json


__metaclass__ = type


DEFAULT_SCHEME = 'http+unix://'


# The following was adapted from some code from docker-py
# https://github.com/docker/docker-py/blob/master/docker/transport/unixconn.py
class UnixHTTPConnection(httplib.HTTPConnection, object):

    def __init__(self, unix_socket_url, timeout=60):
        """Create an HTTP connection to a unix domain socket
        :param unix_socket_url: A URL with a scheme of 'http+unix' and the
        netloc is a percent-encoded path to a unix domain socket. E.g.:
        'http+unix://%2Ftmp%2Fprofilesvc.sock/status/pid'
        """
        super(UnixHTTPConnection, self).__init__('localhost', timeout=timeout)
        self.unix_socket_url = unix_socket_url
        self.timeout = timeout
        self.sock = None

    def __del__(self):  # base class does not have d'tor
        if self.sock:
            self.sock.close()

    def connect(self):
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        socket_path = unquote(urlparse(self.unix_socket_url).netloc)
        sock.connect(socket_path)
        self.sock = sock


if HAS_URLLIB3:
    class UnixHTTPConnectionPool(urllib3.connectionpool.HTTPConnectionPool):

        def __init__(self, socket_path, timeout=60):
            super(UnixHTTPConnectionPool, self).__init__(
                'localhost', timeout=timeout)
            self.socket_path = socket_path
            self.timeout = timeout

        def _new_conn(self):
            return UnixHTTPConnection(self.socket_path, self.timeout)


if HAS_REQUESTS:
    class UnixAdapter(HTTPAdapter):

        def __init__(self, timeout=60, pool_connections=25, *args, **kwargs):
            super(UnixAdapter, self).__init__(*args, **kwargs)
            self.timeout = timeout
            self.pools = urllib3._collections.RecentlyUsedContainer(
                pool_connections, dispose_func=lambda p: p.close()
            )

        def get_connection(self, url, proxies=None):
            proxies = proxies or {}
            proxy = proxies.get(urlparse(url.lower()).scheme)

            if proxy:
                raise ValueError('%s does not support specifying proxies'
                                 % self.__class__.__name__)

            with self.pools.lock:
                pool = self.pools.get(url)
                if pool:
                    return pool

                pool = UnixHTTPConnectionPool(url, self.timeout)
                self.pools[url] = pool

            return pool

        def request_url(self, request, proxies):
            return request.path_url

        def close(self):
            self.pools.clear()


if HAS_REQUESTS:
    class APISession(requests.Session):
        def __init__(self, url_scheme=DEFAULT_SCHEME, *args, **kwargs):
            super(APISession, self).__init__(*args, **kwargs)
            self.mount(url_scheme, UnixAdapter())


class PodmanAPIHTTP:
    def __init__(self, base_url):
        self.api_url = "".join((DEFAULT_SCHEME,
                                quote(base_url, safe=""),
                                "/v2.0.0/libpod"))
        self.session = APISession()

    def request(self, method, url, **kwargs):
        return self.session.request(method=method, url=self.api_url + url, **kwargs)

    def get(self, url, **kwargs):
        kwargs.setdefault('allow_redirects', True)
        return self.request('get', url, **kwargs)

    def head(self, url, **kwargs):
        kwargs.setdefault('allow_redirects', False)
        return self.request('head', url, **kwargs)

    def post(self, url, data=None, json=None, **kwargs):
        return self.request('post', url, data=data, json=json, **kwargs)

    def patch(self, url, data=None, **kwargs):
        return self.request('patch', url, data=data, **kwargs)

    def put(self, url, data=None, **kwargs):
        return self.request('put', url, data=data, **kwargs)

    def delete(self, url, **kwargs):
        return self.request('delete', url, **kwargs)

    def options(self, url, **kwargs):
        kwargs.setdefault('allow_redirects', True)
        return self.request('options', url, **kwargs)


class PodmanAPIClient:
    def __init__(self, base_url):
        if not HAS_REQUESTS:
            raise Exception("requests package is required for podman API")
        socket_opt = urlparse(base_url)
        if socket_opt.scheme != "unix":
            raise Exception("Scheme %s is not supported! Use %s" % (
                socket_opt.scheme,
                DEFAULT_SCHEME
            ))
        self.api = PodmanAPIHTTP(socket_opt.path)
        self.containers = PodmanAPIContainers(self.api)
        self.images = PodmanAPIImages(api=self.api)

    def version(self):
        response = self.api.get(
            '/version')
        return response.json()


class PodmanAPIContainers:
    def __init__(self, api):
        self.api = api
        self.quote = quote

    def list(
            self, all_=None, filters=None, limit=None, size=None, sync=None):
        """List all images for a Podman service."""
        query = {}
        if all_ is not None:
            query["all"] = True
        if filters is not None:
            query["filters"] = filters
        if limit is not None:
            query["limit"] = limit
        if size is not None:
            query["size"] = size
        if sync is not None:
            query["sync"] = sync
        response = self.api.get("/containers/json", params=query)
        # observed to return None when no containers
        return response.json() or []

    def create(self, **container_data):
        response = self.api.post(
            "/containers/create",
            json=container_data,
        )
        if response.ok:
            return response.json()
        raise Exception("Container %s failed to create! Error: %s" %
                        (container_data.get('name'), response.text))

    def get(self, name):
        response = self.api.get(
            '/containers/{0}/json'.format(self.quote(name)))
        data = response.json()
        if data.get('response') == 404:
            data = {}
            # raise Exception("Container %s not found!" % name)
        return data

    def run(self, **container_data):
        _ = self.create(**container_data)  # pylint: disable=blacklisted-name
        name = container_data.get("name")
        _ = self.api.post(  # pylint: disable=blacklisted-name
            "/containers/{0}/start".format(self.quote(name)),
        )
        return self.get(name)

    def start(self, name):
        _ = self.api.post(  # pylint: disable=blacklisted-name
            "/containers/{0}/start".format(self.quote(name)),
        )
        return self.get(name)

    def stop(self, name):
        _ = self.api.post(  # pylint: disable=blacklisted-name
            "/containers/{0}/stop".format(self.quote(name)),
        )
        return self.get(name)

    def restart(self, name):
        _ = self.api.post(  # pylint: disable=blacklisted-name
            "/containers/{0}/restart".format(self.quote(name)),
        )
        return self.get(name)

    def remove(self, name, force=False):
        _ = self.api.delete(  # pylint: disable=blacklisted-name
            "/containers/{0}".format(self.quote(name)),
            params={"force": force}
        )
        return


class PodmanAPIImages:
    def __init__(self, api):
        self.api = api
        self.quote = quote
        self.inspect = self.get

    def exists(self, name):
        response = self.api.get(
            '/images/{0}/exists'.format(self.quote(name)))
        return response.status_code == 204

    def pull(self, reference):
        response = self.api.post(
            '/images/pull',
            params={'reference': reference}
        )
        if response.ok:
            correct_response = {'stream': '', 'text': response.text}
            for i in response.text.splitlines():
                if '"images"' in i:
                    correct_response['images'] = json.loads(i)['images']
                if '"id"' in i:
                    correct_response['id'] = json.loads(i)['id']
                elif '"stream"' in i:
                    correct_response['stream'] += json.loads(i)['stream']
                elif '"error"' in i:
                    correct_response['error'] = json.loads(i)['error']
            correct_response['code'] = response.status_code
            return correct_response
        return {"error": "HTTP %s Error: %s" % (response.json()['message'])}

    def get(self, name):
        response = self.api.get(
            '/images/{0}/json'.format(self.quote(name)))
        return response.json()
