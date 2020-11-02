#!/usr/bin/python
# Copyright (c) 2020 Red Hat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# flake8: noqa: E501
from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = '''
---
module: podman_pod
short_description: Manage Podman pods
author:
  - "Sagi Shnaidman (@sshnaidm)"
version_added: '1.0.0'
description:
  - Manage podman pods.
options:
  state:
    description:
    - This variable is set for state
    type: str
    default: created
    choices:
      - created
      - killed
      - restarted
      - absent
      - started
      - stopped
      - paused
      - unpaused
  recreate:
    description:
      - Use with present and started states to force the re-creation of an
        existing pod.
    type: bool
    default: False
  add_host:
    description:
    - Add a host to the /etc/hosts file shared between all containers in the pod.
    type: list
    elements: str
    required: false
  cgroup_parent:
    description:
    - Path to cgroups under which the cgroup for the pod will be created. If the path
      is not absolute, he path is considered to be relative to the cgroups path of the
      init process. Cgroups will be created if they do not already exist.
    type: str
    required: false
  dns:
    description:
    - Set custom DNS servers in the /etc/resolv.conf file that will be shared between
      all containers in the pod. A special option, "none" is allowed which disables
      creation of /etc/resolv.conf for the pod.
    type: list
    elements: str
    required: false
  dns_opt:
    description:
    - Set custom DNS options in the /etc/resolv.conf file that will be shared between
      all containers in the pod.
    type: list
    elements: str
    required: false
  dns_search:
    description:
    - Set custom DNS search domains in the /etc/resolv.conf file that will be shared
      between all containers in the pod.
    type: list
    elements: str
    required: false
  hostname:
    description:
    - Set a hostname to the pod
    type: str
    required: false
  infra:
    description:
    - Create an infra container and associate it with the pod. An infra container is
      a lightweight container used to coordinate the shared kernel namespace of a pod.
      Default is true.
    type: bool
    required: false
  infra_conmon_pidfile:
    description:
    - Write the pid of the infra container's conmon process to a file. As conmon runs
      in a separate process than Podman, this is necessary when using systemd to manage
      Podman containers and pods.
    type: str
    required: false
  infra_command:
    description:
    - The command that will be run to start the infra container. Default is "/pause".
    type: str
    required: false
  infra_image:
    description:
    - The image that will be created for the infra container. Default is "k8s.gcr.io/pause:3.1".
    type: str
    required: false
  ip:
    description:
    - Set a static IP for the pod's shared network.
    type: str
    required: false
  label:
    description:
    - Add metadata to a pod, pass dictionary of label keys and values.
    type: dict
    required: false
  label_file:
    description:
    - Read in a line delimited file of labels.
    type: str
    required: false
  mac_address:
    description:
    - Set a static MAC address for the pod's shared network.
    type: str
    required: false
  name:
    description:
    - Assign a name to the pod.
    type: str
    required: true
  network:
    description:
    - Set network mode for the pod. Supported values are bridge (the default), host
      (do not create a network namespace, all containers in the pod will use the host's
      network), or a comma-separated list of the names of CNI networks the pod should
      join.
    type: str
    required: false
  no_hosts:
    description:
    - Disable creation of /etc/hosts for the pod.
    type: bool
    required: false
  pod_id_file:
    description:
    - Write the pod ID to the file.
    type: str
    required: false
  publish:
    description:
    - Publish a port or range of ports from the pod to the host.
    type: list
    elements: str
    required: false
    aliases:
      - ports
  share:
    description:
    - A comma delimited list of kernel namespaces to share. If none or "" is specified,
      no namespaces will be shared. The namespaces to choose from are ipc, net, pid,
      user, uts.
    type: str
    required: false
  executable:
    description:
      - Path to C(podman) executable if it is not in the C($PATH) on the
        machine running C(podman)
    default: 'podman'
    type: str
  debug:
    description:
      - Return additional information which can be helpful for investigations.
    type: bool
    default: False

requirements:
  - "podman"

'''

RETURN = '''
pod:
  description: Pod inspection results for the given pod
    built.
  returned: always
  type: dict
  sample:
    Config:
      cgroupParent: /libpod_parent
      created: '2020-06-14T15:16:12.230818767+03:00'
      hostname: newpod
      id: a5a5c6cdf8c72272fc5c33f787e8d7501e2fa0c1e92b2b602860defdafeeec58
      infraConfig:
        infraPortBindings: null
        makeInfraContainer: true
      labels: {}
      lockID: 515
      name: newpod
      sharesCgroup: true
      sharesIpc: true
      sharesNet: true
      sharesUts: true
    Containers:
    - id: dc70a947c7ae15198ec38b3c817587584085dee3919cbeb9969e3ab77ba10fd2
      state: configured
    State:
      cgroupPath: /libpod_parent/a5a5c6cdf8c72272fc5c33f787e8d7501e2fa0c1e92b2b602860defdafeeec58
      infraContainerID: dc70a947c7ae15198ec38b3c817587584085dee3919cbeb9969e3ab77ba10fd2
      status: Created

'''

EXAMPLES = '''
# What modules does for example
- podman_pod:
    name: pod1
    state: started
    ports:
      - 4444:5555
'''
from ansible.module_utils.basic import AnsibleModule  # noqa: F402
from ..module_utils.podman.podman_pod_lib import PodmanPodManager  # noqa: F402
from ..module_utils.podman.podman_pod_lib import ARGUMENTS_SPEC_POD  # noqa: F402


def main():
    module = AnsibleModule(
        argument_spec=ARGUMENTS_SPEC_POD
    )
    results = PodmanPodManager(module, module.params).execute()
    module.exit_json(**results)


if __name__ == '__main__':
    main()
