#!/usr/bin/python
# Copyright (c) 2020 Red Hat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
module: podman_container_info
author:
    - Sagi Shnaidman (@podman)
    - Emilien Macchi (@EmilienM)
short_description: Gather facts about containers using podman
notes:
    - Podman may require elevated privileges in order to run properly.
description:
    - Gather facts about containers using C(podman)
requirements:
    - "Podman installed on host"
options:
  name:
    description:
      - List of container names to gather facts about. If no name is given
        return facts about all containers.
    type: list
    elements: str
  executable:
    description:
      - Path to C(podman) executable if it is not in the C($PATH) on the
        machine running C(podman)
    default: 'podman'
    type: str
"""

EXAMPLES = r"""
- name: Gather facts for all containers
  containers.podman.podman_container_info:

- name: Gather facts on a specific container
  containers.podman.podman_container_info:
    name: web1

- name: Gather facts on several containers
  containers.podman.podman_container_info:
    name:
      - redis
      - web1
"""

RETURN = r"""
containers:
    description: Facts from all or specified containers
    returned: always
    type: list
    elements: dict
    sample: [
                {
                    "Id": "d38a8fcd61ab7e0754355e8fb3acc201e07770f3d1fd8fed36556941ac458ce",
                    "Created": "2024-08-14T00:04:33.127266655+03:00",
                    "Path": "/entrypoint.sh",
                    "Args": [
                        "/entrypoint.sh"
                    ],
                    "State": {
                        "OciVersion": "1.1.0+dev",
                        "Status": "running",
                        "Running": true,
                        "Paused": false,
                        "Restarting": false,
                        "OOMKilled": false,
                        "Dead": false,
                        "Pid": 2434164,
                        "ConmonPid": 2434162,
                        "ExitCode": 0,
                        "Error": "",
                        "StartedAt": "2024-08-14T00:04:33.237286439+03:00",
                        "FinishedAt": "0001-01-01T00:00:00Z",
                        "Health": {
                                "Status": "",
                                "FailingStreak": 0,
                                "Log": null
                        },
                        "CgroupPath": "/user.slice/user-1000.slice/user@1000.service/user.slice/libpod-d38a....scope",
                        "CheckpointedAt": "0001-01-01T00:00:00Z",
                        "RestoredAt": "0001-01-01T00:00:00Z"
                    },
                    "Image": "fe2ba3a8ede60e5938e666b483c3a812ba902dac2303341930fbadc0482592b7",
                    "ImageDigest": "sha256:1222865ed7489298ee28414ddedb63a0c6405938c3a38adf21c8656d7f532271",
                    "ImageName": "registry/org/image:latest",
                    "Rootfs": "",
                    "Pod": "",
                    "ResolvConfPath": "/run/user/1000/containers/overlay-containers/d38a.../userdata/resolv.conf",
                    "HostnamePath": "/run/user/1000/containers/overlay-containers/d38a.../userdata/hostname",
                    "HostsPath": "/run/user/1000/containers/overlay-containers/d38a.../userdata/hosts",
                    "StaticDir": "/home/podman/.local/share/containers/storage/overlay-containers/d38a.../userdata",
                    "OCIConfigPath": "/home/podman/.local/share/containers/....json",
                    "OCIRuntime": "crun",
                    "ConmonPidFile": "/run/user/1000/containers/overlay-containers/d38a.../userdata/conmon.pid",
                    "PidFile": "/run/user/1000/containers/overlay-containers/d38a.../userdata/pidfile",
                    "Name": "costapp",
                    "RestartCount": 0,
                    "Driver": "overlay",
                    "MountLabel": "system_u:object_r:container_file_t:s0:c493,c986",
                    "ProcessLabel": "system_u:system_r:container_t:s0:c493,c986",
                    "AppArmorProfile": "",
                    "EffectiveCaps": [
                        "CAP_CHOWN",
                        "CAP_DAC_OVERRIDE",
                        "CAP_FOWNER",
                        "CAP_FSETID",
                        "CAP_KILL",
                        "CAP_NET_BIND_SERVICE",
                        "CAP_SETFCAP",
                        "CAP_SETGID",
                        "CAP_SETPCAP",
                        "CAP_SETUID",
                        "CAP_SYS_CHROOT"
                    ],
                    "BoundingCaps": [
                        "CAP_CHOWN",
                        "CAP_DAC_OVERRIDE",
                        "CAP_FOWNER",
                        "CAP_FSETID",
                        "CAP_KILL",
                        "CAP_NET_BIND_SERVICE",
                        "CAP_SETFCAP",
                        "CAP_SETGID",
                        "CAP_SETPCAP",
                        "CAP_SETUID",
                        "CAP_SYS_CHROOT"
                    ],
                    "ExecIDs": [],
                    "GraphDriver": {
                        "Name": "overlay",
                        "Data": {
                                "LowerDir": "/home/podman/.local/share/containers/storage/overlay/29e2.../diff:...",
                                "MergedDir": "/home/podman/.local/share/containers/storage/overlay/865909.../merged",
                                "UpperDir": "/home/podman/.local/share/containers/storage/overlay/865909.../diff",
                                "WorkDir": "/home/podman/.local/share/containers/storage/overlay/865909.../work"
                        }
                    },
                    "Mounts": [],
                    "Dependencies": [],
                    "NetworkSettings": {
                        "EndpointID": "",
                        "Gateway": "",
                        "IPAddress": "",
                        "IPPrefixLen": 0,
                        "IPv6Gateway": "",
                        "GlobalIPv6Address": "",
                        "GlobalIPv6PrefixLen": 0,
                        "MacAddress": "",
                        "Bridge": "",
                        "SandboxID": "",
                        "HairpinMode": false,
                        "LinkLocalIPv6Address": "",
                        "LinkLocalIPv6PrefixLen": 0,
                        "Ports": {
                                "80/tcp": [
                                    {
                                        "HostIp": "",
                                        "HostPort": "8888"
                                    }
                                ]
                        },
                        "SandboxKey": "/run/user/1000/netns/netns-2343321-795a-8289-14c0-77ee2556ebf1"
                    },
                    "Namespace": "",
                    "IsInfra": false,
                    "IsService": false,
                    "KubeExitCodePropagation": "invalid",
                    "lockNumber": 1417,
                    "Config": {
                        "Hostname": "444a8274863a",
                        "Domainname": "",
                        "User": "",
                        "AttachStdin": false,
                        "AttachStdout": false,
                        "AttachStderr": false,
                        "Tty": false,
                        "OpenStdin": false,
                        "StdinOnce": false,
                        "Env": [
                                "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
                                "container=podman",
                                "HOME=/root",
                                "HOSTNAME=444a8274863a"
                        ],
                        "Cmd": null,
                        "Image": "registry/org/image:latest",
                        "Volumes": null,
                        "WorkingDir": "/",
                        "Entrypoint": "/entrypoint.sh",
                        "OnBuild": null,
                        "Labels": {
                                "io.buildah.version": "1.31.2"
                        },
                        "Annotations": {
                                "io.container.manager": "libpod",
                                "org.opencontainers.image.stopSignal": "15"
                        },
                        "StopSignal": 15,
                        "HealthcheckOnFailureAction": "none",
                        "CreateCommand": [
                                "podman",
                                "run",
                                "-d",
                                "--name",
                                "test",
                                "-p",
                                "8888:80",
                                "registry/org/image:latest"
                        ],
                        "Umask": "0022",
                        "Timeout": 0,
                        "StopTimeout": 10,
                        "Passwd": true,
                        "sdNotifyMode": "container"
                    },
                    "HostConfig": {
                        "Binds": [],
                        "CgroupManager": "systemd",
                        "CgroupMode": "private",
                        "ContainerIDFile": "",
                        "LogConfig": {
                                "Type": "journald",
                                "Config": null,
                                "Path": "",
                                "Tag": "",
                                "Size": "0B"
                        },
                        "NetworkMode": "slirp4netns",
                        "PortBindings": {
                                "80/tcp": [
                                    {
                                        "HostIp": "",
                                        "HostPort": "8888"
                                    }
                                ]
                        },
                        "RestartPolicy": {
                                "Name": "",
                                "MaximumRetryCount": 0
                        },
                        "AutoRemove": false,
                        "VolumeDriver": "",
                        "VolumesFrom": null,
                        "CapAdd": [],
                        "CapDrop": [],
                        "Dns": [],
                        "DnsOptions": [],
                        "DnsSearch": [],
                        "ExtraHosts": [],
                        "GroupAdd": [],
                        "IpcMode": "shareable",
                        "Cgroup": "",
                        "Cgroups": "default",
                        "Links": null,
                        "OomScoreAdj": 0,
                        "PidMode": "private",
                        "Privileged": false,
                        "PublishAllPorts": false,
                        "ReadonlyRootfs": false,
                        "SecurityOpt": [],
                        "Tmpfs": {},
                        "UTSMode": "private",
                        "UsernsMode": "",
                        "ShmSize": 65536000,
                        "Runtime": "oci",
                        "ConsoleSize": [
                                0,
                                0
                        ],
                        "Isolation": "",
                        "CpuShares": 0,
                        "Memory": 0,
                        "NanoCpus": 0,
                        "CgroupParent": "user.slice",
                        "BlkioWeight": 0,
                        "BlkioWeightDevice": null,
                        "BlkioDeviceReadBps": null,
                        "BlkioDeviceWriteBps": null,
                        "BlkioDeviceReadIOps": null,
                        "BlkioDeviceWriteIOps": null,
                        "CpuPeriod": 0,
                        "CpuQuota": 0,
                        "CpuRealtimePeriod": 0,
                        "CpuRealtimeRuntime": 0,
                        "CpusetCpus": "",
                        "CpusetMems": "",
                        "Devices": [],
                        "DiskQuota": 0,
                        "KernelMemory": 0,
                        "MemoryReservation": 0,
                        "MemorySwap": 0,
                        "MemorySwappiness": 0,
                        "OomKillDisable": false,
                        "PidsLimit": 2048,
                        "Ulimits": [
                                {
                                    "Name": "RLIMIT_NOFILE",
                                    "Soft": 524288,
                                    "Hard": 524288
                                },
                                {
                                    "Name": "RLIMIT_NPROC",
                                    "Soft": 256018,
                                    "Hard": 256018
                                }
                        ],
                        "CpuCount": 0,
                        "CpuPercent": 0,
                        "IOMaximumIOps": 0,
                        "IOMaximumBandwidth": 0,
                        "CgroupConf": null,
                    }
                }
            ]
"""

import json
import time
from ansible.module_utils.basic import AnsibleModule


def get_containers_facts(module, executable, name):
    """Collect containers facts for all containers or for specified in 'name'.

    Arguments:
        module {AnsibleModule} -- instance of AnsibleModule
        executable {string} -- binary to execute when inspecting containers
        name {list} -- list of names or None in case of all containers

    Returns:
        list of containers info, stdout, stderr
    """
    retry = 0
    retry_limit = 4
    if not name:
        all_names = [executable, "container", "ls", "-q", "-a"]
        rc, out, err = module.run_command(all_names)
        # This should not fail in regular circumstances, so retry again
        # https://github.com/containers/podman/issues/10225
        while rc != 0 and retry <= retry_limit:
            module.log(msg="Unable to get list of containers: %s" % err)
            time.sleep(1)
            retry += 1
            rc, out, err = module.run_command(all_names)
        if rc != 0:
            module.fail_json(msg="Unable to get list of containers during" " %s retries" % retry_limit)
        name = out.split()
        if not name:
            return [], out, err
    command = [executable, "container", "inspect"]
    command.extend(name)
    rc, out, err = module.run_command(command)
    if rc == 0:
        json_out = json.loads(out) if out else None
        if json_out is None:
            return [], out, err
        return json_out, out, err
    if rc != 0 and "no such " in err:
        if len(name) < 2:
            return [], out, err
        return cycle_over(module, executable, name)
    module.fail_json(msg="Unable to gather info for %s: %s" % (",".join(name), err))


def cycle_over(module, executable, name):
    """Inspect each container in a cycle in case some of them don't exist.

    Arguments:
        module {AnsibleModule} -- instance of AnsibleModule
        executable {string} -- binary to execute when inspecting containers
        name {list} -- list of containers names to inspect

    Returns:
        list of containers info, stdout as empty, stderr
    """
    inspection = []
    stderrs = []
    for container in name:
        command = [executable, "container", "inspect", container]
        rc, out, err = module.run_command(command)
        if rc != 0 and "no such " not in err:
            module.fail_json(msg="Unable to gather info for %s: %s" % (container, err))
        if rc == 0 and out:
            json_out = json.loads(out)
            if json_out:
                inspection += json_out
        stderrs.append(err)
    return inspection, "", "\n".join(stderrs)


def main():
    module = AnsibleModule(
        argument_spec={
            "executable": {"type": "str", "default": "podman"},
            "name": {"type": "list", "elements": "str"},
        },
        supports_check_mode=True,
    )

    name = module.params["name"]
    executable = module.get_bin_path(module.params["executable"], required=True)
    # pylint: disable=unused-variable
    inspect_results, out, err = get_containers_facts(module, executable, name)

    results = {"changed": False, "containers": inspect_results, "stderr": err}

    module.exit_json(**results)


if __name__ == "__main__":
    main()
