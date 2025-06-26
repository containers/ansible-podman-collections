#!/usr/bin/python
# Copyright (c) 2024 Red Hat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
module: podman_secret_info
author:
  - "Sagi Shnaidman (@sshnaidm)"
short_description: Gather info about podman secrets
notes: []
description:
  - Gather info about podman secrets with podman inspect command.
requirements:
  - "Podman installed on host"
options:
  name:
    description:
      - Name of the secret
    type: str
  showsecret:
    description:
      - Show secret data value
    type: bool
    default: False
  executable:
    description:
      - Path to C(podman) executable if it is not in the C($PATH) on the
        machine running C(podman)
    default: 'podman'
    type: str
"""

EXAMPLES = r"""
- name: Gather info about all present secrets
  podman_secret_info:

- name: Gather info about specific secret
  podman_secret_info:
    name: specific_secret
"""

RETURN = r"""
secrets:
    description: Facts from all or specified secrets
    returned: always
    type: list
    sample: [
                {
                    "ID": "06068c676e9a7f1c7dc0da8dd",
                    "CreatedAt": "2024-01-28T20:32:08.31857841+02:00",
                    "UpdatedAt": "2024-01-28T20:32:08.31857841+02:00",
                    "Spec": {
                        "Name": "secret_name",
                        "Driver": {
                            "Name": "file",
                            "Options": {
                                "path": "/home/user/.local/share/containers/storage/secrets/filedriver"
                            }
                        },
                        "Labels": {}
                    }
                }
        ]
"""

import json
from ansible.module_utils.basic import AnsibleModule


def get_secret_info(module, executable, show, name):
    command = [executable, "secret", "inspect"]
    if show:
        command.append("--showsecret")
    if name:
        command.append(name)
    else:
        all_names = [executable, "secret", "ls", "-q"]
        rc, out, err = module.run_command(all_names)
        name = out.split()
        if not name:
            return [], out, err
        command.extend(name)
    rc, out, err = module.run_command(command)
    if rc != 0 or "no secret with name or id" in err:
        module.fail_json(msg="Unable to gather info for %s: %s" % (name or "all secrets", err))
    if not out or json.loads(out) is None:
        return [], out, err
    return json.loads(out), out, err


def main():
    module = AnsibleModule(
        argument_spec=dict(
            executable=dict(type="str", default="podman"),
            name=dict(type="str"),
            showsecret=dict(type="bool", default=False),
        ),
        supports_check_mode=True,
    )

    name = module.params["name"]
    showsecret = module.params["showsecret"]
    executable = module.get_bin_path(module.params["executable"], required=True)

    inspect_results, out, err = get_secret_info(module, executable, showsecret, name)

    results = {
        "changed": False,
        "secrets": inspect_results,
        "stderr": err,
    }

    module.exit_json(**results)


if __name__ == "__main__":
    main()
