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
                    "Id": "a99a41b8fa77d8c7ff1c432a7a21bc0c2afd8c13b94a9d9b9b19b66ae97920c1",
                    "Name": "pod_name",
                    "Created": "2024-05-28T20:41:09.946926613+03:00",
                    "CreateCommand": [
                        "podman",
                        "pod",
                        "create",
                        "--name",
                        "pod_name",
                        "--infra=True",
                        "--userns",
                        "auto",
                        "--security-opt",
                        "seccomp=unconfined",
                        "--security-opt",
                        "apparmor=unconfined",
                        "--hostname",
                        "mypod",
                        "--dns",
                        "1.1.1.2",
                        "--label",
                        "key=cval",
                        "--label",
                        "otherkey=kddkdk",
                        "--label",
                        "somekey=someval",
                        "--add-host",
                        "google:5.5.5.5",
                        "--volume",
                        "/tmp/test//:/data2"
                    ],
                    "ExitPolicy": "continue",
                    "State": "Created",
                    "Hostname": "mypod",
                    "Labels": {
                        "key": "cval",
                        "otherkey": "kddkdk",
                        "somekey": "someval"
                    },
                    "CreateCgroup": true,
                    "CgroupParent": "user.slice",
                    "CgroupPath": "user.slice/user-1000.slice/user@1000.service/user.slice/....slice",
                    "CreateInfra": true,
                    "InfraContainerID": "37f960e6c8accc6b5b41945b1dcf03a28d3a366f7f37049748f18b21c44f577e",
                    "InfraConfig": {
                        "PortBindings": {},
                        "HostNetwork": false,
                        "StaticIP": "",
                        "StaticMAC": "",
                        "NoManageResolvConf": false,
                        "DNSServer": [
                            "1.1.1.2"
                        ],
                        "DNSSearch": null,
                        "DNSOption": null,
                        "NoManageHosts": false,
                        "HostAdd": [
                            "google:5.5.5.5"
                        ],
                        "Networks": null,
                        "NetworkOptions": null,
                        "pid_ns": "private",
                        "userns": "host",
                        "uts_ns": "private"
                    },
                    "SharedNamespaces": [
                        "user",
                        "uts",
                        "ipc",
                        "net"
                    ],
                    "NumContainers": 1,
                    "Containers": [
                        {
                            "Id": "37f960e6c8accc6b5b41945b1dcf03a28d3a366f7f37049748f18b21c44f577e",
                            "Name": "a99a49b8fa77-infra",
                            "State": "created"
                        }
                    ],
                    "mounts": [
                        {
                            "Type": "bind",
                            "Source": "/tmp/test",
                            "Destination": "/data2",
                            "Driver": "",
                            "Mode": "",
                            "Options": [
                                    "nosuid",
                                    "nodev",
                                    "rbind"
                            ],
                            "RW": true,
                            "Propagation": "rprivate"
                        }
                    ],
                    "security_opt": [
                        "seccomp=unconfined",
                        "apparmor=unconfined"
                    ],
                    "LockNumber": 1
                }
            ]
"""

import json
from ansible.module_utils.basic import AnsibleModule


def get_pod_info(module, executable, name):
    command = [executable, "pod", "inspect"]
    pods = [name]
    result = []
    errs = []
    rcs = []
    if not name:
        all_names = [executable, "pod", "ls", "-q"]
        rc, out, err = module.run_command(all_names)
        if rc != 0:
            module.fail_json(msg="Unable to get list of pods: %s" % err)
        name = out.split()
        if not name:
            return [], [err], [rc]
        pods = name
    for pod in pods:
        rc, out, err = module.run_command(command + [pod])
        errs.append(err.strip())
        rcs += [rc]
        data = json.loads(out) if out else None
        if isinstance(data, list) and data:
            data = data[0]
        if not out or data is None or not data:
            continue
        result.append(data)
    return result, errs, rcs


def main():
    module = AnsibleModule(
        argument_spec=dict(executable=dict(type="str", default="podman"), name=dict(type="str")),
        supports_check_mode=True,
    )

    name = module.params["name"]
    executable = module.get_bin_path(module.params["executable"], required=True)

    inspect_results, errs, rcs = get_pod_info(module, executable, name)

    if len(rcs) > 1 and 0 not in rcs:
        module.fail_json(msg="Failed to inspect pods", stderr="\n".join(errs))

    results = {
        "changed": False,
        "pods": inspect_results,
        "stderr": "\n".join(errs),
    }

    module.exit_json(**results)


if __name__ == "__main__":
    main()
