#!/usr/bin/python
# Copyright (c) 2020 Red Hat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r"""
module: podman_container
author:
  - "Sagi Shnaidman (@sshnaidm)"
version_added: '1.0.0'
short_description: Manage podman containers
notes: []
description:
  - Start, stop, restart and manage Podman containers
requirements:
  - "Podman installed on host"

extends_documentation_fragment:
- containers.podman.podman_containers_doc
"""


EXAMPLES = r"""
- name: Run container
  containers.podman.podman_container:
    name: container
    image: quay.io/bitnami/wildfly
    state: started

- name: Create a data container
  containers.podman.podman_container:
    name: mydata
    image: busybox
    volume:
      - /tmp/data

- name: Re-create a redis container
  containers.podman.podman_container:
    name: myredis
    image: redis
    command: redis-server --appendonly yes
    state: present
    recreate: yes
    expose:
      - 6379
    volumes_from:
      - mydata

- name: Restart a container
  containers.podman.podman_container:
    name: myapplication
    image: redis
    state: started
    restart: yes
    etc_hosts:
        other: "127.0.0.1"
    restart_policy: "no"
    device: "/dev/sda:/dev/xvda:rwm"
    ports:
        - "8080:9000"
        - "127.0.0.1:8081:9001/udp"
    env:
        SECRET_KEY: "ssssh"
        BOOLEAN_KEY: "yes"

- name: Container present
  containers.podman.podman_container:
    name: mycontainer
    state: present
    image: ubuntu:14.04
    command: "sleep 1d"

- name: Stop a container
  containers.podman.podman_container:
    name: mycontainer
    state: stopped

- name: Start 4 load-balanced containers
  containers.podman.podman_container:
    name: "container{{ item }}"
    recreate: yes
    image: someuser/anotherappimage
    command: sleep 1d
  with_sequence: count=4

- name: remove container
  containers.podman.podman_container:
    name: ohno
    state: absent

- name: Writing output
  containers.podman.podman_container:
    name: myservice
    image: busybox
    log_options: path=/var/log/container/mycontainer.json
    log_driver: k8s-file
"""

RETURN = r"""
container:
    description:
      - Facts representing the current state of the container. Matches the
        podman inspection output.
      - Note that facts are part of the registered vars since Ansible 2.8. For
        compatibility reasons, the facts
        are also accessible directly as C(podman_container). Note that the
        returned fact will be removed in Ansible 2.12.
      - Empty if C(state) is I(absent).
    returned: always
    type: dict
    sample: '{
        "AppArmorProfile": "",
        "Args": [
            "sh"
        ],
        "BoundingCaps": [
            "CAP_CHOWN",
            ...
        ],
        "Config": {
            "Annotations": {
                "io.kubernetes.cri-o.ContainerType": "sandbox",
                "io.kubernetes.cri-o.TTY": "false"
            },
            "AttachStderr": false,
            "AttachStdin": false,
            "AttachStdout": false,
            "Cmd": [
                "sh"
            ],
            "Domainname": "",
            "Entrypoint": "",
            "Env": [
                "PATH=/usr/sbin:/usr/bin:/sbin:/bin",
                "TERM=xterm",
                "HOSTNAME=",
                "container=podman"
            ],
            "Hostname": "",
            "Image": "docker.io/library/busybox:latest",
            "Labels": null,
            "OpenStdin": false,
            "StdinOnce": false,
            "StopSignal": 15,
            "Tty": false,
            "User": {
                "gid": 0,
                "uid": 0
            },
            "Volumes": null,
            "WorkingDir": "/"
        },
        "ConmonPidFile": "...",
        "Created": "2019-06-17T19:13:09.873858307+03:00",
        "Dependencies": [],
        "Driver": "overlay",
        "EffectiveCaps": [
            "CAP_CHOWN",
            ...
        ],
        "ExecIDs": [],
        "ExitCommand": [
            "/usr/bin/podman",
            "--root",
            ...
        ],
        "GraphDriver": {
            ...
        },
        "HostConfig": {
            ...
        },
        "HostnamePath": "...",
        "HostsPath": "...",
        "ID": "...",
        "Image": "...",
        "ImageName": "docker.io/library/busybox:latest",
        "IsInfra": false,
        "LogPath": "/tmp/container/mycontainer.json",
        "MountLabel": "system_u:object_r:container_file_t:s0:c282,c782",
        "Mounts": [
            ...
        ],
        "Name": "myservice",
        "Namespace": "",
        "NetworkSettings": {
            "Bridge": "",
            ...
        },
        "Path": "sh",
        "ProcessLabel": "system_u:system_r:container_t:s0:c282,c782",
        "ResolvConfPath": "...",
        "RestartCount": 0,
        "Rootfs": "",
        "State": {
            "Dead": false,
            "Error": "",
            "ExitCode": 0,
            "FinishedAt": "2019-06-17T19:13:10.157518963+03:00",
            "Healthcheck": {
                "FailingStreak": 0,
                "Log": null,
                "Status": ""
            },
            "OOMKilled": false,
            "OciVersion": "1.0.1-dev",
            "Paused": false,
            "Pid": 4083,
            "Restarting": false,
            "Running": false,
            "StartedAt": "2019-06-17T19:13:10.152479729+03:00",
            "Status": "exited"
        },
        "StaticDir": "..."
            ...
    }'
"""
from ansible.module_utils.basic import AnsibleModule  # noqa: F402
from ..module_utils.podman.podman_container_lib import PodmanManager  # noqa: F402
from ..module_utils.podman.podman_container_lib import ARGUMENTS_SPEC_CONTAINER  # noqa: F402


def main():
    module = AnsibleModule(
        argument_spec=ARGUMENTS_SPEC_CONTAINER,
        mutually_exclusive=(
            ['no_hosts', 'etc_hosts'],
        ),
        supports_check_mode=True,
    )

    # work on input vars
    if module.params['state'] in ['started', 'present'] and \
            not module.params['image']:
        module.fail_json(msg="State '%s' required image to be configured!" %
                             module.params['state'])

    results = PodmanManager(module, module.params).execute()
    module.exit_json(**results)


if __name__ == '__main__':
    main()
