#!/usr/bin/python
# coding: utf-8 -*-

# Copyright (c) 2021, Sagi Shnaidman <sshnaidm@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
module: podman_export
short_description: Export a podman container
author: Sagi Shnaidman (@sshnaidm)
description:
  - podman export exports the filesystem of a container and saves it as a
    tarball on the local machine
options:
  dest:
    description:
    - Path to export container to.
    type: str
    required: true
  container:
    description:
    - Container to export.
    type: str
  volume:
    description:
    - Volume to export.
    type: str
  force:
    description:
    - Force saving to file even if it exists.
    type: bool
    default: True
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
- containers.podman.podman_export:
    dest: /path/to/tar/file
    container: container-name
- containers.podman.podman_export:
    dest: /path/to/tar/file
    volume: volume-name
"""

import os  # noqa: E402
from ansible.module_utils.basic import AnsibleModule  # noqa: E402
from ..module_utils.podman.common import remove_file_or_dir  # noqa: E402


def export(module, executable):
    changed = False
    export_type = ""
    command = []
    if module.params["container"]:
        export_type = "container"
        command = [executable, "export"]
    else:
        export_type = "volume"
        command = [executable, "volume", "export"]

    command += ["-o=%s" % module.params["dest"], module.params[export_type]]
    if module.params["force"]:
        dest = module.params["dest"]
        if os.path.exists(dest):
            changed = True
            if module.check_mode:
                return changed, "", ""
            try:
                remove_file_or_dir(dest)
            except Exception as e:
                module.fail_json(msg="Error deleting %s path: %s" % (dest, e))
    else:
        changed = not os.path.exists(module.params["dest"])
    if module.check_mode:
        return changed, "", ""
    rc, out, err = module.run_command(command)
    if rc != 0:
        module.fail_json(msg="Error exporting %s %s: %s" % (export_type, module.params["container"], err))
    return changed, out, err


def main():
    module = AnsibleModule(
        argument_spec=dict(
            dest=dict(type="str", required=True),
            container=dict(type="str"),
            volume=dict(type="str"),
            force=dict(type="bool", default=True),
            executable=dict(type="str", default="podman"),
        ),
        supports_check_mode=True,
        mutually_exclusive=[
            ("container", "volume"),
        ],
        required_one_of=[
            ("container", "volume"),
        ],
    )

    executable = module.get_bin_path(module.params["executable"], required=True)
    changed, out, err = export(module, executable)

    results = {
        "changed": changed,
        "stdout": out,
        "stderr": err,
    }
    module.exit_json(**results)


if __name__ == "__main__":
    main()
