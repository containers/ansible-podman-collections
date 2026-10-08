from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json
from unittest.mock import Mock, patch

import pytest

from ansible_collections.containers.podman.plugins.modules import podman_secret


class ModuleFailure(Exception):
    pass


def secret_module(stored):
    def fail_json(**kwargs):
        raise ModuleFailure(kwargs["msg"])

    module = Mock()
    module.from_json.side_effect = json.loads
    module.fail_json.side_effect = fail_json
    module.run_command.side_effect = [
        (0, json.dumps([{"SecretData": stored.decode("utf-8", errors="replace"), "Spec": {}}]), ""),
        (0, stored.hex() + "\n", ""),
    ]
    return module


def file_needs_update(module, path, **kwargs):
    return podman_secret.need_update(
        module, "/custom/podman", "binary-secret", None, str(path), None,
        kwargs.get("skip", False), None, None, kwargs.get("debug", False), None,
    )


@pytest.mark.parametrize("payload", [b"\xff\xfe\x00\n\n", b"\xc3\x28", b"", b"text\n", "caf\u00e9".encode("utf-8")])
def test_unchanged_file_secret(tmp_path, payload):
    path = tmp_path / "secret"
    path.write_bytes(payload)
    module = secret_module(payload)

    assert file_needs_update(module, path) is False
    assert module.run_command.call_args.args[0] == [
        "/custom/podman", "secret", "inspect", "--showsecret", "--format",
        '{{ printf "%x" .SecretData }}', "binary-secret",
    ]


@pytest.mark.parametrize("stored, desired", [(b"\xff", b"\xfe"), (b"text\n", b"text\n\n"), (b"", b"\x00")])
@pytest.mark.parametrize("debug", [False, True])
def test_changed_file_secret(tmp_path, stored, desired, debug):
    path = tmp_path / "secret"
    path.write_bytes(desired)
    module = secret_module(stored)

    assert file_needs_update(module, path, debug=debug) is True
    if not debug or stored == b"\xff":
        assert podman_secret.diff == {"before": "<secret>", "after": "<different-secret>"}


def test_skip_existing_does_not_read_file(tmp_path):
    module = secret_module(b"\xff")

    assert file_needs_update(module, tmp_path / "missing", skip=True) is False
    module.run_command.assert_called_once()


def test_missing_file_fails_before_secret_removal(tmp_path):
    module = secret_module(b"\xff")

    with patch.object(podman_secret, "get_podman_version", return_value="5.8.7"):
        with pytest.raises(ModuleFailure, match="Unable to read secret file"):
            podman_secret.podman_secret_create(
                module, "/custom/podman", "binary-secret", None, str(tmp_path / "missing"),
                None, False, False, None, None, False, None,
            )
    module.run_command.assert_called_once()


@pytest.mark.parametrize("result", [(125, "", "inspect failed"), (0, "invalid hex\n", "")])
def test_failed_binary_inspection_is_reported(tmp_path, result):
    path = tmp_path / "secret"
    path.write_bytes(b"\xff")
    module = secret_module(b"\xff")
    module.run_command.side_effect = [next(module.run_command.side_effect), result]

    with pytest.raises(ModuleFailure, match="Unable to inspect secret data"):
        file_needs_update(module, path)


@pytest.mark.parametrize("labels, expected", [({"purpose": "old"}, False), ({"purpose": "new"}, True)])
def test_binary_file_still_compares_labels(tmp_path, labels, expected):
    path = tmp_path / "secret"
    path.write_bytes(b"\xff")
    module = secret_module(b"\xff")
    module.run_command.side_effect = [
        (0, json.dumps([{"Spec": {"Labels": {"purpose": "old"}}}]), ""),
        (0, "ff\n", ""),
    ]

    assert podman_secret.need_update(
        module, "/custom/podman", "binary-secret", None, str(path), None,
        False, None, None, False, labels,
    ) is expected
