#!/usr/bin/python
# Copyright (c) 2020 Red Hat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# flake8: noqa: E501

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
options:
  name:
    description:
      - Name of the container
    required: True
    type: str
  executable:
    description:
      - Path to C(podman) executable if it is not in the C($PATH) on the
        machine running C(podman)
    default: 'podman'
    type: str
  state:
    description:
      - I(absent) - A container matching the specified name will be stopped and
        removed.
      - I(present) - Asserts the existence of a container matching the name and
        any provided configuration parameters. If no container matches the
        name, a container will be created. If a container matches the name but
        the provided configuration does not match, the container will be
        updated, if it can be. If it cannot be updated, it will be removed and
        re-created with the requested config. Image version will be taken into
        account when comparing configuration. Use the recreate option to force
        the re-creation of the matching container.
      - I(started) - Asserts there is a running container matching the name and
        any provided configuration. If no container matches the name, a
        container will be created and started. Use recreate to always re-create
        a matching container, even if it is running. Use force_restart to force
        a matching container to be stopped and restarted.
      - I(stopped) - Asserts that the container is first I(present), and then
        if the container is running moves it to a stopped state.
    type: str
    default: started
    choices:
      - absent
      - present
      - stopped
      - started
  image:
    description:
      - Repository path (or image name) and tag used to create the container.
        If an image is not found, the image will be pulled from the registry.
        If no tag is included, C(latest) will be used.
      - Can also be an image ID. If this is the case, the image is assumed to
        be available locally.
    type: str
  annotation:
    description:
      - Add an annotation to the container. The format is key value, multiple
        times.
    type: dict
  authfile:
    description:
      - Path of the authentication file. Default is
        ``${XDG_RUNTIME_DIR}/containers/auth.json``
        (Not available for remote commands) You can also override the default
        path of the authentication file by setting the ``REGISTRY_AUTH_FILE``
        environment variable. ``export REGISTRY_AUTH_FILE=path``
    type: path
  blkio_weight:
    description:
      - Block IO weight (relative weight) accepts a weight value between 10 and
        1000
    type: int
  blkio_weight_device:
    description:
      - Block IO weight (relative device weight, format DEVICE_NAME[:]WEIGHT).
    type: dict
  cap_add:
    description:
      - List of capabilities to add to the container.
    type: list
    elements: str
  cap_drop:
    description:
      - List of capabilities to drop from the container.
    type: list
    elements: str
  cgroup_parent:
    description:
      - Path to cgroups under which the cgroup for the container will be
        created.
        If the path is not absolute, the path is considered to be relative to
        the cgroups path of the init process. Cgroups will be created if they
        do not already exist.
    type: path
  cgroupns:
    description:
      - Path to cgroups under which the cgroup for the container will be
        created.
    type: str
  cgroups:
    description:
      - Determines whether the container will create CGroups.
        Valid values are enabled and disabled, which the default being enabled.
        The disabled option will force the container to not create CGroups,
        and thus conflicts with CGroup options cgroupns and cgroup-parent.
    type: str
    choices:
      - default
      - disabled
  cidfile:
    description:
      - Write the container ID to the file
    type: path
  cmd_args:
    description:
      - Any additional command options you want to pass to podman command,
        cmd_args - ['--other-param', 'value']
        Be aware module doesn't support idempotency if this is set.
    type: list
    elements: str
  conmon_pidfile:
    description:
      - Write the pid of the conmon process to a file.
        conmon runs in a separate process than Podman,
        so this is necessary when using systemd to restart Podman containers.
    type: path
  command:
    description:
      - Override command of container. Can be a string or a list.
    type: raw
  cpu_period:
    description:
      - Limit the CPU real-time period in microseconds
    type: int
  cpu_rt_period:
    description:
      - Limit the CPU real-time period in microseconds.
        Limit the container's Real Time CPU usage. This flag tell the kernel to
        restrict the container's Real Time CPU usage to the period you specify.
    type: int
  cpu_rt_runtime:
    description:
      - Limit the CPU real-time runtime in microseconds.
        This flag tells the kernel to limit the amount of time in a given CPU
        period Real Time tasks may consume.
    type: int
  cpu_shares:
    description:
      - CPU shares (relative weight)
    type: int
  cpus:
    description:
      - Number of CPUs. The default is 0.0 which means no limit.
    type: str
  cpuset_cpus:
    description:
      - CPUs in which to allow execution (0-3, 0,1)
    type: str
  cpuset_mems:
    description:
      - Memory nodes (MEMs) in which to allow execution (0-3, 0,1). Only
        effective on NUMA systems.
    type: str
  detach:
    description:
      - Run container in detach mode
    type: bool
    default: True
  debug:
    description:
      - Return additional information which can be helpful for investigations.
    type: bool
    default: False
  detach_keys:
    description:
      - Override the key sequence for detaching a container. Format is a single
        character or ctrl-value
    type: str
  device:
    description:
      - Add a host device to the container.
        The format is <device-on-host>[:<device-on-container>][:<permissions>]
        (e.g. device /dev/sdc:/dev/xvdc:rwm)
    type: list
    elements: str
  device_read_bps:
    description:
      - Limit read rate (bytes per second) from a device
        (e.g. device-read-bps /dev/sda:1mb)
    type: list
  device_read_iops:
    description:
      - Limit read rate (IO per second) from a device
        (e.g. device-read-iops /dev/sda:1000)
    type: list
  device_write_bps:
    description:
      - Limit write rate (bytes per second) to a device
        (e.g. device-write-bps /dev/sda:1mb)
    type: list
  device_write_iops:
    description:
      - Limit write rate (IO per second) to a device
        (e.g. device-write-iops /dev/sda:1000)
    type: list
  dns:
    description:
      - Set custom DNS servers
    type: list
    elements: str
  dns_option:
    description:
      - Set custom DNS options
    type: str
  dns_search:
    description:
      - Set custom DNS search domains (Use dns_search with '' if you don't wish
        to set the search domain)
    type: str
  entrypoint:
    description:
      - Overwrite the default ENTRYPOINT of the image
    type: str
  env:
    description:
      - Set environment variables.
        This option allows you to specify arbitrary environment variables that
        are available for the process that will be launched inside of the
        container.
    type: dict
  env_file:
    description:
      - Read in a line delimited file of environment variables
    type: path
  env_host:
    description:
      - Use all current host environment variables in container.
        Defaults to false.
    type: bool
  etc_hosts:
    description:
      - Dict of host-to-IP mappings, where each host name is a key in the
        dictionary. Each host name will be added to the container's
        ``/etc/hosts`` file.
    type: dict
    aliases:
      - add_hosts
  expose:
    description:
      - Expose a port, or a range of ports (e.g. expose "3300-3310") to set up
        port redirection on the host system.
    type: list
    elements: str
    aliases:
      - exposed
      - exposed_ports
  force_restart:
    description:
      - Force restart of container.
    type: bool
    default: False
    aliases:
      - restart
  gidmap:
    description:
      - Run the container in a new user namespace using the supplied mapping.
    type: str
  group_add:
    description:
      - Add additional groups to run as
    type: list
  healthcheck:
    description:
      - Set or alter a healthcheck command for a container.
    type: str
  healthcheck_interval:
    description:
      - Set an interval for the healthchecks
        (a value of disable results in no automatic timer setup)
        (default "30s")
    type: str
  healthcheck_retries:
    description:
      - The number of retries allowed before a healthcheck is considered to be
        unhealthy. The default value is 3.
    type: int
  healthcheck_start_period:
    description:
      - The initialization time needed for a container to bootstrap.
        The value can be expressed in time format like 2m3s. The default value
        is 0s
    type: str
  healthcheck_timeout:
    description:
      - The maximum time allowed to complete the healthcheck before an interval
        is considered failed. Like start-period, the value can be expressed in
        a time format such as 1m22s. The default value is 30s
    type: str
  hostname:
    description:
      - Container host name. Sets the container host name that is available
        inside the container.
    type: str
  http_proxy:
    description:
      - By default proxy environment variables are passed into the container if
        set for the podman process. This can be disabled by setting the
        http_proxy option to false. The environment variables passed in
        include http_proxy, https_proxy, ftp_proxy, no_proxy, and also the
        upper case versions of those.
        Defaults to true
    type: bool
  image_volume:
    description:
      - Tells podman how to handle the builtin image volumes.
        The options are bind, tmpfs, or ignore (default bind)
    type: str
    choices:
      - 'bind'
      - 'tmpfs'
      - 'ignore'
  image_strict:
    description:
      - Whether to compare images in idempotency by taking into account a full
        name with registry and namespaces.
    type: bool
    default: False
  init:
    description:
      - Run an init inside the container that forwards signals and reaps
        processes.
    type: str
  init_path:
    description:
      - Path to the container-init binary.
    type: str
  interactive:
    description:
      - Keep STDIN open even if not attached. The default is false.
        When set to true, keep stdin open even if not attached.
        The default is false.
    type: bool
  ip:
    description:
      - Specify a static IP address for the container, for example
        '10.88.64.128'.
        Can only be used if no additional CNI networks to join were specified
        via 'network:', and if the container is not joining another container's
        network namespace via 'network container:<name|id>'.
        The address must be within the default CNI network's pool
        (default 10.88.0.0/16).
    type: str
  ipc:
    description:
      - Default is to create a private IPC namespace (POSIX SysV IPC) for the
        container
    type: str
  kernel_memory:
    description:
      - Kernel memory limit
        (format <number>[<unit>], where unit = b, k, m or g)
        Note - idempotency is supported for integers only.
    type: str
  label:
    description:
      - Add metadata to a container, pass dictionary of label names and values
    type: dict
  label_file:
    description:
      - Read in a line delimited file of labels
    type: str
  log_driver:
    description:
      - Logging driver. Used to set the log driver for the container.
        For example log_driver "k8s-file".
    type: str
    choices:
      - k8s-file
      - journald
      - json-file
  log_opt:
    description:
      - Logging driver specific options. Used to set the path to the container
        log file. For example log_opt
        "path=/var/log/container/mycontainer.json"
    type: str
    aliases:
      - log_options
  memory:
    description:
      - Memory limit (format 10k, where unit = b, k, m or g)
        Note - idempotency is supported for integers only.
    type: str
  memory_reservation:
    description:
      - Memory soft limit (format 100m, where unit = b, k, m or g)
        Note - idempotency is supported for integers only.
    type: str
  memory_swap:
    description:
      - A limit value equal to memory plus swap. Must be used with the -m
        (--memory) flag.
        The swap LIMIT should always be larger than -m (--memory) value.
        By default, the swap LIMIT will be set to double the value of --memory
        Note - idempotency is supported for integers only.
    type: str
  memory_swappiness:
    description:
      - Tune a container's memory swappiness behavior. Accepts an integer
        between 0 and 100.
    type: int
  mount:
    description:
      - Attach a filesystem mount to the container. bind or tmpfs
        For example mount
        "type=bind,source=/path/on/host,destination=/path/in/container"
    type: str
  network:
    description:
      - Set the Network mode for the container
        * bridge create a network stack on the default bridge
        * none no networking
        * container:<name|id> reuse another container's network stack
        * host use the podman host network stack.
        * <network-name>|<network-id> connect to a user-defined network
        * ns:<path> path to a network namespace to join
        * slirp4netns use slirp4netns to create a user network stack.
          This is the default for rootless containers
    type: list
    elements: str
    aliases:
      - net
  no_hosts:
    description:
      - Do not create /etc/hosts for the container
        Default is false.
    type: bool
  oom_kill_disable:
    description:
      - Whether to disable OOM Killer for the container or not.
        Default is false.
    type: bool
  oom_score_adj:
    description:
      - Tune the host's OOM preferences for containers (accepts -1000 to 1000)
    type: int
  pid:
    description:
      - Set the PID mode for the container
    type: str
  pids_limit:
    description:
      - Tune the container's PIDs limit. Set -1 to have unlimited PIDs for the
        container.
    type: str
  pod:
    description:
      - Run container in an existing pod.
        If you want podman to make the pod for you, preference the pod name
        with "new:"
    type: str
  privileged:
    description:
      - Give extended privileges to this container. The default is false.
    type: bool
  publish:
    description:
      - Publish a container's port, or range of ports, to the host.
        Format - ip:hostPort:containerPort | ip::containerPort |
        hostPort:containerPort | containerPort
    type: list
    elements: str
    aliases:
      - ports
      - published
      - published_ports
  publish_all:
    description:
      - Publish all exposed ports to random ports on the host interfaces. The
        default is false.
    type: bool
  read_only:
    description:
      - Mount the container's root filesystem as read only. Default is false
    type: bool
  read_only_tmpfs:
    description:
      - If container is running in --read-only mode, then mount a read-write
        tmpfs on /run, /tmp, and /var/tmp. The default is true
    type: bool
  recreate:
    description:
      - Use with present and started states to force the re-creation of an
        existing container.
    type: bool
    default: False
  restart_policy:
    description:
      - Restart policy to follow when containers exit.
        Restart policy will not take effect if a container is stopped via the
        podman kill or podman stop commands. Valid values are
        * no - Do not restart containers on exit
        * on-failure[:max_retries] - Restart containers when they exit with a
          non-0 exit code, retrying indefinitely
          or until the optional max_retries count is hit
        * always - Restart containers when they exit, regardless of status,
          retrying indefinitely
    type: str
  rm:
    description:
      - Automatically remove the container when it exits. The default is false.
    type: bool
    aliases:
      - remove
  rootfs:
    description:
      - If true, the first argument refers to an exploded container on the file
        system. The default is false.
    type: bool
  security_opt:
    description:
      - Security Options. For example security_opt "seccomp=unconfined"
    type: list
    elements: str
  shm_size:
    description:
      - Size of /dev/shm. The format is <number><unit>. number must be greater
        than 0.
        Unit is optional and can be b (bytes), k (kilobytes), m(megabytes), or
        g (gigabytes).
        If you omit the unit, the system uses bytes. If you omit the size
        entirely, the system uses 64m
    type: str
  sig_proxy:
    description:
      - Proxy signals sent to the podman run command to the container process.
        SIGCHLD, SIGSTOP, and SIGKILL are not proxied. The default is true.
    type: bool
  stop_signal:
    description:
      - Signal to stop a container. Default is SIGTERM.
    type: int
  stop_timeout:
    description:
      - Timeout (in seconds) to stop a container. Default is 10.
    type: int
  subgidname:
    description:
      - Run the container in a new user namespace using the map with 'name' in
        the /etc/subgid file.
    type: str
  subuidname:
    description:
      - Run the container in a new user namespace using the map with 'name' in
        the /etc/subuid file.
    type: str
  sysctl:
    description:
      - Configure namespaced kernel parameters at runtime
    type: dict
  systemd:
    description:
      - Run container in systemd mode. The default is true.
    type: bool
  tmpfs:
    description:
      - Create a tmpfs mount. For example tmpfs
        "/tmp" "rw,size=787448k,mode=1777"
    type: dict
  tty:
    description:
      - Allocate a pseudo-TTY. The default is false.
    type: bool
  uidmap:
    description:
      - Run the container in a new user namespace using the supplied mapping.
    type: list
  ulimit:
    description:
      - Ulimit options
    type: list
  user:
    description:
      - Sets the username or UID used and optionally the groupname or GID for
        the specified command.
    type: str
  userns:
    description:
      - Set the user namespace mode for the container.
        It defaults to the PODMAN_USERNS environment variable.
        An empty value means user namespaces are disabled.
    type: str
  uts:
    description:
      - Set the UTS mode for the container
    type: str
  volume:
    description:
      - Create a bind mount. If you specify, volume /HOST-DIR:/CONTAINER-DIR,
        podman bind mounts /HOST-DIR in the host to /CONTAINER-DIR in the
        podman container.
    type: list
    elements: str
    aliases:
      - volumes
  volumes_from:
    description:
      - Mount volumes from the specified container(s).
    type: list
    elements: str
  workdir:
    description:
      - Working directory inside the container.
        The default working directory for running binaries within a container
        is the root directory (/).
    type: str
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
# noqa: F402

import json  # noqa: F402
from distutils.version import LooseVersion  # noqa: F402
import yaml  # noqa: F402

from ansible.module_utils.basic import AnsibleModule  # noqa: F402
from ansible.module_utils._text import to_bytes, to_native  # noqa: F402


class PodmanModuleParams:
    """Creates list of arguments for podman CLI command.

       Arguments:
           action {str} -- action type from 'run', 'stop', 'create', 'delete',
                           'start'
           params {dict} -- dictionary of module parameters

       """

    def __init__(self, action, params, podman_version, module):
        self.params = params
        self.action = action
        self.podman_version = podman_version
        self.module = module

    def construct_command_from_params(self):
        """Create a podman command from given module parameters.

        Returns:
           list -- list of byte strings for Popen command
        """
        if self.action in ['start', 'stop', 'delete']:
            return self.start_stop_delete()
        if self.action in ['create', 'run']:
            cmd = [self.action, '--name', self.params['name']]
            all_param_methods = [func for func in dir(self)
                                 if callable(getattr(self, func))
                                 and func.startswith("addparam")]
            params_set = (i for i in self.params if self.params[i] is not None)
            for param in params_set:
                func_name = "_".join(["addparam", param])
                if func_name in all_param_methods:
                    cmd = getattr(self, func_name)(cmd)
            cmd.append(self.params['image'])
            if self.params['command']:
                if isinstance(self.params['command'], list):
                    cmd += self.params['command']
                else:
                    cmd += self.params['command'].split()
            return [to_bytes(i, errors='surrogate_or_strict') for i in cmd]

    def start_stop_delete(self):

        if self.action in ['stop', 'start']:
            cmd = [self.action, self.params['name']]
            return [to_bytes(i, errors='surrogate_or_strict') for i in cmd]

        if self.action == 'delete':
            cmd = ['rm', '-f', self.params['name']]
            return [to_bytes(i, errors='surrogate_or_strict') for i in cmd]

    def check_version(self, param, minv=None, maxv=None):
        if minv and LooseVersion(minv) > LooseVersion(
                self.podman_version):
            self.module.fail_json(msg="Parameter %s is supported from podman "
                                  "version %s only! Current version is %s" % (
                                      param, minv, self.podman_version))
        if maxv and LooseVersion(maxv) < LooseVersion(
                self.podman_version):
            self.module.fail_json(msg="Parameter %s is supported till podman "
                                  "version %s only! Current version is %s" % (
                                      param, minv, self.podman_version))

    def addparam_annotation(self, c):
        for annotate in self.params['annotation'].items():
            c += ['--annotation', '='.join(annotate)]
        return c

    def addparam_authfile(self, c):
        return c + ['--authfile', self.params['authfile']]

    def addparam_blkio_weight(self, c):
        return c + ['--blkio-weight', self.params['blkio_weight']]

    def addparam_blkio_weight_device(self, c):
        for blkio in self.params['blkio_weight_device'].items():
            c += ['--blkio-weight-device', ':'.join(blkio)]
        return c

    def addparam_cap_add(self, c):
        for cap_add in self.params['cap_add']:
            c += ['--cap-add', cap_add]
        return c

    def addparam_cap_drop(self, c):
        for cap_drop in self.params['cap_drop']:
            c += ['--cap-drop', cap_drop]
        return c

    def addparam_cgroups(self, c):
        self.check_version('--cgroups', minv='1.6.0')
        return c + ['--cgroups=%s' % self.params['cgroups']]

    def addparam_cgroupns(self, c):
        self.check_version('--cgroupns', minv='1.6.2')
        return c + ['--cgroupns=%s' % self.params['cgroupns']]

    def addparam_cgroup_parent(self, c):
        return c + ['--cgroup-parent', self.params['cgroup_parent']]

    def addparam_cidfile(self, c):
        return c + ['--cidfile', self.params['cidfile']]

    def addparam_conmon_pidfile(self, c):
        return c + ['--conmon-pidfile', self.params['conmon_pidfile']]

    def addparam_cpu_period(self, c):
        return c + ['--cpu-period', self.params['cpu_period']]

    def addparam_cpu_rt_period(self, c):
        return c + ['--cpu-rt-period', self.params['cpu_rt_period']]

    def addparam_cpu_rt_runtime(self, c):
        return c + ['--cpu-rt-runtime', self.params['cpu_rt_runtime']]

    def addparam_cpu_shares(self, c):
        return c + ['--cpu-shares', self.params['cpu_shares']]

    def addparam_cpus(self, c):
        return c + ['--cpus', self.params['cpus']]

    def addparam_cpuset_cpus(self, c):
        return c + ['--cpuset-cpus', self.params['cpuset_cpus']]

    def addparam_cpuset_mems(self, c):
        return c + ['--cpuset-mems', self.params['cpuset_mems']]

    def addparam_detach(self, c):
        return c + ['--detach=%s' % self.params['detach']]

    def addparam_detach_keys(self, c):
        return c + ['--detach-keys', self.params['detach_keys']]

    def addparam_device(self, c):
        for dev in self.params['device']:
            c += ['--device', dev]
        return c

    def addparam_device_read_bps(self, c):
        for dev in self.params['device_read_bps']:
            c += ['--device-read-bps', dev]
        return c

    def addparam_device_read_iops(self, c):
        for dev in self.params['device_read_iops']:
            c += ['--device-read-iops', dev]
        return c

    def addparam_device_write_bps(self, c):
        for dev in self.params['device_write_bps']:
            c += ['--device-write-bps', dev]
        return c

    def addparam_device_write_iops(self, c):
        for dev in self.params['device_write_iops']:
            c += ['--device-write-iops', dev]
        return c

    def addparam_dns(self, c):
        return c + ['--dns', ','.join(self.params['dns'])]

    def addparam_dns_option(self, c):
        return c + ['--dns-option', self.params['dns_option']]

    def addparam_dns_search(self, c):
        return c + ['--dns-search', self.params['dns_search']]

    def addparam_entrypoint(self, c):
        return c + ['--entrypoint', self.params['entrypoint']]

    def addparam_env(self, c):
        for env_value in self.params['env'].items():
            c += ['--env',
                  b"=".join([to_bytes(k, errors='surrogate_or_strict')
                             for k in env_value])]
        return c

    def addparam_env_file(self, c):
        return c + ['--env-file', self.params['env_file']]

    def addparam_env_host(self, c):
        self.check_version('--env-host', minv='1.5.0')
        return c + ['--env-host=%s' % self.params['env_host']]

    def addparam_etc_hosts(self, c):
        for host_ip in self.params['etc_hosts'].items():
            c += ['--add-host', ':'.join(host_ip)]
        return c

    def addparam_expose(self, c):
        for exp in self.params['expose']:
            c += ['--expose', exp]
        return c

    def addparam_gidmap(self, c):
        return c + ['--gidmap', self.params['gidmap']]

    def addparam_group_add(self, c):
        for g in self.params['group_add']:
            c += ['--group-add', g]
        return c

    def addparam_healthcheck(self, c):
        return c + ['--healthcheck-command', self.params['healthcheck']]

    def addparam_healthcheck_interval(self, c):
        return c + ['--healthcheck-interval',
                    self.params['healthcheck_interval']]

    def addparam_healthcheck_retries(self, c):
        return c + ['--healthcheck-retries',
                    self.params['healthcheck_retries']]

    def addparam_healthcheck_start_period(self, c):
        return c + ['--healthcheck-start-period',
                    self.params['healthcheck_start_period']]

    def addparam_healthcheck_timeout(self, c):
        return c + ['--healthcheck-timeout',
                    self.params['healthcheck_timeout']]

    def addparam_hostname(self, c):
        return c + ['--hostname', self.params['hostname']]

    def addparam_http_proxy(self, c):
        return c + ['--http-proxy=%s' % self.params['http_proxy']]

    def addparam_image_volume(self, c):
        return c + ['--image-volume', self.params['image_volume']]

    def addparam_init(self, c):
        return c + ['--init', self.params['init']]

    def addparam_init_path(self, c):
        return c + ['--init-path', self.params['init_path']]

    def addparam_interactive(self, c):
        return c + ['--interactive=%s' % self.params['interactive']]

    def addparam_ip(self, c):
        return c + ['--ip', self.params['ip']]

    def addparam_ipc(self, c):
        return c + ['--ipc', self.params['ipc']]

    def addparam_kernel_memory(self, c):
        return c + ['--kernel-memory', self.params['kernel_memory']]

    def addparam_label(self, c):
        for label in self.params['label'].items():
            c += ['--label', b'='.join([to_bytes(l, errors='surrogate_or_strict')
                                        for l in label])]
        return c

    def addparam_label_file(self, c):
        return c + ['--label-file', self.params['label_file']]

    def addparam_log_driver(self, c):
        return c + ['--log-driver', self.params['log_driver']]

    def addparam_log_opt(self, c):
        return c + ['--log-opt', self.params['log_opt']]

    def addparam_memory(self, c):
        return c + ['--memory', self.params['memory']]

    def addparam_memory_reservation(self, c):
        return c + ['--memory-reservation', self.params['memory_reservation']]

    def addparam_memory_swap(self, c):
        return c + ['--memory-swap', self.params['memory_swap']]

    def addparam_memory_swappiness(self, c):
        return c + ['--memory-swappiness', self.params['memory_swappiness']]

    def addparam_mount(self, c):
        return c + ['--mount', self.params['mount']]

    def addparam_network(self, c):
        return c + ['--network', ",".join(self.params['network'])]

    def addparam_no_hosts(self, c):
        return c + ['--no-hosts=%s' % self.params['no_hosts']]

    def addparam_oom_kill_disable(self, c):
        return c + ['--oom-kill-disable=%s' % self.params['oom_kill_disable']]

    def addparam_oom_score_adj(self, c):
        return c + ['--oom-score-adj', self.params['oom_score_adj']]

    def addparam_pid(self, c):
        return c + ['--pid', self.params['pid']]

    def addparam_pids_limit(self, c):
        return c + ['--pids-limit', self.params['pids_limit']]

    def addparam_pod(self, c):
        return c + ['--pod', self.params['pod']]

    def addparam_privileged(self, c):
        return c + ['--privileged=%s' % self.params['privileged']]

    def addparam_publish(self, c):
        for pub in self.params['publish']:
            c += ['--publish', pub]
        return c

    def addparam_publish_all(self, c):
        return c + ['--publish-all=%s' % self.params['publish_all']]

    def addparam_read_only(self, c):
        return c + ['--read-only=%s' % self.params['read_only']]

    def addparam_read_only_tmpfs(self, c):
        return c + ['--read-only-tmpfs=%s' % self.params['read_only_tmpfs']]

    def addparam_restart_policy(self, c):
        return c + ['--restart=%s' % self.params['restart_policy']]

    def addparam_rm(self, c):
        if self.params['rm']:
            c += ['--rm']
        return c

    def addparam_rootfs(self, c):
        return c + ['--rootfs=%s' % self.params['rootfs']]

    def addparam_security_opt(self, c):
        for secopt in self.params['security_opt']:
            c += ['--security-opt', secopt]
        return c

    def addparam_shm_size(self, c):
        return c + ['--shm-size', self.params['shm_size']]

    def addparam_sig_proxy(self, c):
        return c + ['--sig-proxy=%s' % self.params['sig_proxy']]

    def addparam_stop_signal(self, c):
        return c + ['--stop-signal', self.params['stop_signal']]

    def addparam_stop_timeout(self, c):
        return c + ['--stop-timeout', self.params['stop_timeout']]

    def addparam_subgidname(self, c):
        return c + ['--subgidname', self.params['subgidname']]

    def addparam_subuidname(self, c):
        return c + ['--subuidname', self.params['subuidname']]

    def addparam_sysctl(self, c):
        for sysctl in self.params['sysctl'].items():
            c += ['--sysctl',
                  b"=".join([to_bytes(k, errors='surrogate_or_strict')
                             for k in sysctl])]
        return c

    def addparam_systemd(self, c):
        return c + ['--systemd=%s' % self.params['systemd']]

    def addparam_tmpfs(self, c):
        for tmpfs in self.params['tmpfs'].items():
            c += ['--tmpfs', ':'.join(tmpfs)]
        return c

    def addparam_tty(self, c):
        return c + ['--tty=%s' % self.params['tty']]

    def addparam_uidmap(self, c):
        for uidmap in self.params['uidmap']:
            c += ['--uidmap', uidmap]
        return c

    def addparam_ulimit(self, c):
        for u in self.params['ulimit']:
            c += ['--ulimit', u]
        return c

    def addparam_user(self, c):
        return c + ['--user', self.params['user']]

    def addparam_userns(self, c):
        return c + ['--userns', self.params['userns']]

    def addparam_uts(self, c):
        return c + ['--uts', self.params['uts']]

    def addparam_volume(self, c):
        for vol in self.params['volume']:
            if vol:
                c += ['--volume', vol]
        return c

    def addparam_volumes_from(self, c):
        for vol in self.params['volumes_from']:
            c += ['--volumes-from', vol]
        return c

    def addparam_workdir(self, c):
        return c + ['--workdir', self.params['workdir']]

    # Add your own args for podman command
    def addparam_cmd_args(self, c):
        return c + self.params['cmd_args']


class PodmanDefaults:
    def __init__(self, module, image_info, podman_version):
        self.module = module
        self.version = podman_version
        self.image_info = image_info
        self.defaults = {
            "blkio_weight": 0,
            "cgroups": "default",
            "cidfile": "",
            "cpus": 0.0,
            "cpu_shares": 0,
            "cpu_quota": 0,
            "cpu_period": 0,
            "cpu_rt_runtime": 0,
            "cpu_rt_period": 0,
            "cpuset_cpus": "",
            "cpuset_mems": "",
            "detach": True,
            "device": [],
            "env_host": False,
            "etc_hosts": {},
            "group_add": [],
            "ipc": "",
            "kernelmemory": "0",
            "log_driver": "k8s-file",
            "memory": "0",
            "memory_swap": "0",
            "memory_reservation": "0",
            # "memory_swappiness": -1,
            "no_hosts": False,
            # libpod issue with networks in inspection
            "oom_score_adj": 0,
            "pid": "",
            "privileged": False,
            "rm": False,
            "security_opt": [],
            "stop_signal": self.image_info['config'].get('stopsignal', "15"),
            "tty": False,
            "user": self.image_info.get('user', ''),
            "workdir": self.image_info['config'].get('workingdir', '/'),
            "uts": "",
        }

    def default_dict(self):
        # make here any changes to self.defaults related to podman version
        # https://github.com/containers/libpod/pull/5669
        if (LooseVersion(self.version) >= LooseVersion('1.8.0')
                and LooseVersion(self.version) < LooseVersion('1.9.0')):
            self.defaults['cpu_shares'] = 1024
        if (LooseVersion(self.version) >= LooseVersion('2.0.0')):
            self.defaults['network'] = ["slirp4netns"]
            self.defaults['ipc'] = "private"
            self.defaults['uts'] = "private"
            self.defaults['pid'] = "private"
        return self.defaults


class PodmanContainerDiff:
    def __init__(self, module, info, image_info, podman_version):
        self.module = module
        self.version = podman_version
        self.default_dict = None
        self.info = yaml.safe_load(json.dumps(info).lower())
        self.image_info = yaml.safe_load(json.dumps(image_info).lower())
        self.params = self.defaultize()
        self.diff = {'before': {}, 'after': {}}
        self.non_idempotent = {
            'env_file',  # We can't get env vars from file to check
            'env_host',
        }

    def defaultize(self):
        params_with_defaults = {}
        self.default_dict = PodmanDefaults(
            self.module, self.image_info, self.version).default_dict()
        for p in self.module.params:
            if self.module.params[p] is None and p in self.default_dict:
                params_with_defaults[p] = self.default_dict[p]
            else:
                params_with_defaults[p] = self.module.params[p]
        return params_with_defaults

    def _diff_update_and_compare(self, param_name, before, after):
        if before != after:
            self.diff['before'].update({param_name: before})
            self.diff['after'].update({param_name: after})
            return True
        return False

    def diffparam_annotation(self):
        before = self.info['config']['annotations'] or {}
        after = before.copy()
        if self.module.params['annotation'] is not None:
            after.update(self.params['annotation'])
        return self._diff_update_and_compare('annotation', before, after)

    def diffparam_env_host(self):
        # It's impossible to get from inspest, recreate it if not default
        before = False
        after = self.params['env_host']
        return self._diff_update_and_compare('env_host', before, after)

    def diffparam_blkio_weight(self):
        before = self.info['hostconfig']['blkioweight']
        after = self.params['blkio_weight']
        return self._diff_update_and_compare('blkio_weight', before, after)

    def diffparam_blkio_weight_device(self):
        before = self.info['hostconfig']['blkioweightdevice']
        if before == [] and self.module.params['blkio_weight_device'] is None:
            after = []
        else:
            after = self.params['blkio_weight_device']
        return self._diff_update_and_compare('blkio_weight_device', before, after)

    def diffparam_cap_add(self):
        before = self.info['effectivecaps'] or []
        after = []
        if self.module.params['cap_add'] is not None:
            after += ["cap_" + i.lower()
                      for i in self.module.params['cap_add']]
        after += before
        before, after = sorted(list(set(before))), sorted(list(set(after)))
        return self._diff_update_and_compare('cap_add', before, after)

    def diffparam_cap_drop(self):
        before = self.info['effectivecaps'] or []
        after = before[:]
        if self.module.params['cap_drop'] is not None:
            for c in ["cap_" + i.lower() for i in self.module.params['cap_drop']]:
                if c in after:
                    after.remove(c)
        before, after = sorted(list(set(before))), sorted(list(set(after)))
        return self._diff_update_and_compare('cap_drop', before, after)

    def diffparam_cgroup_parent(self):
        before = self.info['hostconfig']['cgroupparent']
        after = self.params['cgroup_parent']
        if after is None:
            after = before
        return self._diff_update_and_compare('cgroup_parent', before, after)

    def diffparam_cgroups(self):
        # Cgroups output is not supported in all versions
        if 'cgroups' in self.info['hostconfig']:
            before = self.info['hostconfig']['cgroups']
            after = self.params['cgroups']
            return self._diff_update_and_compare('cgroups', before, after)
        return False

    def diffparam_cidfile(self):
        before = self.info['hostconfig']['containeridfile']
        after = self.params['cidfile']
        return self._diff_update_and_compare('cidfile', before, after)

    def diffparam_command(self):
        # TODO(sshnaidm): to inspect image to get the default command
        if self.module.params['command'] is not None:
            before = self.info['config']['cmd']
            after = self.params['command']
            if isinstance(after, str):
                after = [i.lower() for i in after.split()]
            elif isinstance(after, list):
                after = [i.lower() for i in after]
            return self._diff_update_and_compare('command', before, after)
        return False

    def diffparam_conmon_pidfile(self):
        before = self.info['conmonpidfile']
        if self.module.params['conmon_pidfile'] is None:
            after = before
        else:
            after = self.params['conmon_pidfile']
        return self._diff_update_and_compare('conmon_pidfile', before, after)

    def diffparam_cpu_period(self):
        before = self.info['hostconfig']['cpuperiod']
        after = self.params['cpu_period']
        return self._diff_update_and_compare('cpu_period', before, after)

    def diffparam_cpu_rt_period(self):
        before = self.info['hostconfig']['cpurealtimeperiod']
        after = self.params['cpu_rt_period']
        return self._diff_update_and_compare('cpu_rt_period', before, after)

    def diffparam_cpu_rt_runtime(self):
        before = self.info['hostconfig']['cpurealtimeruntime']
        after = self.params['cpu_rt_runtime']
        return self._diff_update_and_compare('cpu_rt_runtime', before, after)

    def diffparam_cpu_shares(self):
        before = self.info['hostconfig']['cpushares']
        after = self.params['cpu_shares']
        return self._diff_update_and_compare('cpu_shares', before, after)

    def diffparam_cpus(self):
        before = int(self.info['hostconfig']['nanocpus']) / 1000000000
        after = self.params['cpus']
        return self._diff_update_and_compare('cpus', before, after)

    def diffparam_cpuset_cpus(self):
        before = self.info['hostconfig']['cpusetcpus']
        after = self.params['cpuset_cpus']
        return self._diff_update_and_compare('cpuset_cpus', before, after)

    def diffparam_cpuset_mems(self):
        before = self.info['hostconfig']['cpusetmems']
        after = self.params['cpuset_mems']
        return self._diff_update_and_compare('cpuset_mems', before, after)

    def diffparam_device(self):
        before = [":".join([i['pathonhost'], i['pathincontainer']])
                  for i in self.info['hostconfig']['devices']]
        after = [":".join(i.split(":")[:2]) for i in self.params['device']]
        before, after = sorted(list(set(before))), sorted(list(set(after)))
        return self._diff_update_and_compare('devices', before, after)

    def diffparam_device_read_bps(self):
        before = self.info['hostconfig']['blkiodevicereadbps'] or []
        before = ["%s:%s" % (i['path'], i['rate']) for i in before]
        after = self.params['device_read_bps'] or []
        before, after = sorted(list(set(before))), sorted(list(set(after)))
        return self._diff_update_and_compare('device_read_bps', before, after)

    def diffparam_device_read_iops(self):
        before = self.info['hostconfig']['blkiodevicereadiops'] or []
        before = ["%s:%s" % (i['path'], i['rate']) for i in before]
        after = self.params['device_read_iops'] or []
        before, after = sorted(list(set(before))), sorted(list(set(after)))
        return self._diff_update_and_compare('device_read_iops', before, after)

    def diffparam_device_write_bps(self):
        before = self.info['hostconfig']['blkiodevicewritebps'] or []
        before = ["%s:%s" % (i['path'], i['rate']) for i in before]
        after = self.params['device_write_bps'] or []
        before, after = sorted(list(set(before))), sorted(list(set(after)))
        return self._diff_update_and_compare('device_write_bps', before, after)

    def diffparam_device_write_iops(self):
        before = self.info['hostconfig']['blkiodevicewriteiops'] or []
        before = ["%s:%s" % (i['path'], i['rate']) for i in before]
        after = self.params['device_write_iops'] or []
        before, after = sorted(list(set(before))), sorted(list(set(after)))
        return self._diff_update_and_compare('device_write_iops', before, after)

    # Limited idempotency, it can't guess default values
    def diffparam_env(self):
        env_before = self.info['config']['env'] or {}
        before = {i.split("=")[0]: "=".join(i.split("=")[1:]) for i in env_before}
        after = before.copy()
        if self.params['env']:
            after.update({
                str(k).lower(): str(v).lower()
                for k, v in self.params['env'].items()
            })
        return self._diff_update_and_compare('env', before, after)

    def diffparam_etc_hosts(self):
        if self.info['hostconfig']['extrahosts']:
            before = dict([i.split(":") for i in self.info['hostconfig']['extrahosts']])
        else:
            before = {}
        after = self.params['etc_hosts']
        return self._diff_update_and_compare('etc_hosts', before, after)

    def diffparam_group_add(self):
        before = self.info['hostconfig']['groupadd']
        after = self.params['group_add']
        return self._diff_update_and_compare('group_add', before, after)

    # Healthcheck is only defined in container config if a healthcheck
    # was configured; otherwise the config key isn't part of the config.
    def diffparam_healthcheck(self):
        if 'healthcheck' in self.info['config']:
            # the "test" key is a list of 2 items where the first one is
            # "CMD-SHELL" and the second one is the actual healthcheck command.
            before = self.info['config']['healthcheck']['test'][1]
        else:
            before = ''
        after = self.params['healthcheck'] or before
        return self._diff_update_and_compare('healthcheck', before, after)

    # Because of hostname is random generated, this parameter has partial idempotency only.
    def diffparam_hostname(self):
        before = self.info['config']['hostname']
        after = self.params['hostname'] or before
        return self._diff_update_and_compare('hostname', before, after)

    def diffparam_image(self):
        # TODO(sshnaidm): for strict image compare mode use SHAs
        before = self.info['config']['image']
        after = self.params['image']
        mode = self.params['image_strict']
        if mode is None or not mode:
            # In a idempotency 'lite mode' assume all images from different registries are the same
            before = before.replace(":latest", "")
            after = after.replace(":latest", "")
            before = before.split("/")[-1]
            after = after.split("/")[-1]
        return self._diff_update_and_compare('image', before, after)

    def diffparam_ipc(self):
        before = self.info['hostconfig']['ipcmode']
        after = self.params['ipc']
        if self.params['pod'] and not self.module.params['ipc']:
            after = before
        return self._diff_update_and_compare('ipc', before, after)

    def diffparam_label(self):
        before = self.info['config']['labels'] or {}
        after = self.image_info.get('labels') or {}
        if self.params['label']:
            after.update({
                str(k).lower(): str(v).lower()
                for k, v in self.params['label'].items()
            })
        return self._diff_update_and_compare('label', before, after)

    def diffparam_log_driver(self):
        before = self.info['hostconfig']['logconfig']['type']
        after = self.params['log_driver']
        return self._diff_update_and_compare('log_driver', before, after)

    # Parameter has limited idempotency, unable to guess the default log_path
    def diffparam_log_opt(self):
        before = self.info['logpath']
        if self.module.params['log_opt'] in [None, '']:
            after = before
        else:
            after = self.params['log_opt'].split("=")[1]
        return self._diff_update_and_compare('log_opt', before, after)

    def diffparam_memory(self):
        before = str(self.info['hostconfig']['memory'])
        after = self.params['memory']
        return self._diff_update_and_compare('memory', before, after)

    def diffparam_memory_swap(self):
        # By default it's twice memory parameter
        before = str(self.info['hostconfig']['memoryswap'])
        after = self.params['memory_swap']
        if (self.module.params['memory_swap'] is None
                and self.params['memory'] != 0
                and self.params['memory'].isdigit()):
            after = str(int(self.params['memory']) * 2)
        return self._diff_update_and_compare('memory_swap', before, after)

    def diffparam_memory_reservation(self):
        before = str(self.info['hostconfig']['memoryreservation'])
        after = self.params['memory_reservation']
        return self._diff_update_and_compare('memory_reservation', before, after)

    def diffparam_network(self):
        net_mode_before = self.info['hostconfig']['networkmode']
        net_mode_after = ''
        before = list(self.info['networksettings'].get('networks', {}))
        after = self.params['network'] or []
        # If container is in pod and no networks are provided
        if not self.module.params['network'] and self.params['pod']:
            after = before
            return self._diff_update_and_compare('network', before, after)
        # Check special network modes
        if after in [['bridge'], ['host'], ['slirp4netns'], ['none']]:
            net_mode_after = after[0]
        # If changes are only for network mode and container has no networks
        if net_mode_after and not before:
            # Remove differences between v1 and v2
            net_mode_after = net_mode_after.replace('bridge', 'default')
            net_mode_after = net_mode_after.replace('slirp4netns', 'default')
            net_mode_before = net_mode_before.replace('bridge', 'default')
            net_mode_before = net_mode_before.replace('slirp4netns', 'default')
            return self._diff_update_and_compare('network', net_mode_before, net_mode_after)
        before, after = sorted(list(set(before))), sorted(list(set(after)))
        return self._diff_update_and_compare('network', before, after)

    def diffparam_no_hosts(self):
        before = not bool(self.info['hostspath'])
        after = self.params['no_hosts']
        if self.params['network'] == ['none']:
            after = True
        return self._diff_update_and_compare('no_hosts', before, after)

    def diffparam_oom_score_adj(self):
        before = self.info['hostconfig']['oomscoreadj']
        after = self.params['oom_score_adj']
        return self._diff_update_and_compare('oom_score_adj', before, after)

    def diffparam_privileged(self):
        before = self.info['hostconfig']['privileged']
        after = self.params['privileged']
        return self._diff_update_and_compare('privileged', before, after)

    def diffparam_pid(self):
        before = self.info['hostconfig']['pidmode']
        after = self.params['pid']
        return self._diff_update_and_compare('pid', before, after)

    # TODO(sshnaidm) Need to add port ranges support
    def diffparam_publish(self):
        ports = self.info['hostconfig']['portbindings']
        before = [":".join([
            j[0]['hostip'],
            str(j[0]["hostport"]),
            i.replace('/tcp', '')
        ]).strip(':') for i, j in ports.items()]
        after = self.params['publish'] or []
        if self.params['publish_all']:
            image_ports = self.image_info['config'].get('exposedports', {})
            if image_ports:
                after += list(image_ports.keys())
        after = [i.replace("/tcp", "") for i in after]
        # No support for port ranges yet
        for ports in after:
            if "-" in ports:
                return self._diff_update_and_compare('publish', '', '')
        before, after = sorted(list(set(before))), sorted(list(set(after)))
        return self._diff_update_and_compare('publish', before, after)

    def diffparam_rm(self):
        before = self.info['hostconfig']['autoremove']
        after = self.params['rm']
        return self._diff_update_and_compare('rm', before, after)

    def diffparam_security_opt(self):
        before = self.info['hostconfig']['securityopt']
        # In rootful containers with apparmor there is a default security opt
        before = [o for o in before if 'apparmor=containers-default' not in o]
        after = self.params['security_opt']
        before, after = sorted(list(set(before))), sorted(list(set(after)))
        return self._diff_update_and_compare('security_opt', before, after)

    def diffparam_stop_signal(self):
        signals = {
            "sighup": "1",
            "sigint": "2",
            "sigquit": "3",
            "sigill": "4",
            "sigtrap": "5",
            "sigabrt": "6",
            "sigiot": "6",
            "sigbus": "7",
            "sigfpe": "8",
            "sigkill": "9",
            "sigusr1": "10",
            "sigsegv": "11",
            "sigusr2": "12",
            "sigpipe": "13",
            "sigalrm": "14",
            "sigterm": "15",
            "sigstkflt": "16",
            "sigchld": "17",
            "sigcont": "18",
            "sigstop": "19",
            "sigtstp": "20",
            "sigttin": "21",
            "sigttou": "22",
            "sigurg": "23",
            "sigxcpu": "24",
            "sigxfsz": "25",
            "sigvtalrm": "26",
            "sigprof": "27",
            "sigwinch": "28",
            "sigio": "29",
            "sigpwr": "30",
            "sigsys": "31"
        }
        before = str(self.info['config']['stopsignal'])
        if not before.isdigit():
            before = signals[before]
        after = str(self.params['stop_signal'])
        if not after.isdigit():
            after = signals[after]
        return self._diff_update_and_compare('stop_signal', before, after)

    def diffparam_tty(self):
        before = self.info['config']['tty']
        after = self.params['tty']
        return self._diff_update_and_compare('tty', before, after)

    def diffparam_user(self):
        before = self.info['config']['user']
        after = self.params['user']
        return self._diff_update_and_compare('user', before, after)

    def diffparam_ulimit(self):
        after = self.params['ulimit'] or []
        # In case of latest podman
        if 'createcommand' in self.info['config']:
            ulimits = []
            for k, c in enumerate(self.info['config']['createcommand']):
                if c == '--ulimit':
                    ulimits.append(self.info['config']['createcommand'][k + 1])
            before = ulimits
            before, after = sorted(before), sorted(after)
            return self._diff_update_and_compare('ulimit', before, after)
        if after:
            ulimits = self.info['hostconfig']['ulimits']
            before = {
                u['name'].replace('rlimit_', ''): "%s:%s" % (u['soft'], u['hard']) for u in ulimits}
            after = {i.split('=')[0]: i.split('=')[1] for i in self.params['ulimit']}
            new_before = []
            new_after = []
            for u in list(after.keys()):
                # We don't support unlimited ulimits because it depends on platform
                if u in before and "-1" not in after[u]:
                    new_before.append([u, before[u]])
                    new_after.append([u, after[u]])
            return self._diff_update_and_compare('ulimit', new_before, new_after)
        return self._diff_update_and_compare('ulimit', '', '')

    def diffparam_uts(self):
        before = self.info['hostconfig']['utsmode']
        after = self.params['uts']
        if self.params['pod'] and not self.module.params['uts']:
            after = before
        return self._diff_update_and_compare('uts', before, after)

    def diffparam_volume(self):
        def clean_volume(x):
            '''Remove trailing and double slashes from volumes.'''
            return x.replace("//", "/").rstrip("/")

        before = self.info['mounts']
        before_local_vols = []
        if before:
            volumes = []
            local_vols = []
            for m in before:
                if m['type'] != 'volume':
                    volumes.append([m['source'], m['destination']])
                elif m['type'] == 'volume':
                    local_vols.append([m['name'], m['destination']])
            before = [":".join(v) for v in volumes]
            before_local_vols = [":".join(v) for v in local_vols]
        if self.params['volume'] is not None:
            after = [":".join(
                [clean_volume(i) for i in v.split(":")[:2]]
            ) for v in self.params['volume']]
        else:
            after = []
        if before_local_vols:
            after = list(set(after).difference(before_local_vols))
        before, after = sorted(list(set(before))), sorted(list(set(after)))
        return self._diff_update_and_compare('volume', before, after)

    def diffparam_volumes_from(self):
        # Possibly volumesfrom is not in config
        before = self.info['hostconfig'].get('volumesfrom', []) or []
        after = self.params['volumes_from'] or []
        return self._diff_update_and_compare('volumes_from', before, after)

    def diffparam_workdir(self):
        before = self.info['config']['workingdir']
        after = self.params['workdir']
        return self._diff_update_and_compare('workdir', before, after)

    def is_different(self):
        diff_func_list = [func for func in dir(self)
                          if callable(getattr(self, func)) and func.startswith(
                              "diffparam")]
        fail_fast = not bool(self.module._diff)
        different = False
        for func_name in diff_func_list:
            dff_func = getattr(self, func_name)
            if dff_func():
                if fail_fast:
                    return True
                different = True
        # Check non idempotent parameters
        for p in self.non_idempotent:
            if self.module.params[p] is not None and self.module.params[p] not in [{}, [], '']:
                different = True
        return different


def ensure_image_exists(module, image):
    """If image is passed, ensure it exists, if not - pull it or fail.

    Arguments:
        module {obj} -- ansible module object
        image {str} -- name of image

    Returns:
        list -- list of image actions - if it pulled or nothing was done
    """
    image_actions = []
    module_exec = module.params['executable']
    if not image:
        return image_actions
    rc, out, err = module.run_command([module_exec, 'image', 'exists', image])
    if rc == 0:
        return image_actions
    rc, out, err = module.run_command([module_exec, 'image', 'pull', image])
    if rc != 0:
        module.fail_json(msg="Can't pull image %s" % image, stdout=out,
                         stderr=err)
    image_actions.append("pulled image %s" % image)
    return image_actions


class PodmanContainer:
    """Perform container tasks.

    Manages podman container, inspects it and checks its current state
    """

    def __init__(self, module, name):
        """Initialize PodmanContainer class.

        Arguments:
            module {obj} -- ansible module object
            name {str} -- name of container
        """

        super(PodmanContainer, self).__init__()
        self.module = module
        self.name = name
        self.stdout, self.stderr = '', ''
        self.info = self.get_info()
        self.version = self._get_podman_version()
        self.diff = {}
        self.actions = []

    @property
    def exists(self):
        """Check if container exists."""
        return bool(self.info != {})

    @property
    def different(self):
        """Check if container is different."""
        diffcheck = PodmanContainerDiff(
            self.module,
            self.info,
            self.get_image_info(),
            self.version)
        is_different = diffcheck.is_different()
        diffs = diffcheck.diff
        if self.module._diff and is_different and diffs['before'] and diffs['after']:
            self.diff['before'] = "\n".join(
                ["%s - %s" % (k, v) for k, v in sorted(
                    diffs['before'].items())]) + "\n"
            self.diff['after'] = "\n".join(
                ["%s - %s" % (k, v) for k, v in sorted(
                    diffs['after'].items())]) + "\n"
        return is_different

    @property
    def running(self):
        """Return True if container is running now."""
        return self.exists and self.info['State']['Running']

    @property
    def stopped(self):
        """Return True if container exists and is not running now."""
        return self.exists and not self.info['State']['Running']

    def get_info(self):
        """Inspect container and gather info about it."""
        # pylint: disable=unused-variable
        rc, out, err = self.module.run_command(
            [self.module.params['executable'], b'container', b'inspect', self.name])
        return json.loads(out)[0] if rc == 0 else {}

    def get_image_info(self):
        """Inspect container image and gather info about it."""
        # pylint: disable=unused-variable
        rc, out, err = self.module.run_command(
            [self.module.params['executable'], b'image', b'inspect', self.module.params['image']])
        return json.loads(out)[0] if rc == 0 else {}

    def _get_podman_version(self):
        # pylint: disable=unused-variable
        rc, out, err = self.module.run_command(
            [self.module.params['executable'], b'--version'])
        if rc != 0 or not out or "version" not in out:
            self.module.fail_json(msg="%s run failed!" % self.module.params['executable'])
        return out.split("version")[1].strip()

    def _perform_action(self, action):
        """Perform action with container.

        Arguments:
            action {str} -- action to perform - start, create, stop, run,
                            delete
        """
        b_command = PodmanModuleParams(action,
                                       self.module.params,
                                       self.version,
                                       self.module,
                                       ).construct_command_from_params()
        full_cmd = " ".join([self.module.params['executable']]
                            + [to_native(i) for i in b_command])
        self.module.log("PODMAN-CONTAINER-DEBUG: %s" % full_cmd)
        self.actions.append(full_cmd)
        if not self.module.check_mode:
            rc, out, err = self.module.run_command(
                [self.module.params['executable'], b'container'] + b_command,
                expand_user_and_vars=False)
            self.stdout = out
            self.stderr = err
            if rc != 0:
                self.module.fail_json(
                    msg="Can't %s container %s" % (action, self.name),
                    stdout=out, stderr=err)

    def run(self):
        """Run the container."""
        self._perform_action('run')

    def delete(self):
        """Delete the container."""
        self._perform_action('delete')

    def stop(self):
        """Stop the container."""
        self._perform_action('stop')

    def start(self):
        """Start the container."""
        self._perform_action('start')

    def create(self):
        """Create the container."""
        self._perform_action('create')

    def recreate(self):
        """Recreate the container."""
        self.delete()
        self.run()

    def restart(self):
        """Restart the container."""
        self.stop()
        self.run()


class PodmanManager:
    """Module manager class.

    Defines according to parameters what actions should be applied to container
    """

    def __init__(self, module):
        """Initialize PodmanManager class.

        Arguments:
            module {obj} -- ansible module object
        """

        super(PodmanManager, self).__init__()

        self.module = module
        self.results = {
            'changed': False,
            'actions': [],
            'container': {},
        }
        self.name = self.module.params['name']
        self.executable = \
            self.module.get_bin_path(self.module.params['executable'],
                                     required=True)
        self.image = self.module.params['image']
        image_actions = ensure_image_exists(self.module, self.image)
        self.results['actions'] += image_actions
        self.state = self.module.params['state']
        self.restart = self.module.params['force_restart']
        self.recreate = self.module.params['recreate']
        self.container = PodmanContainer(self.module, self.name)

    def update_container_result(self, changed=True):
        """Inspect the current container, update results with last info, exit.

        Keyword Arguments:
            changed {bool} -- whether any action was performed
                              (default: {True})
        """
        facts = self.container.get_info() if changed else self.container.info
        out, err = self.container.stdout, self.container.stderr
        self.results.update({'changed': changed, 'container': facts,
                             'podman_actions': self.container.actions},
                            stdout=out, stderr=err)
        if self.container.diff:
            self.results.update({'diff': self.container.diff})
        if self.module.params['debug']:
            self.results.update({'podman_version': self.container.version})
        self.module.exit_json(**self.results)

    def make_started(self):
        """Run actions if desired state is 'started'."""
        if self.container.running and \
                (self.container.different or self.recreate):
            self.container.recreate()
            self.results['actions'].append('recreated %s' %
                                           self.container.name)
            self.update_container_result()
        elif self.container.running and not self.container.different:
            if self.restart:
                self.container.restart()
                self.results['actions'].append('restarted %s' %
                                               self.container.name)
                self.update_container_result()
            self.update_container_result(changed=False)
        elif not self.container.exists:
            self.container.run()
            self.results['actions'].append('started %s' % self.container.name)
            self.update_container_result()
        elif self.container.stopped and self.container.different:
            self.container.recreate()
            self.results['actions'].append('recreated %s' %
                                           self.container.name)
            self.update_container_result()
        elif self.container.stopped and not self.container.different:
            self.container.start()
            self.results['actions'].append('started %s' % self.container.name)
            self.update_container_result()

    def make_stopped(self):
        """Run actions if desired state is 'stopped'."""
        if not self.container.exists and not self.image:
            self.module.fail_json(msg='Cannot create container when image'
                                      ' is not specified!')
        if not self.container.exists:
            self.container.create()
            self.results['actions'].append('created %s' % self.container.name)
            self.update_container_result()
        if self.container.stopped:
            self.update_container_result(changed=False)
        elif self.container.running:
            self.container.stop()
            self.results['actions'].append('stopped %s' % self.container.name)
            self.update_container_result()

    def make_absent(self):
        """Run actions if desired state is 'absent'."""
        if not self.container.exists:
            self.results.update({'changed': False})
        elif self.container.exists:
            self.container.delete()
            self.results['actions'].append('deleted %s' % self.container.name)
            self.results.update({'changed': True})
        self.results.update({'container': {},
                             'podman_actions': self.container.actions})
        self.module.exit_json(**self.results)

    def execute(self):
        """Execute the desired action according to map of actions & states."""
        states_map = {
            'present': self.make_started,
            'started': self.make_started,
            'absent': self.make_absent,
            'stopped': self.make_stopped
        }
        process_action = states_map[self.state]
        process_action()
        self.module.fail_json(msg="Unexpected logic error happened, "
                                  "please contact maintainers ASAP!")


def main():
    module = AnsibleModule(
        argument_spec=yaml.safe_load(DOCUMENTATION)['options'],
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

    PodmanManager(module).execute()


if __name__ == '__main__':
    main()
