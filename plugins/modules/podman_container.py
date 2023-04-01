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
  - podman
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
      - I(created) - Asserts that the container exists with given configuration.
        If container doesn't exist, the module creates it and leaves it in
        'created' state. If configuration doesn't match or 'recreate' option is
        set, the container will be recreated
    type: str
    default: started
    choices:
      - absent
      - present
      - stopped
      - started
      - created
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
    aliases:
      - capabilities
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
  cidfile:
    description:
      - Write the container ID to the file
    type: path
  cmd_args:
    description:
      - Any additional command options you want to pass to podman command itself,
        for example C(--log-level=debug) or C(--syslog). This is NOT command to
        run in container, but rather options for podman itself.
        For container command please use I(command) option.
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
    elements: str
  device_read_iops:
    description:
      - Limit read rate (IO per second) from a device
        (e.g. device-read-iops /dev/sda:1000)
    type: list
    elements: str
  device_write_bps:
    description:
      - Limit write rate (bytes per second) to a device
        (e.g. device-write-bps /dev/sda:1mb)
    type: list
    elements: str
  device_write_iops:
    description:
      - Limit write rate (IO per second) to a device
        (e.g. device-write-iops /dev/sda:1000)
    type: list
    elements: str
  dns:
    description:
      - Set custom DNS servers
    type: list
    elements: str
    aliases:
      - dns_servers
  dns_option:
    description:
      - Set custom DNS options
    type: str
    aliases:
      - dns_opts
  dns_search:
    description:
      - Set custom DNS search domains (Use dns_search with '' if you don't wish
        to set the search domain)
    type: str
    aliases:
      - dns_search_domains
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
      - Read in a line delimited file of environment variables. Doesn't support
        idempotency. If users changes the file with environment variables it's
        on them to recreate the container.
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
      time:
        description:
          - Override the default stop timeout for the container with the given value.
        type: int
        required: false
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
      - Run the container in a new user namespace using the supplied mapping.
    type: list
    elements: str
  group_add:
    description:
      - Add additional groups to run as
    type: list
    elements: str
    aliases:
      - groups
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
  hooks_dir:
    description:
      - Each .json file in the path configures a hook for Podman containers.
        For more details on the syntax of the JSON files and the semantics of
        hook injection, see oci-hooks(5). Can be set multiple times.
    type: list
    elements: str
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
        processes. The default is false.
    type: bool
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
    aliases:
      - ipc_mode
  kernel_memory:
    description:
      - Kernel memory limit
        (format <number>[<unit>], where unit = b, k, m or g)
        Note - idempotency is supported for integers only.
    type: str
  label:
    description:
      - Add metadata to a container, pass dictionary of label names and values
    aliases:
    - labels
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
  log_level:
    description:
      - Logging level for Podman. Log messages above specified level
        ("debug"|"info"|"warn"|"error"|"fatal"|"panic") (default "error")
    type: str
    choices:
      - debug
      - info
      - warn
      - error
      - fatal
      - panic
  log_opt:
    description:
      - Logging driver specific options. Used to set the path to the container
        log file.
    type: dict
    aliases:
      - log_options
    suboptions:
      path:
        description:
          - Specify a path to the log file (e.g. /var/log/container/mycontainer.json).
        type: str
        required: false
      max_size:
        description:
          - Specify a max size of the log file (e.g 10mb).
        type: str
        required: false
      tag:
        description:
          - Specify a custom log tag for the container.
        type: str
        required: false

  mac_address:
    description:
      - Specify a MAC address for the container, for example
        '92:d0:c6:0a:29:33'.
        Don't forget that it must be unique within one Ethernet network.
    type: str
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
    type: list
    elements: str
    aliases:
      - mounts
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
      - network_mode
  network_aliases:
    description:
      - Add network-scoped alias for the container.
        A container will only have access to aliases on the first network that it joins.
        This is a limitation that will be removed in a later release.
    type: list
    elements: str
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
    aliases:
      - pid_mode
  pids_limit:
    description:
      - Tune the container's PIDs limit. Set -1 to have unlimited PIDs for the
        container.
    type: str
  pod:
    description:
      - Run container in an existing pod.
        If you want podman to make the pod for you, prefix the pod name
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
        In case of only containerPort is set, the hostPort will chosen
        randomly by Podman.
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
  requires:
    description:
      - Specify one or more requirements. A requirement is a dependency
        container that will be started before this container.
        Containers can be specified by name or ID.
    type: list
    elements: str
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
      - auto_remove
  rootfs:
    description:
      - If true, the first argument refers to an exploded container on the file
        system. The default is false.
    type: bool
  sdnotify:
    description:
      - Determines how to use the NOTIFY_SOCKET, as passed with systemd and Type=notify.
        Can be container, conmon, ignore.
    type: str
  secrets:
    description:
      - Add the named secrets into the container.
        The format is C(secret[,opt=opt...]), see
        L(documentation,https://docs.podman.io/en/latest/markdown/podman-run.1.html#secret-secret-opt-opt) for more details.
    type: list
    elements: str
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
    type: str
  timezone:
    description:
      - Set timezone in container. This flag takes area-based timezones,
        GMT time, as well as local, which sets the timezone in the container to
        match the host machine.
        See /usr/share/zoneinfo/ for valid timezones.
        Remote connections use local containers.conf for defaults.
    type: str
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
    elements: str
  ulimit:
    description:
      - Ulimit options
    type: list
    elements: str
    aliases:
      - ulimits
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
    aliases:
      - userns_mode
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
    aliases:
      - working_dir
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

- name: Re-create a redis container with systemd service file generated in /tmp/
  containers.podman.podman_container:
    name: myredis
    image: redis
    command: redis-server --appendonly yes
    state: present
    recreate: true
    expose:
      - 6379
    volumes_from:
      - mydata
    generate_systemd:
      path: /tmp/
      restart_policy: always
      time: 120
      names: true
      container_prefix: ainer

- name: Restart a container
  containers.podman.podman_container:
    name: myapplication
    image: redis
    state: started
    restart: true
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
    recreate: true
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
    if (module.params['state'] in ['present', 'created']
            and not module.params['force_restart']
            and not module.params['image']):
        module.fail_json(msg="State '%s' required image to be configured!" %
                             module.params['state'])

    results = PodmanManager(module, module.params).execute()
    module.exit_json(**results)


if __name__ == '__main__':
    main()
