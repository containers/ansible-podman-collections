# Copyright (c) 2025
# GNU General Public License v3.0+

from __future__ import annotations

__metaclass__ = type

DOCUMENTATION = r"""
    name: buildah_containers
    short_description: Inventory plugin that discovers Buildah working containers as hosts
    version_added: '1.18.0'
    author:
      - "Sagi Shnaidman (@sshnaidm)"
    description:
      - Discover Buildah working containers on the local host and add them as inventory hosts.
      - Each discovered host is assigned the Buildah connection plugin so tasks execute inside the working container.
    options:
      plugin:
        description: Token that ensures this is a source file for the 'containers.podman.buildah_containers' inventory plugin.
        required: true
        type: str
        choices: ['containers.podman.buildah_containers']
      executable:
        description: Path to the C(buildah) executable.
        type: str
        default: buildah
        env:
          - name: ANSIBLE_BUILDAH_EXECUTABLE
      name_patterns:
        description: Glob patterns to match working container names or IDs; empty means include all.
        type: list
        elements: str
        default: []
      connection_plugin:
        description: Fully-qualified connection plugin to use for discovered hosts.
        type: str
        default: containers.podman.buildah
      # Logging uses Ansible verbosity (-v/-vvv). Extra debug option is not required.
"""

EXAMPLES = r"""
plugin: containers.podman.buildah_containers
connection_plugin: containers.podman.buildah
name_patterns:
  - my-build-*
"""

import json
import fnmatch
import shutil
import subprocess

from ansible.errors import AnsibleParserError
from ansible.plugins.inventory import BaseInventoryPlugin, Cacheable, Constructable
from ansible_collections.containers.podman.plugins.module_utils.inventory.utils import verify_inventory_file


class InventoryModule(BaseInventoryPlugin, Cacheable, Constructable):
    NAME = "containers.podman.buildah_containers"

    def verify_file(self, path: str) -> bool:
        if not super(InventoryModule, self).verify_file(path):
            return False
        return verify_inventory_file(self, path)

    def parse(self, inventory, loader, path, cache=True):
        super(InventoryModule, self).parse(inventory, loader, path)
        config = self._read_config_data(path)

        executable = config.get("executable", "buildah")
        name_patterns = list(config.get("name_patterns", []) or [])
        connection_plugin = config.get("connection_plugin", "containers.podman.buildah")
        # Logging is controlled by Ansible verbosity flags

        buildah_path = shutil.which(executable) or executable

        # 'buildah containers -a --format json' lists working containers
        args = [buildah_path, "containers", "-a", "--json"]
        output = ""
        containers = []
        try:
            output = subprocess.check_output(args, stderr=subprocess.STDOUT)
            containers = json.loads(output.decode("utf-8"))
        except Exception as exc:
            raise AnsibleParserError(f"Failed to list buildah containers: {exc} from output {output}")

        for c in containers:
            name = c.get("name") or c.get("containername") or c.get("id")
            cid = c.get("id") or c.get("containerid")
            if not name and cid:
                name = cid[:12]

            # name filtering
            if name_patterns:
                if not any(fnmatch.fnmatch(name, pat) or (cid and fnmatch.fnmatch(cid, pat)) for pat in name_patterns):
                    self.display.vvvv(f"Filtered out {name or cid} by name_patterns option")
                    continue

            host = name or cid
            if not host:
                self.display.vvvv(f"Filtered out {name or cid} by no name or cid")
                continue

            self.inventory.add_host(host)
            self.inventory.set_variable(host, "ansible_connection", connection_plugin)
            self.inventory.set_variable(host, "ansible_host", name or cid)
            if cid:
                self.inventory.set_variable(host, "buildah_container_id", cid)
            if name:
                self.inventory.set_variable(host, "buildah_container_name", name)
