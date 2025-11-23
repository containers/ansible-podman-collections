#!/usr/bin/python
# Copyright (c) 2025 Red Hat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# flake8: noqa: E501
from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
module: podman_quadlet_info
author:
  - "Sagi Shnaidman (@sshnaidm)"
short_description: Gather information about Podman Quadlets
description:
  - List installed Podman Quadlets or print one quadlet content using C(podman quadlet list/print).
  - Gather information about Podman Quadlets available on the system.
options:
  name:
    description:
      - Name of the quadlet to print content for.
      - When specified, runs C(podman quadlet print) instead of list.
    type: str
    required: false
  kinds:
    description:
      - List of quadlet kinds to filter by (based on file suffix).
      - For example, C(container) matches quadlets ending with C(.container).
    type: list
    elements: str
    choices:
      - container
      - pod
      - network
      - volume
      - kube
      - image
    required: false
  quadlet_dir:
    description:
      - Filter results to quadlets whose path is under this directory.
      - By default no filtering is applied.
    type: path
    required: false
  executable:
    description:
      - Path to the podman executable.
    type: str
    default: podman
  cmd_args:
    description:
      - Extra global arguments to pass to the C(podman) command (e.g., C(--log-level=debug)).
      - These are placed after the executable and before the subcommand.
    type: list
    elements: str
    required: false
  debug:
    description:
      - Return additional debug information.
    type: bool
    default: false
"""

EXAMPLES = r"""
- name: List all quadlets
  containers.podman.podman_quadlet_info:

- name: Get information about a specific quadlet
  containers.podman.podman_quadlet_info:
    name: myapp.container

- name: List only container quadlets
  containers.podman.podman_quadlet_info:
    kinds:
      - container

- name: List quadlets in a custom directory
  containers.podman.podman_quadlet_info:
    quadlet_dir: /etc/containers/systemd
"""


RETURN = r"""
changed:
  description: Always false
  returned: always
  type: bool
quadlets:
  description: List of installed quadlets when listing
  returned: when name is not provided
  type: list
content:
  description: Content of the quadlet when name is provided
  returned: when name is provided
  type: str
stdout:
  description: podman stdout
  returned: when debug=true
  type: str
stderr:
  description: podman stderr
  returned: when debug=true
  type: str
"""


import json
import os

from ansible.module_utils.basic import AnsibleModule  # noqa: F402

try:
    from ansible.module_utils.common.text.converters import to_native  # noqa: F402
except ImportError:
    from ansible.module_utils.common.text import to_native  # noqa: F402


# Mapping from kind name to file suffix
KIND_SUFFIXES = {
    "container": ".container",
    "pod": ".pod",
    "network": ".network",
    "volume": ".volume",
    "kube": ".kube",
    "image": ".image",
}


def _get_quadlet_kind(name):
    """Extract kind from quadlet name based on suffix."""
    if not name:
        return None
    for kind, suffix in KIND_SUFFIXES.items():
        if name.endswith(suffix):
            return kind
    return None


def _build_base_cmd(module, executable):
    """Build base command with executable and global args."""
    cmd = [executable]
    if module.params.get("cmd_args"):
        cmd.extend(module.params["cmd_args"])
    return cmd


def _list_quadlets(module, executable):
    """List installed quadlets with optional filtering."""
    cmd = _build_base_cmd(module, executable)
    cmd.extend(["quadlet", "list", "--format", "json"])

    module.log("PODMAN-QUADLET-INFO-DEBUG: %s" % " ".join([to_native(i) for i in cmd]))
    rc, out, err = module.run_command(cmd)

    if rc != 0:
        module.fail_json(msg="Failed to list quadlets: %s" % err, stdout=out, stderr=err)

    # Strict JSON parsing - fail on errors instead of returning empty
    try:
        data = json.loads(out) if out.strip() else []
    except json.JSONDecodeError as e:
        module.fail_json(
            msg="Failed to parse quadlet list output: %s" % str(e),
            stdout=out,
            stderr=err,
        )

    # Filter by kinds (based on file suffix in Name)
    kinds = module.params.get("kinds")
    if kinds:
        kinds_set = set(kinds)
        filtered = []
        for q in data:
            name = q.get("Name", "")
            kind = _get_quadlet_kind(name)
            if kind and kind in kinds_set:
                filtered.append(q)
        data = filtered

    # Filter by quadlet_dir (based on Path)
    quadlet_dir = module.params.get("quadlet_dir")
    if quadlet_dir:
        # Normalize the directory path
        quadlet_dir = os.path.normpath(quadlet_dir)
        filtered = []
        for q in data:
            path = q.get("Path", "")
            if path:
                # Check if the quadlet's path is under the specified directory
                normalized_path = os.path.normpath(path)
                if normalized_path.startswith(quadlet_dir + os.sep) or os.path.dirname(normalized_path) == quadlet_dir:
                    filtered.append(q)
        data = filtered

    result = {
        "changed": False,
        "quadlets": data,
    }
    if module.params["debug"]:
        result.update({"stdout": out, "stderr": err})
    return result


def _print_quadlet(module, executable):
    """Print content of a specific quadlet."""
    name = module.params["name"]
    cmd = _build_base_cmd(module, executable)
    cmd.extend(["quadlet", "print", name])

    module.log("PODMAN-QUADLET-INFO-DEBUG: %s" % " ".join([to_native(i) for i in cmd]))
    rc, out, err = module.run_command(cmd)

    if rc != 0:
        module.fail_json(msg="Failed to print quadlet %s: %s" % (name, err), stdout=out, stderr=err)

    result = {
        "changed": False,
        "content": out,
    }
    if module.params["debug"]:
        result.update({"stdout": out, "stderr": err})
    return result


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type="str", required=False),
            quadlet_dir=dict(type="path", required=False),
            kinds=dict(
                type="list",
                elements="str",
                required=False,
                choices=["container", "pod", "network", "volume", "kube", "image"],
            ),
            executable=dict(type="str", default="podman"),
            cmd_args=dict(type="list", elements="str", required=False),
            debug=dict(type="bool", default=False),
        ),
        supports_check_mode=True,
    )

    executable = module.get_bin_path(module.params["executable"], required=True)

    if module.params.get("name"):
        result = _print_quadlet(module, executable)
    else:
        result = _list_quadlets(module, executable)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
