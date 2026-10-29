from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible_collections.containers.podman.plugins.module_utils.podman.podman_container_lib import (
    ARGUMENTS_SPEC_CONTAINER,
)
from ansible_collections.containers.podman.plugins.module_utils.podman.quadlet import (
    ContainerQuadlet,
)


def container_params(**overrides):
    params = {key: spec.get("default") for key, spec in ARGUMENTS_SPEC_CONTAINER.items()}
    params.update({"name": "testcont", "image": "testimage", "state": "quadlet"})
    params.update(overrides)
    return params


@pytest.mark.parametrize(
    "option, flag",
    [
        ("http_proxy", "--http-proxy"),
        ("sig_proxy", "--sig-proxy"),
        ("tls_verify", "--tls-verify"),
    ],
)
@pytest.mark.parametrize("value", [True, False])
def test_container_quadlet_bool_podman_args(option, flag, value):
    quadlet = ContainerQuadlet(container_params(**{option: value}))
    content = quadlet.create_quadlet_content()
    assert "PodmanArgs=%s=%s\n" % (flag, str(value).lower()) in content


@pytest.mark.parametrize("option, flag", [("http_proxy", "--http-proxy"), ("sig_proxy", "--sig-proxy")])
def test_container_quadlet_bool_podman_args_unset(option, flag):
    quadlet = ContainerQuadlet(container_params())
    assert flag not in quadlet.create_quadlet_content()
