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
      - Name of the quadlet to gather information about.
    type: str
    required: false
  kinds:
    description:
      - List of quadlet kinds to filter by.
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
      - Directory where quadlet files are located.
    type: path
    required: false
  executable:
    description:
      - Path to the podman executable.
    type: str
    default: podman
  cmd_args:
    description:
      - Extra arguments to pass to the C(podman) command (e.g., C(--log-level=debug)).
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

from ansible.module_utils.basic import AnsibleModule  # noqa: F402
from ansible.module_utils._text import to_native  # noqa: F402


def _run(module, cmd, capture=True):
    module.log("PODMAN-QUADLET-INFO-DEBUG: %s" % " ".join([to_native(i) for i in cmd]))
    rc, out, err = module.run_command(cmd)
    if rc != 0:
        module.fail_json(msg="Failed to run: %s" % err)
    return out, err


def _list_quadlets(module):
    cmd = [module.params["executable"], "quadlet", "list", "--format", "json"]
    if module.params.get("cmd_args"):
        cmd.extend(module.params["cmd_args"])

    rc, out, err = module.run_command(cmd)
    if rc != 0:
        module.fail_json(msg="Failed to list quadlets: %s" % err, stdout=out, stderr=err)
    try:
        data = json.loads(out) if out else []
    except Exception:
        data = []
    kinds = module.params.get("kinds")
    if kinds:
        kinds = set(kinds)
        data = [d for d in data if str(d.get("kind") or d.get("type") or "").lower() in kinds]

    result = {
        "changed": False,
        "quadlets": data,
    }
    if module.params["debug"]:
        result.update({"stdout": out, "stderr": err})
    return result


def _print_quadlet(module):
    name = module.params["name"]
    cmd = [module.params["executable"], "quadlet", "print", name]
    if module.params.get("cmd_args"):
        cmd.extend(module.params["cmd_args"])
    out, err = _run(module, cmd)
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
    if module.params.get("name"):
        result = _print_quadlet(module)
    else:
        result = _list_quadlets(module)
    module.exit_json(**result)


if __name__ == "__main__":
    main()
