#!/usr/bin/python
# Copyright (c) 2020 Red Hat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# flake8: noqa: E501
from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
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
      - quadlet
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
  blkio_weight:
    description:
    - Block IO relative weight. The weight is a value between 10 and 1000.
    - This option is not supported on cgroups V1 rootless systems.
    type: str
    required: false
  blkio_weight_device:
    description:
    - Block IO relative device weight.
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
  cpus:
    description:
    - Set the total number of CPUs delegated to the pod.
      Default is 0.000 which indicates that there is no limit on computation power.
    required: false
    type: str
  cpuset_cpus:
    description:
    - Limit the CPUs to support execution. First CPU is numbered 0.
      Unlike `cpus` this is of type string and parsed as a list of numbers. Format is 0-3,0,1
    required: false
    type: str
  cpuset_mems:
    description:
    - Memory nodes in which to allow execution (0-3, 0,1). Only effective on NUMA systems.
    required: false
    type: str
  cpu_shares:
    description:
    - CPU shares (relative weight).
    required: false
    type: str
  device:
    description:
    - Add a host device to the pod. Optional permissions parameter can be used to specify
      device permissions. It is a combination of r for read, w for write, and m for mknod(2)
    elements: str
    required: false
    type: list
  device_read_bps:
    description:
    - Limit read rate (bytes per second) from a device (e.g. device-read-bps=/dev/sda:1mb)
    elements: str
    required: false
    type: list
  device_write_bps:
    description:
    - Limit write rate (in bytes per second) to a device.
    type: list
    elements: str
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
    aliases:
      - dns_option
    required: false
  dns_search:
    description:
    - Set custom DNS search domains in the /etc/resolv.conf file that will be shared
      between all containers in the pod.
    type: list
    elements: str
    required: false
  exit_policy:
    description:
      - Set the exit policy of the pod when the last container exits. Supported policies are stop and continue
    choices:
      - stop
      - continue
    type: str
    required: false
  generate_systemd:
    description:
      - Generate systemd unit file for container.
    type: dict
    default: {}
    suboptions:
      path:
        description:
          - Specify a path to the directory where unit files will be generated.
            Required for this option. If it doesn't exist, the directory will be created.
        type: str
        required: false
      restart_policy:
        description:
          - Specify a restart policy for the service.  The restart-policy must be one of
            "no", "on-success", "on-failure", "on-abnormal", "on-watchdog", "on-abort", or "always".
            The default policy is "on-failure".
        type: str
        required: false
        choices:
            - 'no'
            - 'on-success'
            - 'on-failure'
            - 'on-abnormal'
            - 'on-watchdog'
            - 'on-abort'
            - 'always'
      restart_sec:
        description: Set the systemd service restartsec value.
        type: int
        required: false
      start_timeout:
        description: Override the default start timeout for the container with the given value.
        type: int
        required: false
      stop_timeout:
        description:
          - Override the default stop timeout for the container with the given value. Called `time` before version 4.
        type: int
        required: false
        aliases:
          - time
      no_header:
        description:
          - Do not generate the header including meta data such as the Podman version and the timestamp.
            From podman version 3.1.0.
        type: bool
        default: false
      names:
        description:
          - Use names of the containers for the start, stop, and description in the unit file.
            Default is true.
        type: bool
        default: true
      container_prefix:
        description:
          - Set the systemd unit name prefix for containers. The default is "container".
        type: str
        required: false
      pod_prefix:
        description:
          - Set the systemd unit name prefix for pods. The default is "pod".
        type: str
        required: false
      separator:
        description:
          - Set the systemd unit name separator between the name/id of a
            container/pod and the prefix. The default is "-" (dash).
        type: str
        required: false
      new:
        description:
          - Create containers and pods when the unit is started instead of
            expecting them to exist. The default is "false".
            Refer to podman-generate-systemd(1) for more information.
        type: bool
        default: false
      after:
        type: list
        elements: str
        required: false
        description:
          - Add the systemd unit after (After=) option, that ordering dependencies between the list of dependencies and this service.
      wants:
        type: list
        elements: str
        required: false
        description:
          - Add the systemd unit wants (Wants=) option, that this service is (weak) dependent on.
      requires:
        type: list
        elements: str
        required: false
        description:
          - Set the systemd unit requires (Requires=) option. Similar to wants, but declares a stronger requirement dependency.
  gidmap:
    description:
    - GID map for the user namespace. Using this flag will run the container with
      user namespace enabled. It conflicts with the `userns` and `subgidname` flags.
    elements: str
    required: false
    type: list
  gpus:
    description:
    - GPU devices to add to the container ('all' to pass all GPUs).
    type: str
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
  infra_name:
    description:
    - The name that will be used for the pod's infra container.
    type: str
    required: false
  ip:
    description:
    - Set a static IP for the pod's shared network.
    type: str
    required: false
  ip6:
    description:
    - Set a static IPv6 for the pod's shared network.
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
  memory:
    description:
    - Set memory limit.
    - A unit can be b (bytes), k (kibibytes), m (mebibytes), or g (gibibytes).
    type: str
    required: false
  memory_swap:
    description:
    - Set limit value equal to memory plus swap.
    - A unit can be b (bytes), k (kibibytes), m (mebibytes), or g (gibibytes).
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
      network), or a list of names of CNI networks to join.
    type: list
    elements: str
    required: false
  network_alias:
    description:
    - Add a network-scoped alias for the pod, setting the alias for all networks that the pod joins.
      To set a name only for a specific network, use the alias option as described under the -`network` option.
      Network aliases work only with the bridge networking mode.
      This option can be specified multiple times.
    elements: str
    required: false
    type: list
    aliases:
      - network_aliases
  no_hosts:
    description:
    - Disable creation of /etc/hosts for the pod.
    type: bool
    required: false
  pid:
    description:
    - Set the PID mode for the pod. The default is to create a private PID namespace
      for the pod. Requires the PID namespace to be shared via `share` option.
    required: false
    type: str
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
  quadlet_dir:
    description:
      - Path to the directory to write quadlet file in.
        By default, it will be set as C(/etc/containers/systemd/) for root user,
        C(~/.config/containers/systemd/) for non-root users.
    type: path
  quadlet_filename:
    description:
      - Name of quadlet file to write. By default it takes I(name) value.
    type: str
  quadlet_file_mode:
    description:
      - The permissions of the quadlet file.
      - The O(quadlet_file_mode) can be specied as octal numbers or as a symbolic mode (for example, V(u+rwx) or V(u=rw,g=r,o=r)).
        For octal numbers format, you must either add a leading zero so that Ansible's YAML parser knows it is an
        octal number (like V(0644) or V(01777)) or quote it (like V('644') or V('1777')) so Ansible receives a string
        and can do its own conversion from string into number. Giving Ansible a number without following one of these
        rules will end up with a decimal number which will have unexpected results.
      - If O(quadlet_file_mode) is not specified and the quadlet file B(does not) exist, the default C(umask) on the system will be used
        when setting the mode for the newly created file.
      - If O(quadlet_file_mode) is not specified and the quadlet file B(does) exist, the mode of the existing file will be used.
      - Specifying O(quadlet_file_mode) is the best way to ensure files are created with the correct permissions.
    type: raw
    required: false
  quadlet_options:
    description:
      - Options for the quadlet file. Provide missing in usual container args
        options as a list of lines to add.
    type: list
    elements: str
  restart_policy:
    description:
      - Restart policy to follow when containers exit.
    type: str
  security_opt:
    description:
    - Security options for the pod.
    type: list
    elements: str
    required: false
  share:
    description:
    - A comma delimited list of kernel namespaces to share. If none or "" is specified,
      no namespaces will be shared. The namespaces to choose from are ipc, net, pid,
      user, uts.
    type: str
    required: false
  share_parent:
    description:
    - This boolean determines whether or not all containers entering the pod use the pod as their cgroup parent.
      The default value of this option in Podman is true.
    type: bool
    required: false
  shm_size:
    description:
    - Set the size of the /dev/shm shared memory space.
      A unit can be b (bytes), k (kibibytes), m (mebibytes), or g (gibibytes).
      If the unit is omitted, the system uses bytes.
      If the size is omitted, the default is 64m.
      When size is 0, there is no limit on the amount of memory used for IPC by the pod.
    type: str
    required: false
  shm_size_systemd:
    description:
    - Size of systemd-specific tmpfs mounts such as /run, /run/lock, /var/log/journal and /tmp.
      A unit can be b (bytes), k (kibibytes), m (mebibytes), or g (gibibytes).
      If the unit is omitted, the system uses bytes.
      If the size is omitted, the default is 64m.
      When size is 0, the usage is limited to 50 percents of the host's available memory.
    type: str
    required: false
  subgidname:
    description:
    - Name for GID map from the /etc/subgid file. Using this flag will run the container
      with user namespace enabled. This flag conflicts with `userns` and `gidmap`.
    required: false
    type: str
  subuidname:
    description:
    - Name for UID map from the /etc/subuid file.
      Using this flag will run the container with user namespace enabled.
      This flag conflicts with `userns` and `uidmap`.
    required: false
    type: str
  sysctl:
    description:
    - Set kernel parameters for the pod.
    type: dict
    required: false
  uidmap:
    description:
    - Run the container in a new user namespace using the supplied mapping.
      This option conflicts with the `userns` and `subuidname` options.
      This option provides a way to map host UIDs to container UIDs.
      It can be passed several times to map different ranges.
    elements: str
    required: false
    type: list
  userns:
    description:
    - Set the user namespace mode for all the containers in a pod.
      It defaults to the PODMAN_USERNS environment variable.
      An empty value ("") means user namespaces are disabled.
    required: false
    type: str
  uts:
    description:
    - Set the UTS namespace mode for the pod.
    required: false
    type: str
  volume:
    description:
    - Create a bind mount.
    aliases:
    - volumes
    elements: str
    required: false
    type: list
  volumes_from:
    description:
    - Mount volumes from the specified container.
    elements: str
    required: false
    type: list
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

"""

RETURN = r"""
pod:
  description: Pod inspection results for the given pod
    built.
  returned: always
  type: dict
  sample:
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
"""

EXAMPLES = r"""
# What modules does for example
- containers.podman.podman_pod:
    name: pod1
    state: started
    ports:
      - "4444:5555"

# Connect random port from localhost to port 80 on pod2
- name: Connect random port from localhost to port 80 on pod2
  containers.podman.podman_pod:
    name: pod2
    state: started
    publish: "127.0.0.1::80"

# Full workflow example with pod and containers
- name: Create a pod with parameters
  containers.podman.podman_pod:
    name: mypod
    state: created
    network: host
    share: net
    userns: auto
    security_opt:
      - seccomp=unconfined
      - apparmor=unconfined
    hostname: mypod
    dns:
      - 1.1.1.1
    volumes:
      - /tmp:/tmp/:ro
    label:
      key: cval
      otherkey: kddkdk
      somekey: someval
    add_host:
      - "google:5.5.5.5"

- name: Create containers attached to the pod
  containers.podman.podman_container:
    name: "{{ item }}"
    state: created
    pod: mypod
    image: alpine
    command: sleep 1h
    loop:
      - "container1"
      - "container2"

- name: Start pod
  containers.podman.podman_pod:
    name: mypod
    state: started
    network: host
    share: net
    userns: auto
    security_opt:
      - seccomp=unconfined
      - apparmor=unconfined
    hostname: mypod
    dns:
      - 1.1.1.1
    volumes:
      - /tmp:/tmp/:ro
    label:
      key: cval
      otherkey: kddkdk
      somekey: someval
    add_host:
      - "google:5.5.5.5"

# Create a Quadlet file for a pod
- containers.podman.podman_pod:
    name: qpod
    state: quadlet
    ports:
      - "4444:5555"
    volume:
      - /var/run/docker.sock:/var/run/docker.sock
    quadlet_dir: /custom/dir
"""
from ansible.module_utils.basic import AnsibleModule  # noqa: F402
from ..module_utils.podman.podman_pod_lib import PodmanPodManager  # noqa: F402
from ..module_utils.podman.podman_pod_lib import ARGUMENTS_SPEC_POD  # noqa: F402


def main():
    module = AnsibleModule(argument_spec=ARGUMENTS_SPEC_POD)
    results = PodmanPodManager(module, module.params).execute()
    module.exit_json(**results)


if __name__ == "__main__":
    main()
