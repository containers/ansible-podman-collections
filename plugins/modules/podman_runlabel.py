#!/usr/bin/python
# coding: utf-8 -*-

# Copyright (c) 2023, Pavel Dostal <@pdostal>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
module: podman_runlabel
short_description: Run given label from given image
author: Pavel Dostal (@pdostal)
description:
  - podman container runlabel runs selected label from given image
options:
  image:
    description:
    - Image to get the label from.
    type: str
    required: true
  label:
    description:
    - Label to run.
    type: str
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
- containers.podman.podman_runlabel:
    image: docker.io/continuumio/miniconda3
    label: INSTALL
"""

from ansible.module_utils.basic import AnsibleModule  # noqa: E402


def runlabel(module, executable):
    changed = False
    command = [executable, "container", "runlabel"]
    command.append(module.params["label"])
    command.append(module.params["image"])
    rc, out, err = module.run_command(command)
    if rc == 0:
        changed = True
    else:
        module.fail_json(msg="Error running the runlabel from image %s: %s" % (module.params["image"], err))
    return changed, out, err


def main():
    module = AnsibleModule(
        argument_spec=dict(
            image=dict(type="str", required=True),
            label=dict(type="str", required=True),
            executable=dict(type="str", default="podman"),
        ),
        supports_check_mode=False,
    )

    executable = module.get_bin_path(module.params["executable"], required=True)
    changed, out, err = runlabel(module, executable)

    results = {"changed": changed, "stdout": out, "stderr": err}
    module.exit_json(**results)


if __name__ == "__main__":
    main()
