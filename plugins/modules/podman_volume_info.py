#!/usr/bin/python
# Copyright (c) 2020 Red Hat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
module: podman_volume_info
author:
  - "Sagi Shnaidman (@sshnaidm)"
short_description: Gather info about podman volumes
notes: []
description:
  - Gather info about podman volumes with podman inspect command.
requirements:
  - "Podman installed on host"
options:
  name:
    description:
      - Name of the volume
    type: str
  executable:
    description:
      - Path to C(podman) executable if it is not in the C($PATH) on the
        machine running C(podman)
    default: 'podman'
    type: str
"""

EXAMPLES = r"""
- name: Gather info about all present volumes
  podman_volume_info:

- name: Gather info about specific volume
  podman_volume_info:
    name: specific_volume
"""

RETURN = r"""
volumes:
    description: Facts from all or specified volumes
    returned: always
    type: list
    sample: [
                {
                    "Name": "postgres9",
                    "Driver": "local",
                    "Mountpoint": "/home/user/.local/share/containers/storage/volumes/postgres9/_data",
                    "CreatedAt": "2023-11-30T16:41:31.310865559+02:00",
                    "Labels": {},
                    "Scope": "local",
                    "Options": {},
                    "MountCount": 0,
                    "NeedsCopyUp": true,
                    "NeedsChown": true,
                    "LockNumber": 18
                }
        ]
"""

import json
from ansible.module_utils.basic import AnsibleModule


def get_volume_info(module, executable, name):
    command = [executable, "volume", "inspect"]
    if name:
        command.append(name)
    else:
        command.append("--all")
    rc, out, err = module.run_command(command)
    if rc != 0 or "no such volume" in err:
        module.fail_json(msg="Unable to gather info for %s: %s" % (name or "all volumes", err))
    if not out or json.loads(out) is None:
        return [], out, err
    return json.loads(out), out, err


def main():
    module = AnsibleModule(
        argument_spec=dict(executable=dict(type="str", default="podman"), name=dict(type="str")),
        supports_check_mode=True,
    )

    name = module.params["name"]
    executable = module.get_bin_path(module.params["executable"], required=True)

    inspect_results, out, err = get_volume_info(module, executable, name)

    results = {"changed": False, "volumes": inspect_results, "stderr": err}

    module.exit_json(**results)


if __name__ == "__main__":
    main()
