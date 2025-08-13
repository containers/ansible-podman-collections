# Copyright (c) 2025
# GNU General Public License v3.0+

from __future__ import annotations

__metaclass__ = type

DOCUMENTATION = r"""
    name: podman_containers
    short_description: Inventory plugin that discovers Podman containers as hosts
    version_added: '1.18.0'
    author:
      - "Sagi Shnaidman (@sshnaidm)"
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
      # Additional options (non-API dependent), aligned with community.docker
      verbose_output:
        description: When true, store raw C(podman ps --format json) entry under C(podman_ps) host var.
        type: bool
        default: false
      strict:
        description: Fail when keyed/composed grouping references missing data.
        type: bool
        default: false
      keyed_groups:
        description: Create groups based on hostvars/labels.
        type: list
        elements: dict
        default: []
      groups:
        description: Add hosts to groups based on Jinja2 conditionals.
        type: dict
        default: {}
      filters:
        description: Include/exclude selection by attributes - C(name), C(id), C(image), C(status), or C(label.<key>).
        type: dict
        default: {}
      # Logging uses Ansible verbosity (-v/-vvv). Extra debug option is not required.
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

from ansible.errors import AnsibleParserError
from ansible.plugins.inventory import BaseInventoryPlugin, Cacheable, Constructable
from ansible_collections.containers.podman.plugins.module_utils.inventory.utils import verify_inventory_file


class InventoryModule(BaseInventoryPlugin, Cacheable, Constructable):
    NAME = "containers.podman.podman_containers"

    def __init__(self):
        super(InventoryModule, self).__init__()

    def verify_file(self, path: str) -> bool:
        if not super(InventoryModule, self).verify_file(path):
            return False
        return verify_inventory_file(self, path)

    def parse(self, inventory, loader, path, cache=True):
        super(InventoryModule, self).parse(inventory, loader, path)
        config = self._read_config_data(path)

        executable = config.get("executable", "podman")
        include_stopped = bool(config.get("include_stopped", False))
        name_patterns = list(config.get("name_patterns", []) or [])
        label_selectors = dict(config.get("label_selectors", {}) or {})
        connection_plugin = config.get("connection_plugin", "containers.podman.podman")
        group_by_image = bool(config.get("group_by_image", True))
        group_by_label = list(config.get("group_by_label", []) or [])
        verbose_output = bool(config.get("verbose_output", False))
        strict = bool(config.get("strict", False))
        keyed_groups = list(config.get("keyed_groups", []) or [])
        composed_groups = dict(config.get("groups", {}) or {})
        filters = dict(config.get("filters", {}) or {})
        # Logging is controlled by Ansible verbosity flags

        podman_path = shutil.which(executable) or executable

        args = [podman_path, "ps", "--format", "json"]
        if include_stopped:
            args.insert(2, "-a")

        output = ""
        containers = []
        try:
            output = subprocess.check_output(args, stderr=subprocess.STDOUT)
            containers = json.loads(output.decode("utf-8"))
        except Exception as exc:
            raise AnsibleParserError(f"Failed to list podman containers: {exc} from output {output}")

        def matches_filters(name, cid, image, status, labels):
            include_rules = dict(filters.get("include", {}) or {})
            exclude_rules = dict(filters.get("exclude", {}) or {})

            def matches_one(k, v):
                if k.startswith("label."):
                    lk = k.split(".", 1)[1]
                    return fnmatch.fnmatch(str((labels or {}).get(lk, "")).lower(), str(v).lower())
                if k == "name":
                    return fnmatch.fnmatch((name or "").lower(), str(v).lower())
                if k == "id":
                    return fnmatch.fnmatch((cid or "").lower(), str(v).lower())
                if k == "image":
                    return fnmatch.fnmatch((image or "").lower(), str(v).lower())
                if k == "status":
                    return fnmatch.fnmatch((status or "").lower(), str(v).lower())
                return False

            if include_rules:
                for k, v in include_rules.items():
                    if not matches_one(k, v):
                        return False
            for k, v in exclude_rules.items():
                if matches_one(k, v):
                    return False
            return True

        for c in containers:
            name = (
                (c.get("Names") or [c.get("Names", "")])[0]
                if isinstance(c.get("Names"), list)
                else c.get("Names") or c.get("Names", "")
            )
            cid = c.get("Id") or c.get("ID")
            if not name and cid:
                name = cid[:12]

            # name filtering
            if name_patterns:
                if not any(fnmatch.fnmatch(name, pat) or (cid and fnmatch.fnmatch(cid, pat)) for pat in name_patterns):
                    self.display.vvvv(f"Filtered out {name or cid} by name_patterns option")
                    continue

            # label filtering
            labels = c.get("Labels") or {}
            if any(labels.get(k) != v for k, v in label_selectors.items()):
                self.display.vvvv(f"Filtered out {name or cid} by label_selectors option")
                continue

            image = c.get("Image") or c.get("ImageName")
            status = c.get("Status") or c.get("State")

            # additional include/exclude filters
            if filters and not matches_filters(name, cid, image, status, labels):
                self.display.vvvv(f"Filtered out {name or cid} by filters option")
                continue

            host = name or cid
            if not host:
                self.display.vvvv(f"Filtered out {name or cid} by no name or cid")
                continue

            self.inventory.add_host(host)
            # Set connection plugin and remote_addr (container id or name works)
            self.inventory.set_variable(host, "ansible_connection", connection_plugin)
            self.inventory.set_variable(host, "ansible_host", name or cid)

            # Common vars
            self.inventory.set_variable(host, "podman_container_id", cid)
            self.inventory.set_variable(host, "podman_container_name", name)
            if image:
                self.inventory.set_variable(host, "podman_image", image)
            if status:
                self.inventory.set_variable(host, "podman_status", status)
            if labels:
                self.inventory.set_variable(host, "podman_labels", labels)
            if verbose_output:
                self.inventory.set_variable(host, "podman_ps", c)

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

            # Composed and keyed groups
            hostvars = {
                "name": name,
                "id": cid,
                "image": image,
                "status": status,
                "labels": labels,
            }
            try:
                if composed_groups:
                    self._add_host_to_composed_groups(composed_groups, hostvars, host)
                if keyed_groups:
                    # Try built-in helper first (signature may vary by ansible-core), do not fail hard
                    try:
                        self._add_host_to_keyed_groups(keyed_groups, hostvars, host)
                    except Exception as _e:
                        self.display.vvvv(f"_add_host_to_keyed_groups helper failed: {_e}")
                    # Always run manual keyed grouping to support dotted keys like labels.role
                    for kg in keyed_groups:
                        key_expr = kg.get("key")
                        if not key_expr:
                            continue
                        # Resolve dotted key path against hostvars
                        value = None
                        cur = hostvars
                        for part in str(key_expr).split("."):
                            if isinstance(cur, dict) and part in cur:
                                cur = cur.get(part)
                            else:
                                cur = None
                                break
                        value = cur if isinstance(cur, (str, int)) else (cur if cur is not None else None)
                        if value is None:
                            if strict and kg.get("default_value") is None:
                                raise AnsibleParserError(f"Missing keyed_groups key '{key_expr}' for host {host}")
                            value = kg.get("default_value")
                        if value is None or value == "":
                            continue
                        value = str(value)
                        prefix = kg.get("prefix", "") or ""
                        sep = kg.get("separator", "_") or "_"
                        leading = bool(kg.get("leading_separator", False))
                        trailing = bool(kg.get("trailing_separator", False))
                        group_name = ""
                        if leading and not prefix:
                            group_name += sep
                        if prefix:
                            group_name += prefix
                            if value:
                                group_name += sep
                        group_name += value
                        if trailing:
                            group_name += sep
                        parent = kg.get("parent_group")
                        # Sanitize group names per Ansible rules
                        sanitized = self._sanitize_group_name(group_name)
                        parent_sanitized = self._sanitize_group_name(parent) if parent else None
                        if parent_sanitized:
                            self.inventory.add_group(parent_sanitized)
                            self.inventory.add_group(sanitized)
                            try:
                                self.inventory.add_child(parent_sanitized, sanitized)
                            except Exception:
                                pass
                            self.inventory.add_host(host, group=sanitized)
                        else:
                            self.inventory.add_group(sanitized)
                            self.inventory.add_host(host, group=sanitized)
            except Exception as exc:
                if strict:
                    raise
                self.display.vvvv(f"Grouping error for host {host}: {exc}")
