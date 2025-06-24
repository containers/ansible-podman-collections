from __future__ import absolute_import, division, print_function
import json  # noqa: F402
import os  # noqa: F402
import shlex  # noqa: F402

from ansible.module_utils._text import to_bytes, to_native  # noqa: F402
from ansible_collections.containers.podman.plugins.module_utils.podman.common import (
    LooseVersion,
)
from ansible_collections.containers.podman.plugins.module_utils.podman.common import (
    lower_keys,
)
from ansible_collections.containers.podman.plugins.module_utils.podman.common import (
    generate_systemd,
)
from ansible_collections.containers.podman.plugins.module_utils.podman.common import (
    delete_systemd,
)
from ansible_collections.containers.podman.plugins.module_utils.podman.common import (
    diff_generic,
)
from ansible_collections.containers.podman.plugins.module_utils.podman.common import (
    createcommand,
)
from ansible_collections.containers.podman.plugins.module_utils.podman.quadlet import (
    create_quadlet_state,
)
from ansible_collections.containers.podman.plugins.module_utils.podman.quadlet import (
    ContainerQuadlet,
)


__metaclass__ = type

ARGUMENTS_SPEC_CONTAINER = dict(
    name=dict(required=True, type="str"),
    executable=dict(default="podman", type="str"),
    state=dict(
        type="str",
        default="started",
        choices=["absent", "present", "stopped", "started", "created", "quadlet"],
    ),
    image=dict(type="str"),
    annotation=dict(type="dict"),
    arch=dict(type="str"),
    attach=dict(type="list", elements="str", choices=["stdout", "stderr", "stdin"]),
    authfile=dict(type="path"),
    blkio_weight=dict(type="int"),
    blkio_weight_device=dict(type="dict"),
    cap_add=dict(type="list", elements="str", aliases=["capabilities"]),
    cap_drop=dict(type="list", elements="str"),
    cgroup_conf=dict(type="dict"),
    cgroup_parent=dict(type="path"),
    cgroupns=dict(type="str"),
    cgroups=dict(type="str"),
    chrootdirs=dict(type="str"),
    cidfile=dict(type="path"),
    cmd_args=dict(type="list", elements="str"),
    conmon_pidfile=dict(type="path"),
    command=dict(type="raw"),
    cpu_period=dict(type="int"),
    cpu_quota=dict(type="int"),
    cpu_rt_period=dict(type="int"),
    cpu_rt_runtime=dict(type="int"),
    cpu_shares=dict(type="int"),
    cpus=dict(type="str"),
    cpuset_cpus=dict(type="str"),
    cpuset_mems=dict(type="str"),
    decryption_key=dict(type="str", no_log=False),
    delete_depend=dict(type="bool"),
    delete_time=dict(type="str"),
    delete_volumes=dict(type="bool"),
    detach=dict(type="bool", default=True),
    debug=dict(type="bool", default=False),
    detach_keys=dict(type="str", no_log=False),
    device=dict(type="list", elements="str"),
    device_cgroup_rule=dict(type="str"),
    device_read_bps=dict(type="list", elements="str"),
    device_read_iops=dict(type="list", elements="str"),
    device_write_bps=dict(type="list", elements="str"),
    device_write_iops=dict(type="list", elements="str"),
    dns=dict(type="list", elements="str", aliases=["dns_servers"]),
    dns_option=dict(type="str", aliases=["dns_opts"]),
    dns_search=dict(type="list", elements="str", aliases=["dns_search_domains"]),
    entrypoint=dict(type="str"),
    env=dict(type="dict"),
    env_file=dict(type="list", elements="path", aliases=["env_files"]),
    env_host=dict(type="bool"),
    env_merge=dict(type="dict"),
    etc_hosts=dict(type="dict", aliases=["add_hosts"]),
    expose=dict(type="list", elements="str", aliases=["exposed", "exposed_ports"]),
    force_restart=dict(type="bool", default=False, aliases=["restart"]),
    force_delete=dict(type="bool", default=True),
    generate_systemd=dict(type="dict", default={}),
    gidmap=dict(type="list", elements="str"),
    gpus=dict(type="str"),
    group_add=dict(type="list", elements="str", aliases=["groups"]),
    group_entry=dict(type="str"),
    healthcheck=dict(type="str", aliases=["health_cmd"]),
    healthcheck_interval=dict(type="str", aliases=["health_interval"]),
    healthcheck_retries=dict(type="int", aliases=["health_retries"]),
    healthcheck_start_period=dict(type="str", aliases=["health_start_period"]),
    health_startup_cmd=dict(type="str"),
    health_startup_interval=dict(type="str"),
    health_startup_retries=dict(type="int"),
    health_startup_success=dict(type="int"),
    health_startup_timeout=dict(type="str"),
    healthcheck_timeout=dict(type="str", aliases=["health_timeout"]),
    healthcheck_failure_action=dict(
        type="str",
        choices=["none", "kill", "restart", "stop"],
        aliases=["health_on_failure"],
    ),
    hooks_dir=dict(type="list", elements="str"),
    hostname=dict(type="str"),
    hostuser=dict(type="str"),
    http_proxy=dict(type="bool"),
    image_volume=dict(type="str", choices=["bind", "tmpfs", "ignore"]),
    image_strict=dict(type="bool", default=False),
    init=dict(type="bool"),
    init_ctr=dict(type="str", choices=["once", "always"]),
    init_path=dict(type="str"),
    interactive=dict(type="bool"),
    ip=dict(type="str"),
    ip6=dict(type="str"),
    ipc=dict(type="str", aliases=["ipc_mode"]),
    kernel_memory=dict(type="str"),
    label=dict(type="dict", aliases=["labels"]),
    label_file=dict(type="str"),
    log_driver=dict(type="str", choices=["k8s-file", "journald", "json-file"]),
    log_level=dict(type="str", choices=["debug", "info", "warn", "error", "fatal", "panic"]),
    log_opt=dict(
        type="dict",
        aliases=["log_options"],
        options=dict(max_size=dict(type="str"), path=dict(type="str"), tag=dict(type="str")),
    ),
    mac_address=dict(type="str"),
    memory=dict(type="str"),
    memory_reservation=dict(type="str"),
    memory_swap=dict(type="str"),
    memory_swappiness=dict(type="int"),
    mount=dict(type="list", elements="str", aliases=["mounts"]),
    network=dict(type="list", elements="str", aliases=["net", "network_mode"]),
    network_aliases=dict(type="list", elements="str", aliases=["network_alias"]),
    no_healthcheck=dict(type="bool"),
    no_hosts=dict(type="bool"),
    oom_kill_disable=dict(type="bool"),
    oom_score_adj=dict(type="int"),
    os=dict(type="str"),
    passwd=dict(type="bool", no_log=False),
    passwd_entry=dict(type="str", no_log=False),
    personality=dict(type="str"),
    pid=dict(type="str", aliases=["pid_mode"]),
    pid_file=dict(type="path"),
    pids_limit=dict(type="str"),
    platform=dict(type="str"),
    pod=dict(type="str"),
    pod_id_file=dict(type="path"),
    preserve_fd=dict(type="list", elements="str"),
    preserve_fds=dict(type="str"),
    privileged=dict(type="bool"),
    publish=dict(type="list", elements="str", aliases=["ports", "published", "published_ports"]),
    publish_all=dict(type="bool"),
    pull=dict(type="str", choices=["always", "missing", "never", "newer"]),
    quadlet_dir=dict(type="path"),
    quadlet_filename=dict(type="str"),
    quadlet_file_mode=dict(type="raw"),
    quadlet_options=dict(type="list", elements="str"),
    rdt_class=dict(type="str"),
    read_only=dict(type="bool"),
    read_only_tmpfs=dict(type="bool"),
    recreate=dict(type="bool", default=False),
    requires=dict(type="list", elements="str"),
    restart_policy=dict(type="str"),
    restart_time=dict(type="str"),
    retry=dict(type="int"),
    retry_delay=dict(type="str"),
    rm=dict(type="bool", aliases=["remove", "auto_remove"]),
    rmi=dict(type="bool"),
    rootfs=dict(type="bool"),
    seccomp_policy=dict(type="str"),
    secrets=dict(type="list", elements="str", no_log=True),
    sdnotify=dict(type="str"),
    security_opt=dict(type="list", elements="str"),
    shm_size=dict(type="str"),
    shm_size_systemd=dict(type="str"),
    sig_proxy=dict(type="bool"),
    stop_signal=dict(type="int"),
    stop_timeout=dict(type="int"),
    stop_time=dict(type="str"),
    subgidname=dict(type="str"),
    subuidname=dict(type="str"),
    sysctl=dict(type="dict"),
    systemd=dict(type="str"),
    timeout=dict(type="int"),
    timezone=dict(type="str"),
    tls_verify=dict(type="bool"),
    tmpfs=dict(type="dict"),
    tty=dict(type="bool"),
    uidmap=dict(type="list", elements="str"),
    ulimit=dict(type="list", elements="str", aliases=["ulimits"]),
    umask=dict(type="str"),
    unsetenv=dict(type="list", elements="str"),
    unsetenv_all=dict(type="bool"),
    user=dict(type="str"),
    userns=dict(type="str", aliases=["userns_mode"]),
    uts=dict(type="str"),
    variant=dict(type="str"),
    volume=dict(type="list", elements="str", aliases=["volumes"]),
    volumes_from=dict(type="list", elements="str"),
    workdir=dict(type="str", aliases=["working_dir"]),
)


def init_options():
    default = {}
    opts = ARGUMENTS_SPEC_CONTAINER
    for k, v in opts.items():
        if "default" in v:
            default[k] = v["default"]
        else:
            default[k] = None
    return default


def update_options(opts_dict, container):
    def to_bool(x):
        return str(x).lower() not in ["no", "false"]

    aliases = {}
    for k, v in ARGUMENTS_SPEC_CONTAINER.items():
        if "aliases" in v:
            for alias in v["aliases"]:
                aliases[alias] = k
    for k in list(container):
        if k in aliases:
            key = aliases[k]
            container[key] = container.pop(k)
        else:
            key = k
        if ARGUMENTS_SPEC_CONTAINER[key]["type"] == "list" and not isinstance(container[key], list):
            opts_dict[key] = [container[key]]
        elif ARGUMENTS_SPEC_CONTAINER[key]["type"] == "bool" and not isinstance(container[key], bool):
            opts_dict[key] = to_bool(container[key])
        elif ARGUMENTS_SPEC_CONTAINER[key]["type"] == "int" and not isinstance(container[key], int):
            opts_dict[key] = int(container[key])
        else:
            opts_dict[key] = container[key]

    return opts_dict


def set_container_opts(input_vars):
    default_options_templ = init_options()
    options_dict = update_options(default_options_templ, input_vars)
    return options_dict


class PodmanModuleParams:
    """Creates list of arguments for podman CLI command.

    Arguments:
        action {str} -- action type from 'run', 'stop', 'create', 'delete',
                        'start', 'restart'
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
        if self.action in ["start", "stop", "delete", "restart"]:
            return self.start_stop_delete()
        if self.action in ["create", "run"]:
            cmd = [self.action, "--name", self.params["name"]]
            all_param_methods = [
                func for func in dir(self) if callable(getattr(self, func)) and func.startswith("addparam")
            ]
            params_set = (i for i in self.params if self.params[i] is not None)
            for param in params_set:
                func_name = "_".join(["addparam", param])
                if func_name in all_param_methods:
                    cmd = getattr(self, func_name)(cmd)
            cmd.append(self.params["image"])
            if self.params["command"]:
                if isinstance(self.params["command"], list):
                    cmd += self.params["command"]
                else:
                    cmd += self.params["command"].split()
            return [to_bytes(i, errors="surrogate_or_strict") for i in cmd]

    def start_stop_delete(self):

        def complete_params(cmd):
            if self.params["attach"] and self.action == "start":
                cmd.append("--attach")
            if self.params["detach"] is False and self.action == "start" and "--attach" not in cmd:
                cmd.append("--attach")
            if self.params["detach_keys"] and self.action == "start":
                cmd += ["--detach-keys", self.params["detach_keys"]]
            if self.params["sig_proxy"] and self.action == "start":
                cmd.append("--sig-proxy")
            if self.params["stop_time"] and self.action == "stop":
                cmd += ["--time", self.params["stop_time"]]
            if self.params["restart_time"] and self.action == "restart":
                cmd += ["--time", self.params["restart_time"]]
            if self.params["delete_depend"] and self.action == "delete":
                cmd.append("--depend")
            if self.params["delete_time"] and self.action == "delete":
                cmd += ["--time", self.params["delete_time"]]
            if self.params["delete_volumes"] and self.action == "delete":
                cmd.append("--volumes")
            if self.params["force_delete"] and self.action == "delete":
                cmd.append("--force")
            return cmd

        if self.action in ["stop", "start", "restart"]:
            cmd = complete_params([self.action]) + [self.params["name"]]
            return [to_bytes(i, errors="surrogate_or_strict") for i in cmd]

        if self.action == "delete":
            cmd = complete_params(["rm"]) + [self.params["name"]]
            return [to_bytes(i, errors="surrogate_or_strict") for i in cmd]

    def check_version(self, param, minv=None, maxv=None):
        if minv and LooseVersion(minv) > LooseVersion(self.podman_version):
            self.module.fail_json(
                msg="Parameter %s is supported from podman "
                "version %s only! Current version is %s" % (param, minv, self.podman_version)
            )
        if maxv and LooseVersion(maxv) < LooseVersion(self.podman_version):
            self.module.fail_json(
                msg="Parameter %s is supported till podman "
                "version %s only! Current version is %s" % (param, minv, self.podman_version)
            )

    def addparam_annotation(self, c):
        for annotate in self.params["annotation"].items():
            c += ["--annotation", "=".join(annotate)]
        return c

    def addparam_arch(self, c):
        return c + ["--arch=%s" % self.params["arch"]]

    def addparam_attach(self, c):
        for attach in self.params["attach"]:
            c += ["--attach=%s" % attach]
        return c

    def addparam_authfile(self, c):
        return c + ["--authfile", self.params["authfile"]]

    def addparam_blkio_weight(self, c):
        return c + ["--blkio-weight", self.params["blkio_weight"]]

    def addparam_blkio_weight_device(self, c):
        for blkio in self.params["blkio_weight_device"].items():
            c += ["--blkio-weight-device", ":".join(blkio)]
        return c

    def addparam_cap_add(self, c):
        for cap_add in self.params["cap_add"]:
            c += ["--cap-add", cap_add]
        return c

    def addparam_cap_drop(self, c):
        for cap_drop in self.params["cap_drop"]:
            c += ["--cap-drop", cap_drop]
        return c

    def addparam_cgroups(self, c):
        self.check_version("--cgroups", minv="1.6.0")
        return c + ["--cgroups=%s" % self.params["cgroups"]]

    def addparam_cgroupns(self, c):
        self.check_version("--cgroupns", minv="1.6.2")
        return c + ["--cgroupns=%s" % self.params["cgroupns"]]

    def addparam_cgroup_parent(self, c):
        return c + ["--cgroup-parent", self.params["cgroup_parent"]]

    def addparam_cgroup_conf(self, c):
        for cgroup in self.params["cgroup_conf"].items():
            c += ["--cgroup-conf=%s" % "=".join([str(i) for i in cgroup])]
        return c

    def addparam_chrootdirs(self, c):
        return c + ["--chrootdirs", self.params["chrootdirs"]]

    def addparam_cidfile(self, c):
        return c + ["--cidfile", self.params["cidfile"]]

    def addparam_conmon_pidfile(self, c):
        return c + ["--conmon-pidfile", self.params["conmon_pidfile"]]

    def addparam_cpu_period(self, c):
        return c + ["--cpu-period", self.params["cpu_period"]]

    def addparam_cpu_quota(self, c):
        return c + ["--cpu-quota", self.params["cpu_quota"]]

    def addparam_cpu_rt_period(self, c):
        return c + ["--cpu-rt-period", self.params["cpu_rt_period"]]

    def addparam_cpu_rt_runtime(self, c):
        return c + ["--cpu-rt-runtime", self.params["cpu_rt_runtime"]]

    def addparam_cpu_shares(self, c):
        return c + ["--cpu-shares", self.params["cpu_shares"]]

    def addparam_cpus(self, c):
        return c + ["--cpus", self.params["cpus"]]

    def addparam_cpuset_cpus(self, c):
        return c + ["--cpuset-cpus", self.params["cpuset_cpus"]]

    def addparam_cpuset_mems(self, c):
        return c + ["--cpuset-mems", self.params["cpuset_mems"]]

    def addparam_decryption_key(self, c):
        return c + ["--decryption-key=%s" % self.params["decryption_key"]]

    def addparam_detach(self, c):
        # Remove detach from create command and don't set if attach is true
        if self.action == "create" or self.params["attach"]:
            return c
        return c + ["--detach=%s" % self.params["detach"]]

    def addparam_detach_keys(self, c):
        return c + ["--detach-keys", self.params["detach_keys"]]

    def addparam_device(self, c):
        for dev in self.params["device"]:
            c += ["--device", dev]
        return c

    def addparam_device_cgroup_rule(self, c):
        return c + ["--device-cgroup-rule=%s" % self.params["device_cgroup_rule"]]

    def addparam_device_read_bps(self, c):
        for dev in self.params["device_read_bps"]:
            c += ["--device-read-bps", dev]
        return c

    def addparam_device_read_iops(self, c):
        for dev in self.params["device_read_iops"]:
            c += ["--device-read-iops", dev]
        return c

    def addparam_device_write_bps(self, c):
        for dev in self.params["device_write_bps"]:
            c += ["--device-write-bps", dev]
        return c

    def addparam_device_write_iops(self, c):
        for dev in self.params["device_write_iops"]:
            c += ["--device-write-iops", dev]
        return c

    def addparam_dns(self, c):
        return c + ["--dns", ",".join(self.params["dns"])]

    def addparam_dns_option(self, c):
        return c + ["--dns-option", self.params["dns_option"]]

    def addparam_dns_search(self, c):
        for search in self.params["dns_search"]:
            c += ["--dns-search", search]
        return c

    def addparam_entrypoint(self, c):
        return c + ["--entrypoint=%s" % self.params["entrypoint"]]

    def addparam_env(self, c):
        for env_value in self.params["env"].items():
            c += [
                "--env",
                b"=".join([to_bytes(k, errors="surrogate_or_strict") for k in env_value]),
            ]
        return c

    def addparam_env_file(self, c):
        for env_file in self.params["env_file"]:
            c += ["--env-file", env_file]
        return c

    def addparam_env_host(self, c):
        self.check_version("--env-host", minv="1.5.0")
        return c + ["--env-host=%s" % self.params["env_host"]]

    # Exception for etc_hosts and add-host
    def addparam_etc_hosts(self, c):
        for host_ip in self.params["etc_hosts"].items():
            c += ["--add-host", ":".join(host_ip)]
        return c

    def addparam_env_merge(self, c):
        for env_merge in self.params["env_merge"].items():
            c += [
                "--env-merge",
                b"=".join([to_bytes(k, errors="surrogate_or_strict") for k in env_merge]),
            ]
        return c

    def addparam_expose(self, c):
        for exp in self.params["expose"]:
            c += ["--expose", exp]
        return c

    def addparam_gidmap(self, c):
        for gidmap in self.params["gidmap"]:
            c += ["--gidmap", gidmap]
        return c

    def addparam_gpus(self, c):
        return c + ["--gpus", self.params["gpus"]]

    def addparam_group_add(self, c):
        for g in self.params["group_add"]:
            c += ["--group-add", g]
        return c

    def addparam_group_entry(self, c):
        return c + ["--group-entry", self.params["group_entry"]]

    # Exception for healthcheck and healthcheck-command
    def addparam_healthcheck(self, c):
        return c + ["--healthcheck-command", self.params["healthcheck"]]

    def addparam_healthcheck_interval(self, c):
        return c + ["--healthcheck-interval", self.params["healthcheck_interval"]]

    def addparam_healthcheck_retries(self, c):
        return c + ["--healthcheck-retries", self.params["healthcheck_retries"]]

    def addparam_healthcheck_start_period(self, c):
        return c + [
            "--healthcheck-start-period",
            self.params["healthcheck_start_period"],
        ]

    def addparam_health_startup_cmd(self, c):
        return c + ["--health-startup-cmd", self.params["health_startup_cmd"]]

    def addparam_health_startup_interval(self, c):
        return c + ["--health-startup-interval", self.params["health_startup_interval"]]

    def addparam_healthcheck_timeout(self, c):
        return c + ["--healthcheck-timeout", self.params["healthcheck_timeout"]]

    def addparam_health_startup_retries(self, c):
        return c + ["--health-startup-retries", self.params["health_startup_retries"]]

    def addparam_health_startup_success(self, c):
        return c + ["--health-startup-success", self.params["health_startup_success"]]

    def addparam_health_startup_timeout(self, c):
        return c + ["--health-startup-timeout", self.params["health_startup_timeout"]]

    def addparam_healthcheck_failure_action(self, c):
        return c + ["--health-on-failure", self.params["healthcheck_failure_action"]]

    def addparam_hooks_dir(self, c):
        for hook_dir in self.params["hooks_dir"]:
            c += ["--hooks-dir=%s" % hook_dir]
        return c

    def addparam_hostname(self, c):
        return c + ["--hostname", self.params["hostname"]]

    def addparam_hostuser(self, c):
        return c + ["--hostuser", self.params["hostuser"]]

    def addparam_http_proxy(self, c):
        return c + ["--http-proxy=%s" % self.params["http_proxy"]]

    def addparam_image_volume(self, c):
        return c + ["--image-volume", self.params["image_volume"]]

    def addparam_init(self, c):
        if self.params["init"]:
            c += ["--init"]
        return c

    def addparam_init_path(self, c):
        return c + ["--init-path", self.params["init_path"]]

    def addparam_init_ctr(self, c):
        return c + ["--init-ctr", self.params["init_ctr"]]

    def addparam_interactive(self, c):
        return c + ["--interactive=%s" % self.params["interactive"]]

    def addparam_ip(self, c):
        return c + ["--ip", self.params["ip"]]

    def addparam_ip6(self, c):
        return c + ["--ip6", self.params["ip6"]]

    def addparam_ipc(self, c):
        return c + ["--ipc", self.params["ipc"]]

    def addparam_kernel_memory(self, c):
        return c + ["--kernel-memory", self.params["kernel_memory"]]

    def addparam_label(self, c):
        for label in self.params["label"].items():
            c += [
                "--label",
                b"=".join([to_bytes(la, errors="surrogate_or_strict") for la in label]),
            ]
        return c

    def addparam_label_file(self, c):
        return c + ["--label-file", self.params["label_file"]]

    def addparam_log_driver(self, c):
        return c + ["--log-driver", self.params["log_driver"]]

    def addparam_log_opt(self, c):
        for k, v in self.params["log_opt"].items():
            if v is not None:
                c += [
                    "--log-opt",
                    b"=".join(
                        [
                            to_bytes(
                                k.replace("max_size", "max-size"),
                                errors="surrogate_or_strict",
                            ),
                            to_bytes(v, errors="surrogate_or_strict"),
                        ]
                    ),
                ]
        return c

    def addparam_log_level(self, c):
        return c + ["--log-level", self.params["log_level"]]

    def addparam_mac_address(self, c):
        return c + ["--mac-address", self.params["mac_address"]]

    def addparam_memory(self, c):
        return c + ["--memory", self.params["memory"]]

    def addparam_memory_reservation(self, c):
        return c + ["--memory-reservation", self.params["memory_reservation"]]

    def addparam_memory_swap(self, c):
        return c + ["--memory-swap", self.params["memory_swap"]]

    def addparam_memory_swappiness(self, c):
        return c + ["--memory-swappiness", self.params["memory_swappiness"]]

    def addparam_mount(self, c):
        for mnt in self.params["mount"]:
            if mnt:
                c += ["--mount", mnt]
        return c

    def addparam_network(self, c):
        if LooseVersion(self.podman_version) >= LooseVersion("4.0.0"):
            for net in self.params["network"]:
                c += ["--network", net]
            return c
        return c + ["--network", ",".join(self.params["network"])]

    # Exception for network_aliases and network-alias
    def addparam_network_aliases(self, c):
        for alias in self.params["network_aliases"]:
            c += ["--network-alias", alias]
        return c

    def addparam_no_hosts(self, c):
        return c + ["--no-hosts=%s" % self.params["no_hosts"]]

    def addparam_no_healthcheck(self, c):
        if self.params["no_healthcheck"]:
            c += ["--no-healthcheck"]
        return c

    def addparam_oom_kill_disable(self, c):
        return c + ["--oom-kill-disable=%s" % self.params["oom_kill_disable"]]

    def addparam_oom_score_adj(self, c):
        return c + ["--oom-score-adj", self.params["oom_score_adj"]]

    def addparam_os(self, c):
        return c + ["--os", self.params["os"]]

    def addparam_passwd(self, c):
        if self.params["passwd"]:
            c += ["--passwd"]
        return c

    def addparam_passwd_entry(self, c):
        return c + ["--passwd-entry", self.params["passwd_entry"]]

    def addparam_personality(self, c):
        return c + ["--personality", self.params["personality"]]

    def addparam_pid(self, c):
        return c + ["--pid", self.params["pid"]]

    def addparam_pid_file(self, c):
        return c + ["--pid-file", self.params["pid_file"]]

    def addparam_pids_limit(self, c):
        return c + ["--pids-limit", self.params["pids_limit"]]

    def addparam_platform(self, c):
        return c + ["--platform", self.params["platform"]]

    def addparam_pod(self, c):
        return c + ["--pod", self.params["pod"]]

    def addparam_pod_id_file(self, c):
        return c + ["--pod-id-file", self.params["pod_id_file"]]

    def addparam_preserve_fd(self, c):
        for fd in self.params["preserve_fd"]:
            c += ["--preserve-fd", fd]
        return c

    def addparam_preserve_fds(self, c):
        return c + ["--preserve-fds", self.params["preserve_fds"]]

    def addparam_privileged(self, c):
        return c + ["--privileged=%s" % self.params["privileged"]]

    def addparam_publish(self, c):
        for pub in self.params["publish"]:
            c += ["--publish", pub]
        return c

    def addparam_publish_all(self, c):
        return c + ["--publish-all=%s" % self.params["publish_all"]]

    def addparam_pull(self, c):
        return c + ["--pull=%s" % self.params["pull"]]

    def addparam_rdt_class(self, c):
        return c + ["--rdt-class", self.params["rdt_class"]]

    def addparam_read_only(self, c):
        return c + ["--read-only=%s" % self.params["read_only"]]

    def addparam_read_only_tmpfs(self, c):
        return c + ["--read-only-tmpfs=%s" % self.params["read_only_tmpfs"]]

    def addparam_requires(self, c):
        return c + ["--requires", ",".join(self.params["requires"])]

    # Exception for restart_policy and restart
    def addparam_restart_policy(self, c):
        return c + ["--restart=%s" % self.params["restart_policy"]]

    def addparam_retry(self, c):
        return c + ["--retry", self.params["retry"]]

    def addparam_retry_delay(self, c):
        return c + ["--retry-delay", self.params["retry_delay"]]

    def addparam_rm(self, c):
        if self.params["rm"]:
            c += ["--rm"]
        return c

    def addparam_rmi(self, c):
        if self.params["rmi"]:
            c += ["--rmi"]
        return c

    def addparam_rootfs(self, c):
        return c + ["--rootfs=%s" % self.params["rootfs"]]

    def addparam_sdnotify(self, c):
        return c + ["--sdnotify=%s" % self.params["sdnotify"]]

    def addparam_seccomp_policy(self, c):
        return c + ["--seccomp-policy", self.params["seccomp_policy"]]

    # Exception for secrets and secret
    def addparam_secrets(self, c):
        for secret in self.params["secrets"]:
            c += ["--secret", secret]
        return c

    def addparam_security_opt(self, c):
        for secopt in self.params["security_opt"]:
            c += ["--security-opt", secopt]
        return c

    def addparam_shm_size(self, c):
        return c + ["--shm-size", self.params["shm_size"]]

    def addparam_shm_size_systemd(self, c):
        return c + ["--shm-size-systemd", self.params["shm_size_systemd"]]

    def addparam_sig_proxy(self, c):
        return c + ["--sig-proxy=%s" % self.params["sig_proxy"]]

    def addparam_stop_signal(self, c):
        return c + ["--stop-signal", self.params["stop_signal"]]

    def addparam_stop_timeout(self, c):
        return c + ["--stop-timeout", self.params["stop_timeout"]]

    def addparam_subgidname(self, c):
        return c + ["--subgidname", self.params["subgidname"]]

    def addparam_subuidname(self, c):
        return c + ["--subuidname", self.params["subuidname"]]

    def addparam_sysctl(self, c):
        for sysctl in self.params["sysctl"].items():
            c += [
                "--sysctl",
                b"=".join([to_bytes(k, errors="surrogate_or_strict") for k in sysctl]),
            ]
        return c

    def addparam_systemd(self, c):
        return c + ["--systemd=%s" % str(self.params["systemd"]).lower()]

    def addparam_timeout(self, c):
        return c + ["--timeout", self.params["timeout"]]

    # Exception for timezone and tz
    def addparam_timezone(self, c):
        return c + ["--tz=%s" % self.params["timezone"]]

    def addparam_tls_verify(self, c):
        return c + ["--tls-verify=%s" % self.params["tls_verify"]]

    def addparam_tmpfs(self, c):
        for tmpfs in self.params["tmpfs"].items():
            c += ["--tmpfs", ":".join(tmpfs)]
        return c

    def addparam_tty(self, c):
        return c + ["--tty=%s" % self.params["tty"]]

    def addparam_uidmap(self, c):
        for uidmap in self.params["uidmap"]:
            c += ["--uidmap", uidmap]
        return c

    def addparam_ulimit(self, c):
        for u in self.params["ulimit"]:
            c += ["--ulimit", u]
        return c

    def addparam_umask(self, c):
        return c + ["--umask", self.params["umask"]]

    def addparam_unsetenv(self, c):
        for unsetenv in self.params["unsetenv"]:
            c += ["--unsetenv", unsetenv]
        return c

    def addparam_unsetenv_all(self, c):
        if self.params["unsetenv_all"]:
            c += ["--unsetenv-all"]
        return c

    def addparam_user(self, c):
        return c + ["--user", self.params["user"]]

    def addparam_userns(self, c):
        return c + ["--userns", self.params["userns"]]

    def addparam_uts(self, c):
        return c + ["--uts", self.params["uts"]]

    def addparam_variant(self, c):
        return c + ["--variant", self.params["variant"]]

    def addparam_volume(self, c):
        for vol in self.params["volume"]:
            if vol:
                c += ["--volume", vol]
        return c

    def addparam_volumes_from(self, c):
        for vol in self.params["volumes_from"]:
            c += ["--volumes-from", vol]
        return c

    def addparam_workdir(self, c):
        return c + ["--workdir", self.params["workdir"]]

    # Add your own args for podman command
    def addparam_cmd_args(self, c):
        return c + self.params["cmd_args"]


class PodmanDefaults:
    def __init__(self, image_info, podman_version):
        self.version = podman_version
        self.image_info = image_info
        self.defaults = {
            "detach": True,
            "log_level": "error",
            "tty": False,
        }

    def default_dict(self):
        # make here any changes to self.defaults related to podman version
        # https://github.com/containers/libpod/pull/5669
        if LooseVersion(self.version) >= LooseVersion("1.8.0") and LooseVersion(self.version) < LooseVersion("1.9.0"):
            self.defaults["cpu_shares"] = 1024
        if LooseVersion(self.version) >= LooseVersion("3.0.0"):
            self.defaults["log_level"] = "warning"
        return self.defaults


class PodmanContainerDiff:
    def __init__(self, module, module_params, info, image_info, podman_version):
        self.module = module
        self.module_params = module_params
        self.version = podman_version
        self.default_dict = None
        self.info = lower_keys(info)
        self.image_info = lower_keys(image_info)
        self.params = self.defaultize()
        self.diff = {"before": {}, "after": {}}
        self.non_idempotent = {}

    def defaultize(self):
        params_with_defaults = {}
        self.default_dict = PodmanDefaults(self.image_info, self.version).default_dict()
        for p in self.module_params:
            if self.module_params[p] is None and p in self.default_dict:
                params_with_defaults[p] = self.default_dict[p]
            else:
                params_with_defaults[p] = self.module_params[p]
        return params_with_defaults

    def _diff_update_and_compare(self, param_name, before, after):
        if before != after:
            self.diff["before"].update({param_name: before})
            self.diff["after"].update({param_name: after})
            return True
        return False

    def _diff_generic(self, module_arg, cmd_arg, boolean_type=False):
        """
        Generic diff function for module arguments from CreateCommand
        in Podman inspection output.

        Args:
            module_arg (str): module argument name
            cmd_arg (str): command line argument name
            boolean_type (bool): if True, then argument is boolean type

        Returns:
            bool: True if there is a difference, False otherwise

        """
        info_config = self.info["config"]
        before, after = diff_generic(self.params, info_config, module_arg, cmd_arg, boolean_type)
        return self._diff_update_and_compare(module_arg, before, after)

    def diffparam_annotation(self):
        before = self.info["config"]["annotations"] or {}
        after = before.copy()
        if self.module_params["annotation"] is not None:
            after.update(self.params["annotation"])
        return self._diff_update_and_compare("annotation", before, after)

    def diffparam_arch(self):
        return self._diff_generic("arch", "--arch")

    def diffparam_authfile(self):
        return self._diff_generic("authfile", "--authfile")

    def diffparam_blkio_weight(self):
        return self._diff_generic("blkio_weight", "--blkio-weight")

    def diffparam_blkio_weight_device(self):
        return self._diff_generic("blkio_weight_device", "--blkio-weight-device")

    def diffparam_cap_add(self):
        before = self.info["effectivecaps"] or []
        before = [i.lower() for i in before]
        after = []
        if self.module_params["cap_add"] is not None:
            for cap in self.module_params["cap_add"]:
                cap = cap.lower()
                cap = cap if cap.startswith("cap_") else "cap_" + cap
                after.append(cap)
        after += before
        before, after = sorted(list(set(before))), sorted(list(set(after)))
        return self._diff_update_and_compare("cap_add", before, after)

    def diffparam_cap_drop(self):
        before = self.info["effectivecaps"] or []
        before = [i.lower() for i in before]
        after = before[:]
        if self.module_params["cap_drop"] is not None:
            for cap in self.module_params["cap_drop"]:
                cap = cap.lower()
                cap = cap if cap.startswith("cap_") else "cap_" + cap
                if cap in after:
                    after.remove(cap)
        before, after = sorted(list(set(before))), sorted(list(set(after)))
        return self._diff_update_and_compare("cap_drop", before, after)

    def diffparam_cgroup_conf(self):
        return self._diff_generic("cgroup_conf", "--cgroup-conf")

    def diffparam_cgroup_parent(self):
        return self._diff_generic("cgroup_parent", "--cgroup-parent")

    def diffparam_cgroupns(self):
        return self._diff_generic("cgroupns", "--cgroupns")

    # Disabling idemotency check for cgroups as it's added by systemd generator
    # https://github.com/containers/ansible-podman-collections/issues/775
    # def diffparam_cgroups(self):
    #     return self._diff_generic('cgroups', '--cgroups')

    def diffparam_chrootdirs(self):
        return self._diff_generic("chrootdirs", "--chrootdirs")

    # Disabling idemotency check for cidfile as it's added by systemd generator
    # https://github.com/containers/ansible-podman-collections/issues/775
    # def diffparam_cidfile(self):
    #     return self._diff_generic('cidfile', '--cidfile')

    def diffparam_command(self):
        def _join_quotes(com_list):
            result = []
            buffer = []
            in_quotes = False

            for item in com_list:
                if item.startswith('"') and not in_quotes:
                    buffer.append(item)
                    in_quotes = True
                elif item.endswith('"') and in_quotes:
                    buffer.append(item)
                    result.append(" ".join(buffer).strip('"'))
                    buffer = []
                    in_quotes = False
                elif in_quotes:
                    buffer.append(item)
                else:
                    result.append(item)
            if in_quotes:
                result.extend(buffer)

            return result

        # TODO(sshnaidm): to inspect image to get the default command
        if self.module_params["command"] is not None:
            before = self.info["config"]["cmd"]
            after = self.params["command"]
            if before:
                before = _join_quotes(before)
            if isinstance(after, list):
                after = [str(i) for i in after]
            if isinstance(after, str):
                after = shlex.split(after)
            return self._diff_update_and_compare("command", before, after)
        return False

    def diffparam_conmon_pidfile(self):
        return self._diff_generic("conmon_pidfile", "--conmon-pidfile")

    def diffparam_cpu_period(self):
        return self._diff_generic("cpu_period", "--cpu-period")

    def diffparam_cpu_quota(self):
        return self._diff_generic("cpu_quota", "--cpu-quota")

    def diffparam_cpu_rt_period(self):
        return self._diff_generic("cpu_rt_period", "--cpu-rt-period")

    def diffparam_cpu_rt_runtime(self):
        return self._diff_generic("cpu_rt_runtime", "--cpu-rt-runtime")

    def diffparam_cpu_shares(self):
        return self._diff_generic("cpu_shares", "--cpu-shares")

    def diffparam_cpus(self):
        return self._diff_generic("cpus", "--cpus")

    def diffparam_cpuset_cpus(self):
        return self._diff_generic("cpuset_cpus", "--cpuset-cpus")

    def diffparam_cpuset_mems(self):
        return self._diff_generic("cpuset_mems", "--cpuset-mems")

    def diffparam_decryption_key(self):
        return self._diff_generic("decryption_key", "--decryption-key")

    def diffparam_device(self):
        return self._diff_generic("device", "--device")

    def diffparam_device_cgroup_rule(self):
        return self._diff_generic("device_cgroup_rule", "--device-cgroup-rule")

    def diffparam_device_read_bps(self):
        return self._diff_generic("device_read_bps", "--device-read-bps")

    def diffparam_device_read_iops(self):
        return self._diff_generic("device_read_iops", "--device-read-iops")

    def diffparam_device_write_bps(self):
        return self._diff_generic("device_write_bps", "--device-write-bps")

    def diffparam_device_write_iops(self):
        return self._diff_generic("device_write_iops", "--device-write-iops")

    def diffparam_dns(self):
        return self._diff_generic("dns", "--dns")

    def diffparam_dns_option(self):
        return self._diff_generic("dns_option", "--dns-option")

    def diffparam_dns_search(self):
        return self._diff_generic("dns_search", "--dns-search")

    def diffparam_env(self):
        return self._diff_generic("env", "--env")

    def diffparam_env_file(self):
        return self._diff_generic("env_file", "--env-file")

    def diffparam_env_merge(self):
        return self._diff_generic("env_merge", "--env-merge")

    def diffparam_env_host(self):
        return self._diff_generic("env_host", "--env-host")

    def diffparam_etc_hosts(self):
        if self.info["hostconfig"]["extrahosts"]:
            before = dict([i.split(":", 1) for i in self.info["hostconfig"]["extrahosts"]])
        else:
            before = {}
        after = self.params["etc_hosts"] or {}
        return self._diff_update_and_compare("etc_hosts", before, after)

    def diffparam_expose(self):
        return self._diff_generic("expose", "--expose")

    def diffparam_gidmap(self):
        return self._diff_generic("gidmap", "--gidmap")

    def diffparam_gpus(self):
        return self._diff_generic("gpus", "--gpus")

    def diffparam_group_add(self):
        return self._diff_generic("group_add", "--group-add")

    def diffparam_group_entry(self):
        return self._diff_generic("group_entry", "--group-entry")

    # Healthcheck is only defined in container config if a healthcheck
    # was configured; otherwise the config key isn't part of the config.
    def diffparam_healthcheck(self):
        before = ""
        if "healthcheck" in self.info["config"]:
            # the "test" key is a list of 2 items where the first one is
            # "CMD-SHELL" and the second one is the actual healthcheck command.
            if len(self.info["config"]["healthcheck"]["test"]) > 1:
                before = self.info["config"]["healthcheck"]["test"][1]
        after = self.params["healthcheck"] or before
        return self._diff_update_and_compare("healthcheck", before, after)

    def diffparam_healthcheck_failure_action(self):
        if "healthcheckonfailureaction" in self.info["config"]:
            before = self.info["config"]["healthcheckonfailureaction"]
        else:
            before = ""
        after = self.params["healthcheck_failure_action"] or before
        return self._diff_update_and_compare("healthcheckonfailureaction", before, after)

    def diffparam_healthcheck_interval(self):
        return self._diff_generic("healthcheck_interval", "--healthcheck-interval")

    def diffparam_healthcheck_retries(self):
        return self._diff_generic("healthcheck_retries", "--healthcheck-retries")

    def diffparam_healthcheck_start_period(self):
        return self._diff_generic("healthcheck_start_period", "--healthcheck-start-period")

    def diffparam_health_startup_cmd(self):
        return self._diff_generic("health_startup_cmd", "--health-startup-cmd")

    def diffparam_health_startup_interval(self):
        return self._diff_generic("health_startup_interval", "--health-startup-interval")

    def diffparam_health_startup_retries(self):
        return self._diff_generic("health_startup_retries", "--health-startup-retries")

    def diffparam_health_startup_success(self):
        return self._diff_generic("health_startup_success", "--health-startup-success")

    def diffparam_health_startup_timeout(self):
        return self._diff_generic("health_startup_timeout", "--health-startup-timeout")

    def diffparam_healthcheck_timeout(self):
        return self._diff_generic("healthcheck_timeout", "--healthcheck-timeout")

    def diffparam_hooks_dir(self):
        return self._diff_generic("hooks_dir", "--hooks-dir")

    def diffparam_hostname(self):
        return self._diff_generic("hostname", "--hostname")

    def diffparam_hostuser(self):
        return self._diff_generic("hostuser", "--hostuser")

    def diffparam_http_proxy(self):
        return self._diff_generic("http_proxy", "--http-proxy")

    def diffparam_image(self):
        before_id = self.info["image"] or self.info["rootfs"]
        after_id = self.image_info["id"]
        if before_id == after_id:
            return self._diff_update_and_compare("image", before_id, after_id)
        is_rootfs = self.info["rootfs"] != "" or self.params["rootfs"]
        before = self.info["config"]["image"] or before_id
        after = self.params["image"]
        mode = self.params["image_strict"] or is_rootfs
        if mode is None or not mode:
            # In a idempotency 'lite mode' assume all images from different registries are the same
            before = before.replace(":latest", "")
            after = after.replace(":latest", "")
            before = before.split("/")[-1]
            after = after.split("/")[-1]
        else:
            return self._diff_update_and_compare("image", before_id, after_id)
        return self._diff_update_and_compare("image", before, after)

    def diffparam_image_volume(self):
        return self._diff_generic("image_volume", "--image-volume")

    def diffparam_init(self):
        return self._diff_generic("init", "--init", boolean_type=True)

    def diffparam_init_ctr(self):
        return self._diff_generic("init_ctr", "--init-ctr")

    def diffparam_init_path(self):
        return self._diff_generic("init_path", "--init-path")

    def diffparam_interactive(self):
        return self._diff_generic("interactive", "--interactive")

    def diffparam_ip(self):
        return self._diff_generic("ip", "--ip")

    def diffparam_ip6(self):
        return self._diff_generic("ip6", "--ip6")

    def diffparam_ipc(self):
        return self._diff_generic("ipc", "--ipc")

    def diffparam_label(self):
        before = self.info["config"]["labels"] or {}
        after = self.image_info.get("labels") or {}
        if self.params["label"]:
            after.update({str(k).lower(): str(v) for k, v in self.params["label"].items()})
        # Strip out labels that are coming from systemd files
        # https://github.com/containers/ansible-podman-collections/issues/276
        if "podman_systemd_unit" in before:
            after.pop("podman_systemd_unit", None)
            before.pop("podman_systemd_unit", None)
        return self._diff_update_and_compare("label", before, after)

    def diffparam_label_file(self):
        return self._diff_generic("label_file", "--label-file")

    def diffparam_log_driver(self):
        return self._diff_generic("log_driver", "--log-driver")

    def diffparam_log_opt(self):
        return self._diff_generic("log_opt", "--log-opt")

    def diffparam_mac_address(self):
        return self._diff_generic("mac_address", "--mac-address")

    def diffparam_memory(self):
        return self._diff_generic("memory", "--memory")

    def diffparam_memory_reservation(self):
        return self._diff_generic("memory_reservation", "--memory-reservation")

    def diffparam_memory_swap(self):
        return self._diff_generic("memory_swap", "--memory-swap")

    def diffparam_memory_swappiness(self):
        return self._diff_generic("memory_swappiness", "--memory-swappiness")

    def diffparam_mount(self):
        return self._diff_generic("mount", "--mount")

    def diffparam_network(self):
        return self._diff_generic("network", "--network")

    def diffparam_network_aliases(self):
        return self._diff_generic("network_aliases", "--network-alias")

    def diffparam_no_healthcheck(self):
        return self._diff_generic("no_healthcheck", "--no-healthcheck", boolean_type=True)

    def diffparam_no_hosts(self):
        return self._diff_generic("no_hosts", "--no-hosts")

    def diffparam_oom_kill_disable(self):
        return self._diff_generic("oom_kill_disable", "--oom-kill-disable")

    def diffparam_oom_score_adj(self):
        return self._diff_generic("oom_score_adj", "--oom-score-adj")

    def diffparam_os(self):
        return self._diff_generic("os", "--os")

    def diffparam_passwd(self):
        return self._diff_generic("passwd", "--passwd", boolean_type=True)

    def diffparam_passwd_entry(self):
        return self._diff_generic("passwd_entry", "--passwd-entry")

    def diffparam_personality(self):
        return self._diff_generic("personality", "--personality")

    def diffparam_pid(self):
        return self._diff_generic("pid", "--pid")

    def diffparam_pid_file(self):
        return self._diff_generic("pid_file", "--pid-file")

    def diffparam_pids_limit(self):
        return self._diff_generic("pids_limit", "--pids-limit")

    def diffparam_platform(self):
        return self._diff_generic("platform", "--platform")

    # def diffparam_pod(self):
    #     return self._diff_generic('pod', '--pod')

    # https://github.com/containers/ansible-podman-collections/issues/828
    # def diffparam_pod_id_file(self):
    #     return self._diff_generic('pod_id_file', '--pod-id-file')

    def diffparam_privileged(self):
        return self._diff_generic("privileged", "--privileged")

    def diffparam_publish(self):
        return self._diff_generic("publish", "--publish")

    def diffparam_publish_all(self):
        return self._diff_generic("publish_all", "--publish-all")

    def diffparam_pull(self):
        return self._diff_generic("pull", "--pull")

    def diffparam_rdt_class(self):
        return self._diff_generic("rdt_class", "--rdt-class")

    def diffparam_read_only(self):
        return self._diff_generic("read_only", "--read-only")

    def diffparam_read_only_tmpfs(self):
        return self._diff_generic("read_only_tmpfs", "--read-only-tmpfs")

    def diffparam_requires(self):
        return self._diff_generic("requires", "--requires")

    def diffparam_restart_policy(self):
        return self._diff_generic("restart_policy", "--restart")

    def diffparam_retry(self):
        return self._diff_generic("retry", "--retry")

    def diffparam_retry_delay(self):
        return self._diff_generic("retry_delay", "--retry-delay")

    def diffparam_rootfs(self):
        return self._diff_generic("rootfs", "--rootfs")

    # Disabling idemotency check for sdnotify as it's added by systemd generator
    # https://github.com/containers/ansible-podman-collections/issues/775
    # def diffparam_sdnotify(self):
    #     return self._diff_generic('sdnotify', '--sdnotify')

    def diffparam_rm(self):
        before = self.info["hostconfig"]["autoremove"]
        after = self.params["rm"]
        if after is None:
            return self._diff_update_and_compare("rm", "", "")
        return self._diff_update_and_compare("rm", before, after)

    def diffparam_rmi(self):
        return self._diff_generic("rmi", "--rmi", boolean_type=True)

    def diffparam_seccomp_policy(self):
        return self._diff_generic("seccomp_policy", "--seccomp-policy")

    def diffparam_secrets(self):
        return self._diff_generic("secrets", "--secret")

    def diffparam_security_opt(self):
        return self._diff_generic("security_opt", "--security-opt")

    def diffparam_shm_size(self):
        return self._diff_generic("shm_size", "--shm-size")

    def diffparam_shm_size_systemd(self):
        return self._diff_generic("shm_size_systemd", "--shm-size-systemd")

    def diffparam_stop_signal(self):
        return self._diff_generic("stop_signal", "--stop-signal")

    def diffparam_stop_timeout(self):
        return self._diff_generic("stop_timeout", "--stop-timeout")

    def diffparam_subgidname(self):
        return self._diff_generic("subgidname", "--subgidname")

    def diffparam_subuidname(self):
        return self._diff_generic("subuidname", "--subuidname")

    def diffparam_sysctl(self):
        return self._diff_generic("sysctl", "--sysctl")

    def diffparam_systemd(self):
        if self.params["systemd"] is not None:
            self.params["systemd"] = str(self.params["systemd"]).lower()
        return self._diff_generic("systemd", "--systemd")

    def diffparam_timeout(self):
        return self._diff_generic("timeout", "--timeout")

    def diffparam_timezone(self):
        return self._diff_generic("timezone", "--tz")

    def diffparam_tls_verify(self):
        return self._diff_generic("tls_verify", "--tls-verify")

    def diffparam_tty(self):
        before = self.info["config"]["tty"]
        after = self.params["tty"]
        return self._diff_update_and_compare("tty", before, after)

    def diffparam_tmpfs(self):
        before = createcommand("--tmpfs", self.info["config"])
        if before == []:
            before = None
        after = self.params["tmpfs"]
        if before is None and after is None:
            return self._diff_update_and_compare("tmpfs", before, after)
        if after is not None:
            after = ",".join(sorted([str(k).lower() + ":" + str(v).lower() for k, v in after.items() if v is not None]))
            if before:
                before = ",".join(sorted([j.lower() for j in before]))
            else:
                before = ""
        return self._diff_update_and_compare("tmpfs", before, after)

    def diffparam_uidmap(self):
        return self._diff_generic("uidmap", "--uidmap")

    def diffparam_ulimit(self):
        return self._diff_generic("ulimit", "--ulimit")

    def diffparam_umask(self):
        return self._diff_generic("umask", "--umask")

    def diffparam_unsetenv(self):
        return self._diff_generic("unsetenv", "--unsetenv")

    def diffparam_unsetenv_all(self):
        return self._diff_generic("unsetenv_all", "--unsetenv-all", boolean_type=True)

    def diffparam_user(self):
        return self._diff_generic("user", "--user")

    def diffparam_userns(self):
        return self._diff_generic("userns", "--userns")

    def diffparam_uts(self):
        return self._diff_generic("uts", "--uts")

    def diffparam_variant(self):
        return self._diff_generic("variant", "--variant")

    def diffparam_volume(self):
        def clean_volume(x):
            """Remove trailing and double slashes from volumes."""
            if not x.rstrip("/"):
                return "/"
            return x.replace("//", "/").rstrip("/")

        before = createcommand("--volume", self.info["config"])
        if before == []:
            before = None
        after = self.params["volume"]
        if after is not None:
            after = [":".join([clean_volume(i) for i in v.split(":")[:3]]) for v in self.params["volume"]]
        if before is not None:
            before = [":".join([clean_volume(i) for i in v.split(":")[:3]]) for v in before]
        if before is None and after is None:
            return self._diff_update_and_compare("volume", before, after)
        if after is not None:
            after = ",".join(sorted([str(i).lower() for i in after]))
            if before:
                before = ",".join(sorted([str(i).lower() for i in before]))
        return self._diff_update_and_compare("volume", before, after)

    def diffparam_volumes_from(self):
        return self._diff_generic("volumes_from", "--volumes-from")

    def diffparam_workdir(self):
        return self._diff_generic("workdir", "--workdir")

    def is_different(self):
        diff_func_list = [func for func in dir(self) if callable(getattr(self, func)) and func.startswith("diffparam")]
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
            if self.module_params[p] is not None and self.module_params[p] not in [
                {},
                [],
                "",
            ]:
                different = True
        return different


def ensure_image_exists(module, image, module_params):
    """If image is passed, ensure it exists, if not - pull it or fail.

    Arguments:
        module {obj} -- ansible module object
        image {str} -- name of image

    Returns:
        list -- list of image actions - if it pulled or nothing was done
    """
    image_actions = []
    module_exec = module_params["executable"]
    is_rootfs = module_params["rootfs"]

    if is_rootfs:
        if not os.path.exists(image) or not os.path.isdir(image):
            module.fail_json(msg="Image rootfs doesn't exist %s" % image)
        return image_actions
    if not image:
        return image_actions
    image_exists_cmd = [module_exec, "image", "exists", image]
    rc, out, err = module.run_command(image_exists_cmd)
    if rc == 0:
        return image_actions
    image_pull_cmd = [module_exec, "image", "pull", image]
    if module_params["tls_verify"] is False:
        image_pull_cmd.append("--tls-verify=false")
    if module_params["authfile"]:
        image_pull_cmd.extend(["--authfile", module_params["authfile"]])
    if module_params["arch"]:
        image_pull_cmd.append("--arch=%s" % module_params["arch"])
    if module_params["decryption_key"]:
        image_pull_cmd.append("--decryption-key=%s" % module_params["decryption_key"])
    if module_params["platform"]:
        image_pull_cmd.append("--platform=%s" % module_params["platform"])
    if module_params["os"]:
        image_pull_cmd.append("--os=%s" % module_params["os"])
    if module_params["variant"]:
        image_pull_cmd.append("--variant=%s" % module_params["variant"])
    if module_params.get("debug"):
        module.log("PODMAN-CONTAINER-DEBUG: %s" % " ".join(image_pull_cmd))
    rc, out, err = module.run_command(image_pull_cmd)
    if rc != 0:
        module.fail_json(msg="Can't pull image %s" % image, stdout=out, stderr=err)
    image_actions.append("pulled image %s" % image)
    return image_actions


class PodmanContainer:
    """Perform container tasks.

    Manages podman container, inspects it and checks its current state
    """

    def __init__(self, module, name, module_params):
        """Initialize PodmanContainer class.

        Arguments:
            module {obj} -- ansible module object
            name {str} -- name of container
        """

        self.module = module
        self.module_params = module_params
        self.name = name
        self.stdout, self.stderr = "", ""
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
            self.module_params,
            self.info,
            self.get_image_info(),
            self.version,
        )
        is_different = diffcheck.is_different()
        diffs = diffcheck.diff
        if self.module._diff and is_different and diffs["before"] and diffs["after"]:
            self.diff["before"] = "\n".join(["%s - %s" % (k, v) for k, v in sorted(diffs["before"].items())]) + "\n"
            self.diff["after"] = "\n".join(["%s - %s" % (k, v) for k, v in sorted(diffs["after"].items())]) + "\n"
        return is_different

    @property
    def running(self):
        """Return True if container is running now."""
        return self.exists and self.info["State"]["Running"]

    @property
    def stopped(self):
        """Return True if container exists and is not running now."""
        return self.exists and not self.info["State"]["Running"]

    def get_info(self):
        """Inspect container and gather info about it."""
        # pylint: disable=unused-variable
        rc, out, err = self.module.run_command([self.module_params["executable"], b"container", b"inspect", self.name])
        return json.loads(out)[0] if rc == 0 else {}

    def get_image_info(self):
        """Inspect container image and gather info about it."""
        # pylint: disable=unused-variable
        is_rootfs = self.module_params["rootfs"]
        if is_rootfs:
            return {"Id": self.module_params["image"]}
        rc, out, err = self.module.run_command(
            [
                self.module_params["executable"],
                b"image",
                b"inspect",
                self.module_params["image"].replace("docker://", ""),
            ]
        )
        self.module.log("PODMAN-CONTAINER-DEBUG: %s: %s" % (out, self.module_params["image"]))
        return json.loads(out)[0] if rc == 0 else {}

    def _get_podman_version(self):
        # pylint: disable=unused-variable
        rc, out, err = self.module.run_command([self.module_params["executable"], b"--version"])
        if rc != 0 or not out or "version" not in out:
            self.module.fail_json(msg="%s run failed!" % self.module_params["executable"])
        return out.split("version")[1].strip()

    def _perform_action(self, action):
        """Perform action with container.

        Arguments:
            action {str} -- action to perform - start, create, stop, run,
                            delete, restart
        """
        b_command = PodmanModuleParams(
            action,
            self.module_params,
            self.version,
            self.module,
        ).construct_command_from_params()
        full_cmd = " ".join([self.module_params["executable"]] + [to_native(i) for i in b_command])
        self.actions.append(full_cmd)
        if self.module.check_mode:
            self.module.log("PODMAN-CONTAINER-DEBUG (check_mode): %s" % full_cmd)
        else:
            rc, out, err = self.module.run_command(
                [self.module_params["executable"], b"container"] + b_command,
                expand_user_and_vars=False,
            )
            self.module.log("PODMAN-CONTAINER-DEBUG: %s" % full_cmd)
            if self.module_params["debug"]:
                self.module.log("PODMAN-CONTAINER-DEBUG STDOUT: %s" % out)
                self.module.log("PODMAN-CONTAINER-DEBUG STDERR: %s" % err)
                self.module.log("PODMAN-CONTAINER-DEBUG RC: %s" % rc)
            self.stdout = out
            self.stderr = err
            if rc != 0:
                self.module.fail_json(
                    msg="Container %s exited with code %s when %sed" % (self.name, rc, action),
                    stdout=out,
                    stderr=err,
                )

    def run(self):
        """Run the container."""
        self._perform_action("run")

    def delete(self):
        """Delete the container."""
        self._perform_action("delete")

    def stop(self):
        """Stop the container."""
        self._perform_action("stop")

    def start(self):
        """Start the container."""
        self._perform_action("start")

    def restart(self):
        """Restart the container."""
        self._perform_action("restart")

    def create(self):
        """Create the container."""
        self._perform_action("create")

    def recreate(self):
        """Recreate the container."""
        if self.running:
            self.stop()
        if not self.info["HostConfig"]["AutoRemove"]:
            self.delete()
        self.create()

    def recreate_run(self):
        """Recreate and run the container."""
        if self.running:
            self.stop()
        if not self.info["HostConfig"]["AutoRemove"]:
            self.delete()
        self.run()


class PodmanManager:
    """Module manager class.

    Defines according to parameters what actions should be applied to container
    """

    def __init__(self, module, params):
        """Initialize PodmanManager class.

        Arguments:
            module {obj} -- ansible module object
        """

        self.module = module
        self.results = {
            "changed": False,
            "actions": [],
            "container": {},
        }
        self.module_params = params
        self.name = self.module_params["name"]
        self.executable = self.module.get_bin_path(self.module_params["executable"], required=True)
        self.image = self.module_params["image"]
        self.state = self.module_params["state"]
        disable_image_pull = self.state in ("quadlet", "absent") or self.module_params["pull"] == "never"
        image_actions = (
            ensure_image_exists(self.module, self.image, self.module_params) if not disable_image_pull else []
        )
        self.results["actions"] += image_actions

        self.restart = self.module_params["force_restart"]
        self.recreate = self.module_params["recreate"]

        if self.module_params["generate_systemd"].get("new"):
            self.module_params["rm"] = True

        self.container = PodmanContainer(self.module, self.name, self.module_params)

    def update_container_result(self, changed=True):
        """Inspect the current container, update results with last info, exit.

        Keyword Arguments:
            changed {bool} -- whether any action was performed
                              (default: {True})
        """
        facts = self.container.get_info() if changed else self.container.info
        out, err = self.container.stdout, self.container.stderr
        self.results.update(
            {
                "changed": changed,
                "container": facts,
                "podman_actions": self.container.actions,
            },
            stdout=out,
            stderr=err,
        )
        if self.container.diff:
            self.results.update({"diff": self.container.diff})
        if self.module.params["debug"] or self.module_params["debug"]:
            self.results.update({"podman_version": self.container.version})
        sysd = generate_systemd(self.module, self.module_params, self.name, self.container.version)
        self.results["changed"] = changed or sysd["changed"]
        self.results.update({"podman_systemd": sysd["systemd"]})
        if sysd["diff"]:
            if "diff" not in self.results:
                self.results.update({"diff": sysd["diff"]})
            else:
                self.results["diff"]["before"] += sysd["diff"]["before"]
                self.results["diff"]["after"] += sysd["diff"]["after"]
        quadlet = ContainerQuadlet(self.module_params)
        quadlet_content = quadlet.create_quadlet_content()
        self.results.update({"podman_quadlet": quadlet_content})

    def make_started(self):
        """Run actions if desired state is 'started'."""
        if not self.image:
            if not self.container.exists:
                self.module.fail_json(msg="Cannot start container when image" " is not specified!")
            if self.restart:
                self.container.restart()
                self.results["actions"].append("restarted %s" % self.container.name)
            else:
                self.container.start()
                self.results["actions"].append("started %s" % self.container.name)
            self.update_container_result()
            return
        if self.container.exists and self.restart:
            if self.container.running:
                self.container.restart()
                self.results["actions"].append("restarted %s" % self.container.name)
            else:
                self.container.start()
                self.results["actions"].append("started %s" % self.container.name)
            self.update_container_result()
            return
        if self.container.running and (self.container.different or self.recreate):
            self.container.recreate_run()
            self.results["actions"].append("recreated %s" % self.container.name)
            self.update_container_result()
            return
        elif self.container.running and not self.container.different:
            if self.restart:
                self.container.restart()
                self.results["actions"].append("restarted %s" % self.container.name)
                self.update_container_result()
                return
            self.update_container_result(changed=False)
            return
        elif not self.container.exists:
            self.container.run()
            self.results["actions"].append("started %s" % self.container.name)
            self.update_container_result()
            return
        elif self.container.stopped and (self.container.different or self.recreate):
            self.container.recreate_run()
            self.results["actions"].append("recreated %s" % self.container.name)
            self.update_container_result()
            return
        elif self.container.stopped and not self.container.different:
            self.container.start()
            self.results["actions"].append("started %s" % self.container.name)
            self.update_container_result()
            return

    def make_created(self):
        """Run actions if desired state is 'created'."""
        if not self.container.exists and not self.image:
            self.module.fail_json(msg="Cannot create container when image" " is not specified!")
        if not self.container.exists:
            self.container.create()
            self.results["actions"].append("created %s" % self.container.name)
            self.update_container_result()
            return
        else:
            if self.container.different or self.recreate:
                self.container.recreate()
                self.results["actions"].append("recreated %s" % self.container.name)
                if self.container.running:
                    self.container.start()
                    self.results["actions"].append("started %s" % self.container.name)
                self.update_container_result()
                return
            elif self.restart:
                if self.container.running:
                    self.container.restart()
                    self.results["actions"].append("restarted %s" % self.container.name)
                else:
                    self.container.start()
                    self.results["actions"].append("started %s" % self.container.name)
                self.update_container_result()
                return
            self.update_container_result(changed=False)
            return

    def make_stopped(self):
        """Run actions if desired state is 'stopped'."""
        if not self.container.exists and not self.image:
            self.module.fail_json(msg="Cannot create container when image" " is not specified!")
        if not self.container.exists:
            self.container.create()
            self.results["actions"].append("created %s" % self.container.name)
            self.update_container_result()
            return
        if self.container.stopped:
            self.update_container_result(changed=False)
            return
        elif self.container.running:
            self.container.stop()
            self.results["actions"].append("stopped %s" % self.container.name)
            self.update_container_result()
            return

    def make_absent(self):
        """Run actions if desired state is 'absent'."""
        if not self.container.exists:
            self.results.update({"changed": False})
        elif self.container.exists:
            delete_systemd(self.module, self.module_params, self.name, self.container.version)
            self.container.delete()
            self.results["actions"].append("deleted %s" % self.container.name)
            self.results.update({"changed": True})
        self.results.update({"container": {}, "podman_actions": self.container.actions})

    def make_quadlet(self):
        results_update = create_quadlet_state(self.module, "container")
        self.results.update(results_update)

    def execute(self):
        """Execute the desired action according to map of actions & states."""
        states_map = {
            "present": self.make_created,
            "started": self.make_started,
            "absent": self.make_absent,
            "stopped": self.make_stopped,
            "created": self.make_created,
            "quadlet": self.make_quadlet,
        }
        process_action = states_map[self.state]
        process_action()
        return self.results
