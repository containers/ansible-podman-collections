#!/usr/bin/python
# Copyright (c) 2020 Red Hat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
module: podman_network_info
author:
  - "Sagi Shnaidman (@sshnaidm)"
version_added: '1.0.0'
short_description: Gather info about podman networks
notes: []
description:
  - Gather info about podman networks with podman inspect command.
requirements:
  - "Podman installed on host"
options:
  name:
    description:
      - Name of the network
    type: str
  executable:
    description:
      - Path to C(podman) executable if it is not in the C($PATH) on the
        machine running C(podman)
    default: 'podman'
    type: str
"""

EXAMPLES = r"""
- name: Gather info about all present networks
  containers.podman.podman_network_info:

- name: Gather info about specific network
  containers.podman.podman_network_info:
    name: podman
"""

RETURN = r"""
networks:
    description: Facts from all or specified networks
    returned: always
    type: list
    sample: [
              {
                "name": "dmz",
                "id": "3227f9785ae4657c022c8da7b0e04d2d124199e66da10a9130437e3c3f0e0e42",
                "driver": "macvlan",
                "created": "2024-05-27T21:09:03.486699659+03:00",
                "subnets": [
                    {
                            "subnet": "10.10.0.0/24",
                            "gateway": "10.10.0.1",
                            "lease_range": {
                                "start_ip": "10.10.0.249",
                                "end_ip": "10.10.0.255"
                            }
                    },
                    {
                            "subnet": "2001:db8:abcd:10::/64",
                            "gateway": "2001:db8:abcd:10::1"
                    }
                ],
                "ipv6_enabled": true,
                "internal": false,
                "dns_enabled": false,
                "options": {
                    "no_default_route": "true"
                },
                "ipam_options": {
                    "driver": "host-local"
                }
            }
        ]
"""

import json
from ansible.module_utils.basic import AnsibleModule


def get_network_info(module, executable, name):
    command = [executable, "network", "inspect"]
    if not name:
        all_names = [executable, "network", "ls", "-q"]
        rc, out, err = module.run_command(all_names)
        if rc != 0:
            module.fail_json(msg="Unable to get list of networks: %s" % err)
        name = out.split()
        if not name:
            return [], out, err
        command += name
    else:
        command.append(name)
    rc, out, err = module.run_command(command)
    if rc != 0 or "unable to find network configuration" in err:
        module.fail_json(msg="Unable to gather info for %s: %s" % (name, err))
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

    inspect_results, out, err = get_network_info(module, executable, name)

    results = {"changed": False, "networks": inspect_results, "stderr": err}

    module.exit_json(**results)


if __name__ == "__main__":
    main()
