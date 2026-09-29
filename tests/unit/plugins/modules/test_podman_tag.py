from __future__ import absolute_import, division, print_function

__metaclass__ = type

from unittest.mock import Mock

import pytest

from ansible_collections.containers.podman.plugins.modules.podman_tag import create_full_qualified_image_name, tag


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


def test_tag_fails_when_source_image_not_resolvable():
    """A dangling/missing source image must fail instead of silently no-op'ing."""
    module = Mock()
    module.params = {
        "image": "quay.io/example/missing:latest",
        "target_names": ["localhost/missing"],
    }
    module.check_mode = False
    # `podman image ls -q <missing image>` exits 0 with empty stdout.
    module.run_command.return_value = (0, "", "")

    tag(module, "podman")

    assert module.fail_json.called
    assert "image not known" in module.fail_json.call_args.kwargs["msg"]
    module.run_command.assert_called_once()
