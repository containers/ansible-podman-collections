from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json
from unittest.mock import patch


class FakeInventory:
    def __init__(self):
        self.hostvars = {}
        self.groups = {}

    def add_group(self, name):
        self.groups.setdefault(name, {"hosts": [], "children": []})

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


def build_containers_json(entries):
    return json.dumps(entries).encode("utf-8")


@patch(
    "ansible_collections.containers.podman.plugins.inventory.buildah_containers.shutil.which", return_value="buildah"
)
def test_basic_buildah_inventory(mock_which):
    from ansible_collections.containers.podman.plugins.inventory.buildah_containers import (
        InventoryModule,
    )

    containers = [
        {"name": "w1", "id": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "containername": "w1"},
        {"containername": "build/with/slash", "containerid": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"},
        {"id": "cccccccccccccccccccccccccccccccc"},  # no name
    ]
    with patch(
        "ansible_collections.containers.podman.plugins.inventory.buildah_containers.subprocess.check_output",
        return_value=build_containers_json(containers),
    ):
        inv = FakeInventory()
        mod = InventoryModule()
        cfg = {"connection_plugin": "containers.podman.buildah"}
        with patch.object(mod, "_read_config_data", return_value=cfg):
            mod.parse(inv, loader=None, path="dummy.yml", cache=False)

    # Names resolved
    assert "w1" in inv.hostvars
    assert "build/with/slash" in inv.hostvars
    # Unnamed container present (either as short id or full id depending on plugin behavior)
    unnamed_id = "cccccccccccccccccccccccccccccccc"
    assert (unnamed_id in inv.hostvars) or (unnamed_id[:12] in inv.hostvars)
    # Hostvars contain id/name
    assert inv.hostvars["w1"]["buildah_container_id"].startswith("a")
    assert inv.hostvars["w1"]["buildah_container_name"] == "w1"


@patch(
    "ansible_collections.containers.podman.plugins.inventory.buildah_containers.shutil.which", return_value="buildah"
)
def test_name_patterns_filtering_buildah(mock_which):
    from ansible_collections.containers.podman.plugins.inventory.buildah_containers import (
        InventoryModule,
    )

    containers = [
        {"name": "alpha", "id": "id1"},
        {"name": "beta", "id": "id2"},
        {"name": "gamma", "id": "id3"},
    ]
    with patch(
        "ansible_collections.containers.podman.plugins.inventory.buildah_containers.subprocess.check_output",
        return_value=build_containers_json(containers),
    ):
        inv = FakeInventory()
        mod = InventoryModule()
        cfg = {"name_patterns": ["b*", "id3"], "connection_plugin": "containers.podman.buildah"}
        with patch.object(mod, "_read_config_data", return_value=cfg):
            mod.parse(inv, loader=None, path="dummy.yml", cache=False)

    # Should include beta by name pattern, and gamma via id pattern
    assert set(inv.hostvars.keys()) == {"beta", "gamma"}


def test_verify_inventory_file_helper():
    from ansible_collections.containers.podman.plugins.module_utils.inventory.utils import (
        verify_inventory_file,
    )

    class Dummy:
        NAME = "containers.podman.buildah_containers"

    # wrong extension
    assert not verify_inventory_file(Dummy(), "inv.txt")
    # missing plugin header
    p = "/tmp/test_inv.yml"
    with open(p, "w", encoding="utf-8") as f:
        f.write("foo: bar\n")
    assert not verify_inventory_file(Dummy(), p)
    # correct header
    with open(p, "w", encoding="utf-8") as f:
        f.write("plugin: containers.podman.buildah_containers\n")
    assert verify_inventory_file(Dummy(), p)
