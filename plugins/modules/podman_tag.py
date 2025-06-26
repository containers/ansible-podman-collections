#!/usr/bin/python
# coding: utf-8 -*-

# Copyright (c) 2021, Christian Bourque <@ocafebabe>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
module: podman_tag
short_description: Add an additional name to a local image
author: Christian Bourque (@ocafebabe)
description:
  - podman tag adds one or more additional names to locally-stored image.
options:
  image:
    description:
    - Image to tag.
    type: str
    required: true
  target_names:
    description:
    - Additional names.
    type: list
    elements: str
    required: true
  executable:
    description:
      - Path to C(podman) executable if it is not in the C($PATH) on the
        machine running C(podman)
    default: 'podman'
    type: str
requirements:
  - "Podman installed on host"
"""

RETURN = """
"""

EXAMPLES = """
# What modules does for example
- containers.podman.podman_tag:
    image: docker.io/continuumio/miniconda3
    target_names:
      - miniconda3
      - miniconda
"""

from ansible.module_utils.basic import AnsibleModule  # noqa: E402


def tag(module, executable):
    changed = False
    command = [executable, "tag"]
    command.append(module.params["image"])
    command.extend(module.params["target_names"])
    if module.check_mode:
        return changed, "", ""
    rc, out, err = module.run_command(command)
    if rc == 0:
        changed = True
    else:
        module.fail_json(msg="Error tagging local image %s: %s" % (module.params["image"], err))
    return changed, out, err


def main():
    module = AnsibleModule(
        argument_spec=dict(
            image=dict(type="str", required=True),
            target_names=dict(type="list", elements="str", required=True),
            executable=dict(type="str", default="podman"),
        ),
        supports_check_mode=True,
    )

    executable = module.get_bin_path(module.params["executable"], required=True)
    changed, out, err = tag(module, executable)

    results = {
        "changed": changed,
        "stdout": out,
        "stderr": err,
    }
    module.exit_json(**results)


if __name__ == "__main__":
    main()
