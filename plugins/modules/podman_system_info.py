#!/usr/bin/python
# Copyright (c) 2025 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
module: podman_system_info
author:
  - Johnson Lien (@johnsonlien)
short_description: Get podman system information from host machine
description: Runs "podman system info" on host machine
requirements:
  - "Podman installed on host"
options:
  executable:
    description:
      - Path to C(podman) executable if it is not in the C($PATH) on the
        machine running C(podman)
    default: 'podman'
    type: str
"""

EXAMPLES = r"""
- name: Get Podman system information
  containers.podman.podman_system_info:

- name: Get Podman system information into a variable
  containers.podman.podman_system_info:
  register: podman_info
- name: Printing Podman System info
  debug:
    msg: "{{ podman_info['podman_system_info'] }}"
"""

RETURN = r"""
podman_system_info:
    description: System information from podman
    returned: always
    type: dict
    sample:
        {
            "host": {
                "arch": "amd64",
                "buildahVersion": "1.40.1",
                "cgroupManager": "systemd",
                "cgroupVersion": "v2",
                "cgroupControllers": [
                "cpu",
                "io",
                "memory",
                "pids"
                ],
                "conmon": {
                "package": "conmon-2.1.13-1.fc41.x86_64",
                "path": "/usr/bin/conmon",
                "version": "conmon version 2.1.13, commit "
                },
                "cpus": 12,
                "cpuUtilization": {
                "userPercent": 5.73,
                "systemPercent": 2.15,
                "idlePercent": 92.12
                },
                "databaseBackend": "boltdb",
                "distribution": {
                "distribution": "fedora",
                "variant": "workstation",
                "version": "41"
                },
                "eventLogger": "journald",
                "freeLocks": 897,
                "hostname": "user.remote",
                "idMappings": {
                "gidmap": [
                    {
                    "container_id": 0,
                    "host_id": 1000,
                    "size": 1
                    },
                    {
                    "container_id": 1,
                    "host_id": 100000,
                    "size": 65536
                    }
                ],
                "uidmap": [
                    {
                    "container_id": 0,
                    "host_id": 1000,
                    "size": 1
                    },
                    {
                    "container_id": 1,
                    "host_id": 100000,
                    "size": 65536
                    }
                ]
                },
                "kernel": "6.14.9-200.fc41.x86_64",
                "logDriver": "journald",
                "memFree": 3055095808,
                "memTotal": 67157032960,
                "networkBackend": "netavark",
                "networkBackendInfo": {
                "backend": "netavark",
                "version": "netavark 1.15.2",
                "package": "netavark-1.15.2-1.fc41.x86_64",
                "path": "/usr/libexec/podman/netavark",
                "dns": {
                    "version": "aardvark-dns 1.15.0",
                    "package": "aardvark-dns-1.15.0-1.fc41.x86_64",
                    "path": "/usr/libexec/podman/aardvark-dns"
                }
                },
                "ociRuntime": {
                "name": "crun",
                "package": "crun-1.21-1.fc41.x86_64",
                "path": "/usr/bin/crun",
                "version": "crun version 1.21..."
                },
                "os": "linux",
                "remoteSocket": {
                "path": "/run/user/1000/podman/podman.sock",
                "exists": true
                },
                "rootlessNetworkCmd": "pasta",
                "serviceIsRemote": false,
                "security": {
                "apparmorEnabled": false,
                "capabilities": "CAP_CHOWN,CAP_DAC_OVERRIDE,CAP_FOWNER,CAP_FSETID,CAP_KILL,...",
                "rootless": true,
                "seccompEnabled": true,
                "seccompProfilePath": "/usr/share/containers/seccomp.json",
                "selinuxEnabled": true
                },
                "slirp4netns": {
                "executable": "/usr/bin/slirp4netns",
                "package": "slirp4netns-1.3.1-1.fc41.x86_64",
                "version": "slirp4netns version 1.3.1\ncommit..."
                },
                "pasta": {
                "executable": "/usr/bin/pasta",
                "package": "passt-0^20250611.g0293c6f-1.fc41.x86_64",
                "version": "pasta 0^20250611.g0293c6f-1.fc41.x86_64\nCopyright Red Hat\n..."
                },
                "swapFree": 1911504896,
                "swapTotal": 8589930496,
                "uptime": "115h 11m 51.00s (Approximately 3.88 days)",
                "variant": "",
                "linkmode": "dynamic"
            },
            "store": {
                "configFile": "/home/user/.config/containers/storage.conf",
                "containerStore": {
                "number": 6,
                "paused": 0,
                "running": 1,
                "stopped": 5
                },
                "graphDriverName": "overlay",
                "graphOptions": {
                "overlay.mountopt": "nodev"
                },
                "graphRoot": "/home/user/.local/share/containers/storage",
                "graphRootAllocated": 502921060352,
                "graphRootUsed": 457285541888,
                "graphStatus": {
                "Backing Filesystem": "extfs",
                "Native Overlay Diff": "false",
                "Supports d_type": "true",
                "Supports shifting": "true",
                "Supports volatile": "true",
                "Using metacopy": "false"
                },
                "imageCopyTmpDir": "/var/tmp",
                "imageStore": {
                "number": 859
                },
                "runRoot": "/run/user/1000/containers",
                "volumePath": "/storage/containers/storage/volumes",
                "transientStore": false
            },
            "registries": {
                "search": [
            "registry.fedoraproject.org",
            "registry.access.redhat.com",
            "docker.io"
            ]
            },
            "plugins": {
                "volume": [
                "local"
                ],
                "network": [
                "bridge",
                "macvlan",
                "ipvlan"
                ],
                "log": [
                "k8s-file",
                "none",
                "passthrough",
                "journald"
                ],
                "authorization": null
            },
            "version": {
                "APIVersion": "5.5.1",
                "Version": "5.5.1",
                "GoVersion": "go1.23.9",
                "GitCommit": "850db76dd78a0641eddb9ee19ee6f60d2c59bcfa",
                "BuiltTime": "Thu Jun  5 03:00:00 2025",
                "Built": 1749081600,
                "BuildOrigin": "Fedora Project",
                "OsArch": "linux/amd64",
                "Os": "linux"
            }
        }
"""

import json

from ansible.module_utils.basic import AnsibleModule


def get_podman_system_info(module, executable):
    command = [executable, "system", "info", "--format", "json"]
    rc, out, err = module.run_command(command)
    out = out.strip()
    if out:
        try:
            return json.loads(out)
        except Exception as e:
            module.fail_json(
                msg="Failed to parse podman system info output: error: %s, output: %s err: %s" % (e, out, err),
                exception=str(e),
            )


def main():
    module = AnsibleModule(
        argument_spec=dict(
            executable=dict(type="str", default="podman"),
        ),
        supports_check_mode=True,
    )

    executable = module.get_bin_path(module.params["executable"], required=True)

    results = get_podman_system_info(module, executable)

    results = dict(
        changed=False,
        podman_system_info=results,
    )

    module.exit_json(**results)


if __name__ == "__main__":
    main()
