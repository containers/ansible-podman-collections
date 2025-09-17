from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible_collections.containers.podman.plugins.modules.podman_tag import create_full_qualified_image_name


@pytest.mark.parametrize(
    "test_input, expected",
    [
        ("alpine", "localhost/alpine:latest"),
        ("alpine:3.19", "localhost/alpine:3.19"),
        ("docker.io/library/alpine", "docker.io/library/alpine:latest"),
        ("docker.io/alpine", "docker.io/library/alpine:latest"),
        ("docker.io/alpine@sha256:1234567890abcdef", "docker.io/library/alpine@sha256:1234567890abcdef"),
    ],
)
def test_create_full_qualified_image_name(test_input, expected):
    print(create_full_qualified_image_name.__code__.co_filename)
    assert create_full_qualified_image_name(test_input) == expected
