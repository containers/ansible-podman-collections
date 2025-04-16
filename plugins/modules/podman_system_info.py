#!/usr/bin/python
# Copyright (c) 2025 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
module: podman_system_info
author:
  - Johnson Lien (@johnsonlien)
short_description: Get podman system information from host machine
description: Runs "podman system info --format json" on host machine
'''

EXAMPLES = r'''
- name: Get Podman system information
  containers.podman.podman_system_info:

- name: Get Podman system information into a variable
  containers.podman.podman_system_info:
  register: podman_info
- name: Printing Podman System info
  debug:
    msg: "{{ podman_info['podman_system_info'] }}
'''

RETURN = r'''
{
  "host": {
    "arch": "amd64",
    "buildahVersion": "1.23.0",
    "cgroupManager": "systemd",
    "cgroupVersion": "v2",
    "cgroupControllers": [],
    "conmon": {
      "package": "conmon-2.0.29-2.fc34.x86_64",
      "path": "/usr/bin/conmon",
      "version": "conmon version 2.0.29, commit: "
    },
    "cpus": 8,
    "distribution": {
      "distribution": "fedora",
      "version": "34"
    },
    "eventLogger": "journald",
    "hostname": "localhost.localdomain",
    "idMappings": {
      "gidmap": [
	{
	  "container_id": 0,
	  "host_id": 3267,
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
	  "host_id": 3267,
	  "size": 1
	},
	{
	  "container_id": 1,
	  "host_id": 100000,
	  "size": 65536
	}
      ]
    },
    "kernel": "5.13.13-200.fc34.x86_64",
    "logDriver": "journald",
    "memFree": 1785753600,
    "memTotal": 16401895424,
    "networkBackend": "cni",
    "networkBackendInfo": {
      "backend": "cni",
      "package": "containernetworking-plugins-1.0.1-1.fc34.x86_64\npodman-plugins-3.4.4-1.fc34.x86_64",
      "path": "/usr/libexec/cni",
      "dns": {
        "version": "CNI dnsname plugin\nversion: 1.3.1\ncommit: unknown",
        "package": "podman-plugins-3.4.4-1.fc34.x86_64",
        "path": "/usr/libexec/cni/dnsname"
      }
    },
    "ociRuntime": {
      "name": "crun",
      "package": "crun-1.0-1.fc34.x86_64",
      "path": "/usr/bin/crun",
      "version": "crun version 1.0\ncommit: 139dc6971e2f1d931af520188763e984d6cdfbf8\nspec: 1.0.0\n+SYSTEMD +SELINUX +APPARMOR +CAP +SECCOMP +EBPF +CRIU +YAJL"
    },
    "os": "linux",
    "remoteSocket": {
      "path": "/run/user/3267/podman/podman.sock"
    },
    "serviceIsRemote": false,
    "security": {
      "apparmorEnabled": false,
      "capabilities": "CAP_CHOWN,CAP_DAC_OVERRIDE,CAP_FOWNER,CAP_FSETID,CAP_KILL,CAP_NET_BIND_SERVICE,CAP_SETFCAP,CAP_SETGID,CAP_SETPCAP,CAP_SETUID",
      "rootless": true,
      "seccompEnabled": true,
      "seccompProfilePath": "/usr/share/containers/seccomp.json",
      "selinuxEnabled": true
    },
    "slirp4netns": {
      "executable": "/bin/slirp4netns",
      "package": "slirp4netns-1.1.12-2.fc34.x86_64",
      "version": "slirp4netns version 1.1.12\ncommit: 7a104a101aa3278a2152351a082a6df71f57c9a3\nlibslirp: 4.4.0\nSLIRP_CONFIG_VERSION_MAX: 3\nlibseccomp: 2.5.0"
    },
    "pasta": {
      "executable": "/usr/bin/passt",
      "package": "passt-0^20221116.gace074c-1.fc34.x86_64",
      "version": "passt 0^20221116.gace074c-1.fc34.x86_64\nCopyright Red Hat\nGNU Affero GPL version 3 or later \u003chttps://www.gnu.org/licenses/agpl-3.0.html\u003e\nThis is free software: you are free to change and redistribute it.\nThere is NO WARRANTY, to the extent permitted by law.\n"
    },
    "swapFree": 15687475200,
    "swapTotal": 16886259712,
    "uptime": "47h 17m 29.75s (Approximately 1.96 days)",
    "linkmode": "dynamic"
  },
  "store": {
    "configFile": "/home/dwalsh/.config/containers/storage.conf",
    "containerStore": {
      "number": 9,
      "paused": 0,
      "running": 1,
      "stopped": 8
    },
    "graphDriverName": "overlay",
    "graphOptions": {

    },
    "graphRoot": "/home/dwalsh/.local/share/containers/storage",
    "graphStatus": {
      "Backing Filesystem": "extfs",
      "Native Overlay Diff": "true",
      "Supports d_type": "true",
      "Using metacopy": "false"
    },
    "imageCopyTmpDir": "/home/dwalsh/.local/share/containers/storage/tmp",
    "imageStore": {
      "number": 5
    },
    "runRoot": "/run/user/3267/containers",
    "volumePath": "/home/dwalsh/.local/share/containers/storage/volumes",
    "transientStore": false
  },
  "registries": {
    "search": [
  "registry.fedoraproject.org",
  "registry.access.redhat.com",
  "docker.io",
  "quay.io"
]
  },
  "plugins": {
    "volume": [
      "local"
    ],
    "network": [
      "bridge",
      "macvlan"
    ],
    "log": [
      "k8s-file",
      "none",
      "journald"
    ]
  },
  "version": {
    "APIVersion": "4.0.0",
    "Version": "4.0.0",
    "GoVersion": "go1.16.6",
    "GitCommit": "23677f92dd83e96d2bc8f0acb611865fb8b1a56d",
    "BuiltTime": "Tue Sep 14 15:45:22 2021",
    "Built": 1631648722,
    "OsArch": "linux/amd64"
  }
}
'''

import json

from ansible.module_utils.basic import AnsibleModule

def get_podman_system_info(module, executable):
    command = [executable, 'system', 'info', '--format', 'json']
    rc, out, err = module.run_command(command)
    out = out.strip()
    if out:
        return json.loads(out)

    module.log(msg="Unable to get podman system info: %s" % err)
    return json.dumps([])

def main():
    module = AnsibleModule(
        argument_spec=dict(
            executable=dict(type='str', default='podman'),
        ),
        supports_check_mode=True,
    )

    executable = module.get_bin_path(module.params['executable'], required=True)

    results = get_podman_system_info(module, executable)

    results = dict(
        changed=False,
        podman_system_info=results,
    )

    module.exit_json(**results)

if __name__ == '__main__':
    main()
