# Copyright (c) 2025
# GNU General Public License v3.0+

from __future__ import annotations

__metaclass__ = type

DOCUMENTATION = r"""
    name: podman_containers
    short_description: Inventory plugin that discovers Podman containers as hosts
    version_added: '1.18.0'
    description:
      - Discover running (and optionally stopped) Podman containers on the local host and add them as inventory hosts.
      - Each discovered host is assigned an Ansible connection plugin so tasks execute inside the container without SSH.
    options:
      plugin:
        description: Token that ensures this is a source file for the 'containers.podman.podman_containers' inventory plugin.
        required: true
        type: str
        choices: ['containers.podman.podman_containers']
      executable:
        description: Path to the C(podman) executable.
        type: str
        default: podman
        env:
          - name: ANSIBLE_PODMAN_EXECUTABLE
      include_stopped:
        description: Whether to include stopped/exited containers.
        type: bool
        default: false
      name_patterns:
        description: Glob patterns to match container names or IDs; empty means include all.
        type: list
        elements: str
        default: []
      label_selectors:
        description: Key/value labels that must match (all) for a container to be included.
        type: dict
        default: {}
      connection_plugin:
        description: Fully-qualified connection plugin to use for discovered hosts.
        type: str
        default: containers.podman.podman
      group_by_image:
        description: Add containers to a group derived from image name (e.g., C(image_node_14)).
        type: bool
        default: true
      group_by_label:
        description: Label keys to group containers by (C(label_<key>_<value>)).
        type: list
        elements: str
        default: []
"""

EXAMPLES = r"""
plugin: containers.podman.podman_containers
include_stopped: false
label_selectors:
  role: api
connection_plugin: containers.podman.podman
"""

import json
import fnmatch
import shutil
import subprocess
import os
from typing import Dict, List

from ansible.errors import AnsibleParserError
from ansible.plugins.inventory import BaseInventoryPlugin, Cacheable


class InventoryModule(BaseInventoryPlugin, Cacheable):
    NAME = "containers.podman.podman_containers"

    def verify_file(self, path: str) -> bool:
        if not super(InventoryModule, self).verify_file(path):
            return False
        unused, ext = os.path.splitext(path)
        if ext not in (".yml", ".yaml"):
            return False
        try:
            with open(path, "r", encoding="utf-8") as f:
                header = f.read(2048)
            return (
                (f"plugin: {self.NAME}\n" in header)
                or (f"plugin: '{self.NAME}'" in header)
                or (f'plugin: "{self.NAME}"' in header)
            )
        except Exception:
            return False

    def parse(self, inventory, loader, path, cache=True):
        super(InventoryModule, self).parse(inventory, loader, path)
        config = self._read_config_data(path)

        executable = config.get("executable", "podman")
        include_stopped = bool(config.get("include_stopped", False))
        name_patterns = list(config.get("name_patterns", []) or [])
        label_selectors: Dict[str, str] = dict(config.get("label_selectors", {}) or {})
        connection_plugin = config.get("connection_plugin", "containers.podman.podman")
        group_by_image = bool(config.get("group_by_image", True))
        group_by_label: List[str] = list(config.get("group_by_label", []) or [])

        podman_path = shutil.which(executable) or executable

        args = [podman_path, "ps", "--format", "json"]
        if include_stopped:
            args.insert(2, "-a")

        try:
            output = subprocess.check_output(args, stderr=subprocess.STDOUT)
            containers = json.loads(output.decode("utf-8"))
        except Exception as exc:
            raise AnsibleParserError(f"Failed to list podman containers: {exc}")

        for c in containers or []:
            name = (
                (c.get("Names") or [c.get("Names", "")])[0]
                if isinstance(c.get("Names"), list)
                else c.get("Names") or c.get("Names", "")
            )
            cid = c.get("Id") or c.get("ID") or c.get("Id")
            if not name and cid:
                name = cid[:12]

            # name filtering
            if name_patterns:
                if not any(fnmatch.fnmatch(name, pat) or (cid and fnmatch.fnmatch(cid, pat)) for pat in name_patterns):
                    continue

            # label filtering
            labels = c.get("Labels") or {}
            if any(labels.get(k) != v for k, v in label_selectors.items()):
                continue

            host = name or cid
            if not host:
                continue

            self.inventory.add_host(host)
            # Set connection plugin and remote_addr (container id or name works)
            self.inventory.set_variable(host, "ansible_connection", connection_plugin)
            self.inventory.set_variable(host, "ansible_host", name or cid)

            # Common vars
            image = c.get("Image") or c.get("ImageName")
            status = c.get("Status") or c.get("State")
            self.inventory.set_variable(host, "podman_container_id", cid)
            self.inventory.set_variable(host, "podman_container_name", name)
            if image:
                self.inventory.set_variable(host, "podman_image", image)
            if status:
                self.inventory.set_variable(host, "podman_status", status)
            if labels:
                self.inventory.set_variable(host, "podman_labels", labels)

            # Grouping
            if group_by_image and image:
                safe_image = image.replace(":", "_").replace("/", "_").replace("-", "_")
                self.inventory.add_group(f"image_{safe_image}")
                self.inventory.add_host(host, group=f"image_{safe_image}")

            for key in group_by_label:
                if key in labels:
                    val = str(labels.get(key)).replace("/", "_").replace(":", "_").replace("-", "_")
                    group = f"label_{key}_{val}"
                    self.inventory.add_group(group)
                    self.inventory.add_host(host, group=group)
