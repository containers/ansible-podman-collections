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
host:
  arch: amd64
  buildahVersion: 1.23.0
  cgroupControllers: []
  cgroupManager: systemd
  cgroupVersion: v2
  conmon:
    package: conmon-2.0.29-2.fc34.x86_64
    path: /usr/bin/conmon
    version: 'conmon version 2.0.29, commit: '
 cpu_utilization:
   idle_percent: 96.84
   system_percent: 0.71
   user_percent: 2.45
  cpus: 8
  distribution:
    distribution: fedora
    variant: workstation
    version: "34"
  eventLogger: journald
  hostname: localhost.localdomain
  idMappings:
    gidmap:
    - container_id: 0
      host_id: 3267
      size: 1
    - container_id: 1
      host_id: 100000
      size: 65536
    uidmap:
    - container_id: 0
      host_id: 3267
      size: 1
    - container_id: 1
      host_id: 100000
      size: 65536
  kernel: 5.13.13-200.fc34.x86_64
  linkmode: dynamic
  logDriver: journald
  memFree: 1833385984
  memTotal: 16401895424
  networkBackend: cni
  networkBackendInfo:
    backend: cni
    dns:
      package: podman-plugins-3.4.4-1.fc34.x86_64
      path: /usr/libexec/cni/dnsname
      version: |-
        CNI dnsname plugin
        version: 1.3.1
        commit: unknown
    package: |-
      containernetworking-plugins-1.0.1-1.fc34.x86_64
      podman-plugins-3.4.4-1.fc34.x86_64
    path: /usr/libexec/cni
  ociRuntime:
    name: crun
    package: crun-1.0-1.fc34.x86_64
    path: /usr/bin/crun
    version: |-
      crun version 1.0
      commit: 139dc6971e2f1d931af520188763e984d6cdfbf8
      spec: 1.0.0
      +SYSTEMD +SELINUX +APPARMOR +CAP +SECCOMP +EBPF +CRIU +YAJL
  os: linux
  pasta:
    executable: /usr/bin/passt
    package: passt-0^20221116.gace074c-1.fc34.x86_64
    version: |
      passt 0^20221116.gace074c-1.fc34.x86_64
      Copyright Red Hat
      GNU Affero GPL version 3 or later <https://www.gnu.org/licenses/agpl-3.0.html>
      This is free software: you are free to change and redistribute it.
      There is NO WARRANTY, to the extent permitted by law.
  remoteSocket:
    path: /run/user/3267/podman/podman.sock
  security:
    apparmorEnabled: false
    capabilities: CAP_CHOWN,CAP_DAC_OVERRIDE,CAP_FOWNER,CAP_FSETID,CAP_KILL,CAP_NET_BIND_SERVICE,CAP_SETFCAP,CAP_SETGID,CAP_SETPCAP,CAP_SETUID
    rootless: true
    seccompEnabled: true
    seccompProfilePath: /usr/share/containers/seccomp.json
    selinuxEnabled: true
  serviceIsRemote: false
  slirp4netns:
    executable: /bin/slirp4netns
    package: slirp4netns-1.1.12-2.fc34.x86_64
    version: |-
      slirp4netns version 1.1.12
      commit: 7a104a101aa3278a2152351a082a6df71f57c9a3
      libslirp: 4.4.0
      SLIRP_CONFIG_VERSION_MAX: 3
      libseccomp: 2.5.0
  swapFree: 15687475200
  swapTotal: 16886259712
  uptime: 47h 15m 9.91s (Approximately 1.96 days)
plugins:
  log:
  - k8s-file
  - none
  - journald
  network:
  - bridge
  - macvlan
  volume:
  - local
registries:
  search:
  - registry.fedoraproject.org
  - registry.access.redhat.com
  - docker.io
  - quay.io
store:
  configFile: /home/dwalsh/.config/containers/storage.conf
  containerStore:
    number: 9
    paused: 0
    running: 1
    stopped: 8
  graphDriverName: overlay
  graphOptions: {}
  graphRoot: /home/dwalsh/.local/share/containers/storage
  graphRootAllocated: 510389125120
  graphRootUsed: 129170714624
  graphStatus:
    Backing Filesystem: extfs
    Native Overlay Diff: "true"
    Supports d_type: "true"
    Using metacopy: "false"
  imageCopyTmpDir: /home/dwalsh/.local/share/containers/storage/tmp
  imageStore:
    number: 5
  runRoot: /run/user/3267/containers
  transientStore: false
  volumePath: /home/dwalsh/.local/share/containers/storage/volumes
version:
  APIVersion: 4.0.0
  Built: 1631648722
  BuiltTime: Tue Sep 14 15:45:22 2021
  GitCommit: 23677f92dd83e96d2bc8f0acb611865fb8b1a56d
  GoVersion: go1.16.6
  OsArch: linux/amd64
  Version: 4.0.0
}
'''

import json

from ansible.module_utils.basic import AnsibleModule

def get_podman_system_info(module, executable):
    command = [executable, 'system', 'info']
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
