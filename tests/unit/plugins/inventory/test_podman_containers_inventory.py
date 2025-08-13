from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json
from unittest.mock import patch

import pytest

from ansible.errors import AnsibleParserError


class FakeInventory:
    def __init__(self):
        self.hostvars = {}
        self.groups = {}

    def add_group(self, name):
        self.groups.setdefault(name, {"hosts": [], "children": []})

    def add_child(self, parent, child):
        self.add_group(parent)
        self.add_group(child)
        if child not in self.groups[parent]["children"]:
            self.groups[parent]["children"].append(child)

    def add_host(self, host, group=None):
        self.hostvars.setdefault(host, {})
        if group:
            self.add_group(group)
            if host not in self.groups[group]["hosts"]:
                self.groups[group]["hosts"].append(host)
        else:
            self.add_group("ungrouped")
            if host not in self.groups["ungrouped"]["hosts"]:
                self.groups["ungrouped"]["hosts"].append(host)

    def set_variable(self, host, var, value):
        self.hostvars.setdefault(host, {})
        self.hostvars[host][var] = value


def build_ps_json(entries):
    return json.dumps(entries).encode("utf-8")


@patch("ansible_collections.containers.podman.plugins.inventory.podman_containers.shutil.which", return_value="podman")
def test_basic_discovery_and_hostvars(mock_which):
    from ansible_collections.containers.podman.plugins.inventory.podman_containers import (
        InventoryModule,
    )

    containers = [
        {
            "Names": ["app-1"],
            "Id": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "Image": "docker.io/library/alpine:latest",
            "Status": "Up 1 second",
            "Labels": {"env": "dev", "role": "api"},
        },
        {
            "Names": ["db/primary"],
            "ID": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            "ImageName": "quay.io/ns/repo-name:1.0",
            "State": "Exited (0) 2 seconds ago",
            "Labels": {},
        },
    ]

    with patch(
        "ansible_collections.containers.podman.plugins.inventory.podman_containers.subprocess.check_output",
        return_value=build_ps_json(containers),
    ):
        inv = FakeInventory()
        mod = InventoryModule()
        # Feed config directly
        with patch.object(
            mod,
            "_read_config_data",
            return_value={
                "executable": "podman",
                "include_stopped": True,
                "connection_plugin": "containers.podman.podman",
                "group_by_image": True,
                "group_by_label": ["env"],
                "verbose_output": True,
            },
        ):
            mod.parse(inv, loader=None, path="dummy.yml", cache=False)

    # Hosts discovered
    assert "app-1" in inv.hostvars
    assert "db/primary" in inv.hostvars
    # Hostvars set - image, id, status keys
    assert inv.hostvars["app-1"]["podman_image"] == "docker.io/library/alpine:latest"
    assert inv.hostvars["db/primary"]["podman_image"] == "quay.io/ns/repo-name:1.0"
    assert inv.hostvars["app-1"]["podman_container_id"].startswith("a")
    assert inv.hostvars["db/primary"]["podman_container_id"].startswith("b")
    assert inv.hostvars["app-1"]["podman_status"].lower().startswith("up")
    assert inv.hostvars["db/primary"]["podman_status"].lower().startswith("exited")
    # Verbose output included
    assert "podman_ps" in inv.hostvars["app-1"]
    # Image grouping sanitized
    assert "image_docker.io_library_alpine_latest" in inv.groups
    assert "image_quay.io_ns_repo_name_1.0" in inv.groups
    # Label grouping
    assert "label_env_dev" in inv.groups
    assert "app-1" in inv.groups["label_env_dev"]["hosts"]


@patch("ansible_collections.containers.podman.plugins.inventory.podman_containers.shutil.which", return_value="podman")
def test_name_patterns_and_label_selectors(mock_which):
    from ansible_collections.containers.podman.plugins.inventory.podman_containers import (
        InventoryModule,
    )

    containers = [
        {"Names": ["one"], "Id": "id1", "Image": "alpine:latest", "Status": "Up", "Labels": {}},
        {"Names": ["two"], "Id": "id2", "Image": "alpine:latest", "Status": "Up", "Labels": {"role": "api"}},
        {"Names": ["three"], "Id": "id3", "Image": "alpine:latest", "Status": "Up", "Labels": {"role": "db"}},
    ]
    with patch(
        "ansible_collections.containers.podman.plugins.inventory.podman_containers.subprocess.check_output",
        return_value=build_ps_json(containers),
    ):
        inv = FakeInventory()
        mod = InventoryModule()
        cfg = {
            "name_patterns": ["t*"],
            "label_selectors": {"role": "api"},
        }
        with patch.object(mod, "_read_config_data", return_value=cfg):
            mod.parse(inv, loader=None, path="dummy.yml", cache=False)

    # Only 'two' matches both name pattern and label
    assert list(inv.hostvars.keys()) == ["two"]


@patch("ansible_collections.containers.podman.plugins.inventory.podman_containers.shutil.which", return_value="podman")
def test_filters_include_exclude_and_status(mock_which):
    from ansible_collections.containers.podman.plugins.inventory.podman_containers import (
        InventoryModule,
    )

    containers = [
        {"Names": ["run-a"], "Id": "r1", "Image": "quay.io/ns/a:latest", "Status": "Up", "Labels": {}},
        {"Names": ["stop-b"], "Id": "s1", "Image": "quay.io/ns/b:latest", "Status": "Exited (0)", "Labels": {}},
    ]
    with patch(
        "ansible_collections.containers.podman.plugins.inventory.podman_containers.subprocess.check_output",
        return_value=build_ps_json(containers),
    ):
        inv = FakeInventory()
        mod = InventoryModule()
        cfg = {
            "include_stopped": True,
            "filters": {"include": {"image": "quay.io/*"}, "exclude": {"status": "exited*"}},
        }
        with patch.object(mod, "_read_config_data", return_value=cfg):
            mod.parse(inv, loader=None, path="dummy.yml", cache=False)

    # Stopped excluded, running included
    assert "run-a" in inv.hostvars
    assert "stop-b" not in inv.hostvars


@patch("ansible_collections.containers.podman.plugins.inventory.podman_containers.shutil.which", return_value="podman")
def test_keyed_groups_and_parent_group(mock_which):
    from ansible_collections.containers.podman.plugins.inventory.podman_containers import (
        InventoryModule,
    )

    containers = [
        {"Names": ["svc"], "Id": "x1", "Image": "img", "Status": "Up", "Labels": {"role": "api"}},
        {"Names": ["svc2"], "Id": "x2", "Image": "img", "Status": "Up", "Labels": {}},
    ]
    with patch(
        "ansible_collections.containers.podman.plugins.inventory.podman_containers.subprocess.check_output",
        return_value=build_ps_json(containers),
    ):
        inv = FakeInventory()
        mod = InventoryModule()
        cfg = {
            "keyed_groups": [
                {"key": "labels.role", "prefix": "k", "separator": "-", "parent_group": "keyed"},
                {"key": "labels.missing", "prefix": "missing", "default_value": "unknown"},
            ]
        }
        with patch.object(mod, "_read_config_data", return_value=cfg):
            mod.parse(inv, loader=None, path="dummy.yml", cache=False)

    assert "k_api" in inv.groups  # sanitized hyphen -> underscore
    assert "svc" in inv.groups["k_api"]["hosts"]
    assert "keyed" in inv.groups
    assert "k_api" in inv.groups["keyed"]["children"]
    assert "missing_unknown" in inv.groups
    assert set(inv.groups["missing_unknown"]["hosts"]) == {"svc", "svc2"}


@patch("ansible_collections.containers.podman.plugins.inventory.podman_containers.shutil.which", return_value="podman")
def test_strict_missing_key_raises(mock_which):
    from ansible_collections.containers.podman.plugins.inventory.podman_containers import (
        InventoryModule,
    )

    containers = [
        {"Names": ["h"], "Id": "id", "Image": "img", "Status": "Up", "Labels": {}},
    ]
    with patch(
        "ansible_collections.containers.podman.plugins.inventory.podman_containers.subprocess.check_output",
        return_value=build_ps_json(containers),
    ):
        inv = FakeInventory()
        mod = InventoryModule()
        cfg = {"strict": True, "keyed_groups": [{"key": "labels.nonexistent"}]}
        with patch.object(mod, "_read_config_data", return_value=cfg):
            with pytest.raises(AnsibleParserError):
                mod.parse(inv, loader=None, path="dummy.yml", cache=False)


@patch("ansible_collections.containers.podman.plugins.inventory.podman_containers.shutil.which", return_value="podman")
def test_include_stopped_toggles_args(mock_which):
    from ansible_collections.containers.podman.plugins.inventory.podman_containers import (
        InventoryModule,
    )

    def fake_co_with_a(args, stderr=None):
        # ensure -a present when include_stopped true
        assert "-a" in args
        return build_ps_json([])

    def fake_co_without_a(args, stderr=None):
        # ensure -a absent when include_stopped false
        assert "-a" not in args
        return build_ps_json([])

    inv = FakeInventory()
    mod = InventoryModule()
    with patch(
        "ansible_collections.containers.podman.plugins.inventory.podman_containers.subprocess.check_output",
        side_effect=fake_co_without_a,
    ):
        with patch.object(mod, "_read_config_data", return_value={"include_stopped": False}):
            mod.parse(inv, loader=None, path="dummy.yml", cache=False)

    inv2 = FakeInventory()
    mod2 = InventoryModule()
    with patch(
        "ansible_collections.containers.podman.plugins.inventory.podman_containers.subprocess.check_output",
        side_effect=fake_co_with_a,
    ):
        with patch.object(mod2, "_read_config_data", return_value={"include_stopped": True}):
            mod2.parse(inv2, loader=None, path="dummy.yml", cache=False)


@patch("ansible_collections.containers.podman.plugins.inventory.podman_containers.shutil.which", return_value="podman")
def test_debug_paths_and_no_host(mock_which):
    from ansible_collections.containers.podman.plugins.inventory.podman_containers import (
        InventoryModule,
    )

    # One container with no name and no id to hit host==None path
    containers = [{}]
    with patch(
        "ansible_collections.containers.podman.plugins.inventory.podman_containers.subprocess.check_output",
        return_value=build_ps_json(containers),
    ):
        inv = FakeInventory()
        mod = InventoryModule()
        cfg = {"filters": {"include": {"name": "nomatch"}}}
        with patch.object(mod, "_read_config_data", return_value=cfg):
            mod.parse(inv, loader=None, path="dummy.yml", cache=False)
    # Nothing added
    assert inv.hostvars == {}


@patch("ansible_collections.containers.podman.plugins.inventory.podman_containers.shutil.which", return_value="podman")
def test_check_output_exception_path(mock_which):
    from ansible_collections.containers.podman.plugins.inventory.podman_containers import (
        InventoryModule,
    )

    with patch(
        "ansible_collections.containers.podman.plugins.inventory.podman_containers.subprocess.check_output",
        side_effect=RuntimeError("boom"),
    ):
        inv = FakeInventory()
        mod = InventoryModule()
        with patch.object(mod, "_read_config_data", return_value={}):
            with pytest.raises(AnsibleParserError):
                mod.parse(inv, loader=None, path="dummy.yml", cache=False)


@patch("ansible_collections.containers.podman.plugins.inventory.podman_containers.shutil.which", return_value="podman")
def test_filter_include_only_and_label_match(mock_which):
    from ansible_collections.containers.podman.plugins.inventory.podman_containers import (
        InventoryModule,
    )

    containers = [
        {"Names": ["svc"], "Id": "x1", "Image": "reg/ns/app:1", "Status": "Up", "Labels": {"tier": "be"}},
        {"Names": ["svc2"], "Id": "x2", "Image": "reg/ns/oth:1", "Status": "Up", "Labels": {"tier": "fe"}},
    ]
    with patch(
        "ansible_collections.containers.podman.plugins.inventory.podman_containers.subprocess.check_output",
        return_value=build_ps_json(containers),
    ):
        inv = FakeInventory()
        mod = InventoryModule()
        cfg = {"filters": {"include": {"label.tier": "be", "image": "reg/*"}}}
        with patch.object(mod, "_read_config_data", return_value=cfg):
            mod.parse(inv, loader=None, path="dummy.yml", cache=False)
    assert list(inv.hostvars.keys()) == ["svc"]


@patch("ansible_collections.containers.podman.plugins.inventory.podman_containers.shutil.which", return_value="podman")
def test_group_by_image_and_label_skip_branches(mock_which):
    from ansible_collections.containers.podman.plugins.inventory.podman_containers import (
        InventoryModule,
    )

    # One without Image to skip image grouping, and one without target label for label grouping
    containers = [
        {"Names": ["nolbl"], "Id": "y1", "Status": "Up", "Labels": {}},
        {"Names": ["haslbl"], "Id": "y2", "Image": "img", "Status": "Up", "Labels": {"other": "x"}},
    ]
    with patch(
        "ansible_collections.containers.podman.plugins.inventory.podman_containers.subprocess.check_output",
        return_value=build_ps_json(containers),
    ):
        inv = FakeInventory()
        mod = InventoryModule()
        cfg = {"group_by_image": True, "group_by_label": ["tier"]}
        with patch.object(mod, "_read_config_data", return_value=cfg):
            mod.parse(inv, loader=None, path="dummy.yml", cache=False)
    # Image "img" should group when present; this asserts grouping executes while label grouping is skipped
    assert "image_img" in inv.groups
    assert "label_tier_x" not in inv.groups


@patch("ansible_collections.containers.podman.plugins.inventory.podman_containers.shutil.which", return_value="podman")
def test_keyed_groups_leading_trailing_separators(mock_which):
    from ansible_collections.containers.podman.plugins.inventory.podman_containers import (
        InventoryModule,
    )

    containers = [
        {"Names": ["svc"], "Id": "x1", "Image": "img", "Status": "Up", "Labels": {"num": 7}},
    ]
    with patch(
        "ansible_collections.containers.podman.plugins.inventory.podman_containers.subprocess.check_output",
        return_value=build_ps_json(containers),
    ):
        inv = FakeInventory()
        mod = InventoryModule()
        cfg = {
            "keyed_groups": [
                {
                    "key": "labels.num",
                    "prefix": "p",
                    "separator": "-",
                    "leading_separator": True,
                    "trailing_separator": True,
                }
            ]
        }
        with patch.object(mod, "_read_config_data", return_value=cfg):
            mod.parse(inv, loader=None, path="dummy.yml", cache=False)
    # Expect group name sanitized; verify host assignment in some group containing 'p' and '7'
    assert any(("p" in g and "7" in g and "svc" in inv.groups[g]["hosts"]) for g in inv.groups)


@patch("ansible_collections.containers.podman.plugins.inventory.podman_containers.shutil.which", return_value="podman")
def test_filters_include_by_id_only(mock_which):
    from ansible_collections.containers.podman.plugins.inventory.podman_containers import (
        InventoryModule,
    )

    containers = [
        {"Names": ["first"], "Id": "idaaa", "Image": "img1", "Status": "Up", "Labels": {}},
        {"Names": ["second"], "Id": "idbbb", "Image": "img2", "Status": "Up", "Labels": {}},
    ]
    with patch(
        "ansible_collections.containers.podman.plugins.inventory.podman_containers.subprocess.check_output",
        return_value=build_ps_json(containers),
    ):
        inv = FakeInventory()
        mod = InventoryModule()
        cfg = {"filters": {"include": {"id": "ida*"}}}
        with patch.object(mod, "_read_config_data", return_value=cfg):
            mod.parse(inv, loader=None, path="dummy.yml", cache=False)
    assert list(inv.hostvars.keys()) == ["first"]


@patch("ansible_collections.containers.podman.plugins.inventory.podman_containers.shutil.which", return_value="podman")
def test_name_falls_back_to_short_id_when_no_names(mock_which):
    from ansible_collections.containers.podman.plugins.inventory.podman_containers import (
        InventoryModule,
    )

    long_id = "1234567890abcdef1234567890abcdef"
    containers = [
        {"Id": long_id, "Image": "img", "Status": "Up", "Labels": {}},
    ]
    with patch(
        "ansible_collections.containers.podman.plugins.inventory.podman_containers.subprocess.check_output",
        return_value=build_ps_json(containers),
    ):
        inv = FakeInventory()
        mod = InventoryModule()
        with patch.object(mod, "_read_config_data", return_value={}):
            mod.parse(inv, loader=None, path="dummy.yml", cache=False)
    # Host should be short id
    assert long_id[:12] in inv.hostvars


@patch("ansible_collections.containers.podman.plugins.inventory.podman_containers.shutil.which", return_value="podman")
def test_filters_unknown_key_path(mock_which):
    from ansible_collections.containers.podman.plugins.inventory.podman_containers import (
        InventoryModule,
    )

    containers = [
        {"Names": ["x"], "Id": "idx", "Image": "img", "Status": "Up", "Labels": {}},
    ]
    with patch(
        "ansible_collections.containers.podman.plugins.inventory.podman_containers.subprocess.check_output",
        return_value=build_ps_json(containers),
    ):
        inv = FakeInventory()
        mod = InventoryModule()
        cfg = {"filters": {"include": {"unknown": "val"}}}
        with patch.object(mod, "_read_config_data", return_value=cfg):
            mod.parse(inv, loader=None, path="dummy.yml", cache=False)
    # Include with unknown key should exclude host
    assert inv.hostvars == {}


@patch("ansible_collections.containers.podman.plugins.inventory.podman_containers.shutil.which", return_value="podman")
def test_include_rules_status_only(mock_which):
    from ansible_collections.containers.podman.plugins.inventory.podman_containers import (
        InventoryModule,
    )

    containers = [
        {"Names": ["run"], "Id": "r1", "Image": "img1", "Status": "Up 2s", "Labels": {}},
        {"Names": ["stop"], "Id": "s1", "Image": "img2", "Status": "Exited (0)", "Labels": {}},
    ]
    with patch(
        "ansible_collections.containers.podman.plugins.inventory.podman_containers.subprocess.check_output",
        return_value=build_ps_json(containers),
    ):
        inv = FakeInventory()
        mod = InventoryModule()
        cfg = {"include_stopped": True, "filters": {"include": {"status": "up*"}}}
        with patch.object(mod, "_read_config_data", return_value=cfg):
            mod.parse(inv, loader=None, path="dummy.yml", cache=False)
    assert list(inv.hostvars.keys()) == ["run"]
