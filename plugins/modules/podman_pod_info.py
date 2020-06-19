#!/usr/bin/python
# Copyright (c) 2020 Red Hat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r"""
module: podman_pod_info
author:
  - "Sagi Shnaidman (@sshnaidm)"
version_added: '1.0.0'
short_description: Gather info about podman pods
notes: []
description:
  - Gather info about podman pods with podman inspect command.
requirements:
  - "Podman installed on host"
options:
  name:
    description:
      - Name of the pod
    type: str
  executable:
    description:
      - Path to C(podman) executable if it is not in the C($PATH) on the
        machine running C(podman)
    default: 'podman'
    type: str
"""

EXAMPLES = r"""
- name: Gather info about all present pods
  containers.podman.podman_pod_info:

- name: Gather info about specific pods
  containers.podman.podman_pod_info:
    name: special_pod
"""

RETURN = r"""
pods:
    description: Facts from all or specified pods
    returned: always
    type: list
    sample: [
                {
                    "Config": {
                        "id": "d9cb6dbb0....",
                        "name": "pod1",
                        "hostname": "pod1host",
                        "labels": {
                        },
                        "cgroupParent": "/libpod_parent",
                        "sharesCgroup": true,
                        "sharesIpc": true,
                        "sharesNet": true,
                        "sharesUts": true,
                        "infraConfig": {
                            "makeInfraContainer": true,
                            "infraPortBindings": [
                                    {
                                        "hostPort": 7777,
                                        "containerPort": 7111,
                                        "protocol": "tcp",
                                        "hostIP": ""
                                    }
                            ]
                        },
                    "created": "2020-07-13T20:29:12.572282186+03:00",
                        "lockID": 682
                    },
                    "State": {
                        "cgroupPath": "/libpod_parent/d9cb6dbb0....",
                        "infraContainerID": "ad46737bf....",
                        "status": "Created"
                    },
                    "Containers": [
                        {
                            "id": "ad46737bf....",
                            "state": "configured"
                        }
                    ]
                }
            ]
"""

import json
from ansible.module_utils.basic import AnsibleModule


def get_pod_info(module, executable, name):
    command = [executable, 'pod', 'inspect']
    pods = [name]
    result = []
    errs = []
    rcs = []
    if not name:
        all_names = [executable, 'pod', 'ls', '-q']
        rc, out, err = module.run_command(all_names)
        if rc != 0:
            module.fail_json(msg="Unable to get list of pods: %s" % err)
        name = out.split()
        if not name:
            return [], out, err
        pods = name
    for pod in pods:
        rc, out, err = module.run_command(command + [pod])
        errs.append(err.strip())
        rcs += [rc]
        if not out or json.loads(out) is None:
            continue
        result.append(json.loads(out))
    return result, errs, rcs


def main():
    module = AnsibleModule(
        argument_spec=dict(
            executable=dict(type='str', default='podman'),
            name=dict(type='str')
        ),
        supports_check_mode=True,
    )

    name = module.params['name']
    executable = module.get_bin_path(module.params['executable'], required=True)

    inspect_results, errs, rcs = get_pod_info(module, executable, name)

    if len(rcs) > 1 and 0 not in rcs:
        module.fail_json(msg="Failed to inspect pods", stderr="\n".join(errs))

    results = {
        "changed": False,
        "pods": inspect_results,
        "stderr": "\n".join(errs),
    }

    module.exit_json(**results)


if __name__ == '__main__':
    main()
