from __future__ import absolute_import, division, print_function
import json  # noqa: F402

from ansible.module_utils._text import to_bytes, to_native
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
    PodQuadlet,
)


__metaclass__ = type

ARGUMENTS_SPEC_POD = dict(
    state=dict(
        type="str",
        default="created",
        choices=[
            "created",
            "killed",
            "restarted",
            "absent",
            "started",
            "stopped",
            "paused",
            "unpaused",
            "quadlet",
        ],
    ),
    recreate=dict(type="bool", default=False),
    add_host=dict(type="list", required=False, elements="str"),
    blkio_weight=dict(type="str", required=False),
    blkio_weight_device=dict(type="list", elements="str", required=False),
    cgroup_parent=dict(type="str", required=False),
    cpus=dict(type="str", required=False),
    cpuset_cpus=dict(type="str", required=False),
    cpuset_mems=dict(type="str", required=False),
    cpu_shares=dict(type="str", required=False),
    device=dict(type="list", elements="str", required=False),
    device_read_bps=dict(type="list", elements="str", required=False),
    device_write_bps=dict(type="list", elements="str", required=False),
    dns=dict(type="list", elements="str", required=False),
    dns_opt=dict(type="list", elements="str", aliases=["dns_option"], required=False),
    dns_search=dict(type="list", elements="str", required=False),
    exit_policy=dict(type="str", required=False, choices=["continue", "stop"]),
    generate_systemd=dict(type="dict", default={}),
    gidmap=dict(type="list", elements="str", required=False),
    gpus=dict(type="str", required=False),
    hostname=dict(type="str", required=False),
    infra=dict(type="bool", required=False),
    infra_conmon_pidfile=dict(type="str", required=False),
    infra_command=dict(type="str", required=False),
    infra_image=dict(type="str", required=False),
    infra_name=dict(type="str", required=False),
    ip=dict(type="str", required=False),
    ip6=dict(type="str", required=False),
    label=dict(type="dict", required=False),
    label_file=dict(type="str", required=False),
    mac_address=dict(type="str", required=False),
    memory=dict(type="str", required=False),
    memory_swap=dict(type="str", required=False),
    name=dict(type="str", required=True),
    network=dict(type="list", elements="str", required=False),
    network_alias=dict(type="list", elements="str", required=False, aliases=["network_aliases"]),
    no_hosts=dict(type="bool", required=False),
    pid=dict(type="str", required=False),
    pod_id_file=dict(type="str", required=False),
    publish=dict(type="list", required=False, elements="str", aliases=["ports"]),
    quadlet_dir=dict(type="path"),
    quadlet_filename=dict(type="str"),
    quadlet_file_mode=dict(type="raw", required=False),
    quadlet_options=dict(type="list", elements="str"),
    restart_policy=dict(type="str", required=False),
    security_opt=dict(type="list", elements="str", required=False),
    share=dict(type="str", required=False),
    share_parent=dict(type="bool", required=False),
    shm_size=dict(type="str", required=False),
    shm_size_systemd=dict(type="str", required=False),
    subgidname=dict(type="str", required=False),
    subuidname=dict(type="str", required=False),
    sysctl=dict(type="dict", required=False),
    uidmap=dict(type="list", elements="str", required=False),
    userns=dict(type="str", required=False),
    uts=dict(type="str", required=False),
    volume=dict(type="list", elements="str", aliases=["volumes"], required=False),
    volumes_from=dict(type="list", elements="str", required=False),
    executable=dict(type="str", required=False, default="podman"),
    debug=dict(type="bool", default=False),
)


class PodmanPodModuleParams:
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
        if self.action in [
            "start",
            "restart",
            "stop",
            "delete",
            "pause",
            "unpause",
            "kill",
        ]:
            return self._simple_action()
        if self.action in ["create"]:
            return self._create_action()
        self.module.fail_json(msg="Unknown action %s" % self.action)

    def _simple_action(self):
        if self.action in ["start", "restart", "stop", "pause", "unpause", "kill"]:
            cmd = [self.action, self.params["name"]]
            return [to_bytes(i, errors="surrogate_or_strict") for i in cmd]

        if self.action == "delete":
            cmd = ["rm", "-f", self.params["name"]]
            return [to_bytes(i, errors="surrogate_or_strict") for i in cmd]
        self.module.fail_json(msg="Unknown action %s" % self.action)

    def _create_action(self):
        cmd = [self.action]
        all_param_methods = [
            func for func in dir(self) if callable(getattr(self, func)) and func.startswith("addparam")
        ]
        params_set = (i for i in self.params if self.params[i] is not None)
        for param in params_set:
            func_name = "_".join(["addparam", param])
            if func_name in all_param_methods:
                cmd = getattr(self, func_name)(cmd)
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

    def addparam_add_host(self, c):
        for g in self.params["add_host"]:
            c += ["--add-host", g]
        return c

    def addparam_blkio_weight(self, c):
        self.check_version("--blkio-weight", minv="4.3.0")
        return c + ["--blkio-weight", self.params["blkio_weight"]]

    def addparam_blkio_weight_device(self, c):
        self.check_version("--blkio-weight-device", minv="4.3.0")
        for dev in self.params["blkio_weight_device"]:
            c += ["--blkio-weight-device", dev]
        return c

    def addparam_cgroup_parent(self, c):
        return c + ["--cgroup-parent", self.params["cgroup_parent"]]

    def addparam_cpus(self, c):
        self.check_version("--cpus", minv="4.2.0")
        return c + ["--cpus", self.params["cpus"]]

    def addparam_cpuset_cpus(self, c):
        self.check_version("--cpus", minv="4.2.0")
        return c + ["--cpuset-cpus", self.params["cpuset_cpus"]]

    def addparam_cpuset_mems(self, c):
        self.check_version("--cpuset-mems", minv="4.3.0")
        return c + ["--cpuset-mems", self.params["cpuset_mems"]]

    def addparam_cpu_shares(self, c):
        self.check_version("--cpu-shares", minv="4.3.0")
        return c + ["--cpu-shares", self.params["cpu_shares"]]

    def addparam_device(self, c):
        for dev in self.params["device"]:
            c += ["--device", dev]
        return c

    def addparam_device_read_bps(self, c):
        self.check_version("--device-read-bps", minv="4.3.0")
        for dev in self.params["device_read_bps"]:
            c += ["--device-read-bps", dev]
        return c

    def addparam_device_write_bps(self, c):
        self.check_version("--device-write-bps", minv="4.3.0")
        for dev in self.params["device_write_bps"]:
            c += ["--device-write-bps", dev]
        return c

    def addparam_dns(self, c):
        for g in self.params["dns"]:
            c += ["--dns", g]
        return c

    def addparam_dns_opt(self, c):
        for g in self.params["dns_opt"]:
            c += ["--dns-option", g]
        return c

    def addparam_dns_search(self, c):
        for g in self.params["dns_search"]:
            c += ["--dns-search", g]
        return c

    def addparam_exit_policy(self, c):
        return c + ["--exit-policy=%s" % self.params["exit_policy"]]

    def addparam_gidmap(self, c):
        for gidmap in self.params["gidmap"]:
            c += ["--gidmap", gidmap]
        return c

    def addparam_gpus(self, c):
        return c + ["--gpus", self.params["gpus"]]

    def addparam_hostname(self, c):
        return c + ["--hostname", self.params["hostname"]]

    def addparam_infra(self, c):
        return c + [
            b"=".join(
                [
                    b"--infra",
                    to_bytes(self.params["infra"], errors="surrogate_or_strict"),
                ]
            )
        ]

    def addparam_infra_conmon_pidfile(self, c):
        return c + ["--infra-conmon-pidfile", self.params["infra_conmon_pidfile"]]

    def addparam_infra_command(self, c):
        return c + ["--infra-command", self.params["infra_command"]]

    def addparam_infra_image(self, c):
        return c + ["--infra-image", self.params["infra_image"]]

    def addparam_infra_name(self, c):
        return c + ["--infra-name", self.params["infra_name"]]

    def addparam_ip(self, c):
        return c + ["--ip", self.params["ip"]]

    def addparam_ip6(self, c):
        return c + ["--ip6", self.params["ip6"]]

    def addparam_label(self, c):
        for label in self.params["label"].items():
            c += [
                "--label",
                b"=".join([to_bytes(i, errors="surrogate_or_strict") for i in label]),
            ]
        return c

    def addparam_label_file(self, c):
        return c + ["--label-file", self.params["label_file"]]

    def addparam_mac_address(self, c):
        return c + ["--mac-address", self.params["mac_address"]]

    def addparam_memory(self, c):
        self.check_version("--memory", minv="4.2.0")
        return c + ["--memory", self.params["memory"]]

    def addparam_memory_swap(self, c):
        self.check_version("--memory-swap", minv="4.3.0")
        return c + ["--memory-swap", self.params["memory_swap"]]

    def addparam_name(self, c):
        return c + ["--name", self.params["name"]]

    def addparam_network(self, c):
        if LooseVersion(self.podman_version) >= LooseVersion("4.0.0"):
            for net in self.params["network"]:
                c += ["--network", net]
            return c
        return c + ["--network", ",".join(self.params["network"])]

    def addparam_network_aliases(self, c):
        for alias in self.params["network_aliases"]:
            c += ["--network-alias", alias]
        return c

    def addparam_no_hosts(self, c):
        return c + ["=".join(["--no-hosts", self.params["no_hosts"]])]

    def addparam_pid(self, c):
        return c + ["--pid", self.params["pid"]]

    def addparam_pod_id_file(self, c):
        return c + ["--pod-id-file", self.params["pod_id_file"]]

    def addparam_publish(self, c):
        for g in self.params["publish"]:
            c += ["--publish", g]
        return c

    def addparam_restart_policy(self, c):
        return c + ["--restart=%s" % self.params["restart_policy"]]

    def addparam_security_opt(self, c):
        for g in self.params["security_opt"]:
            c += ["--security-opt", g]
        return c

    def addparam_share(self, c):
        return c + ["--share", self.params["share"]]

    def addparam_share_parent(self, c):
        if self.params["share_parent"] is not None:
            return c + ["--share-parent=%s" % self.params["share_parent"]]
        return c

    def addparam_shm_size(self, c):
        return c + ["--shm-size=%s" % self.params["shm_size"]]

    def addparam_shm_size_systemd(self, c):
        return c + ["--shm-size-systemd=%s" % self.params["shm_size_systemd"]]

    def addparam_subgidname(self, c):
        return c + ["--subgidname", self.params["subgidname"]]

    def addparam_subuidname(self, c):
        return c + ["--subuidname", self.params["subuidname"]]

    def addparam_sysctl(self, c):
        for k, v in self.params["sysctl"].items():
            c += ["--sysctl", "%s=%s" % (k, v)]
        return c

    def addparam_uidmap(self, c):
        for uidmap in self.params["uidmap"]:
            c += ["--uidmap", uidmap]
        return c

    def addparam_userns(self, c):
        return c + ["--userns", self.params["userns"]]

    def addparam_uts(self, c):
        return c + ["--uts", self.params["uts"]]

    def addparam_volume(self, c):
        for vol in self.params["volume"]:
            if vol:
                c += ["--volume", vol]
        return c

    def addparam_volumes_from(self, c):
        for vol in self.params["volumes_from"]:
            c += ["--volumes-from", vol]
        return c


class PodmanPodDefaults:
    def __init__(self, module, podman_version):
        self.module = module
        self.version = podman_version
        self.defaults = {
            "infra": True,
            "label": {},
        }

    def default_dict(self):
        # make here any changes to self.defaults related to podman version
        # https://github.com/containers/libpod/pull/5669
        # if (LooseVersion(self.version) >= LooseVersion('1.8.0')
        #         and LooseVersion(self.version) < LooseVersion('1.9.0')):
        #     self.defaults['cpu_shares'] = 1024
        return self.defaults


class PodmanPodDiff:
    def __init__(self, module, module_params, info, infra_info, podman_version):
        self.module = module
        self.module_params = module_params
        self.version = podman_version
        self.default_dict = None
        self.info = lower_keys(info)
        self.infra_info = lower_keys(infra_info)
        self.params = self.defaultize()
        self.diff = {"before": {}, "after": {}}
        self.non_idempotent = {}

    def defaultize(self):
        params_with_defaults = {}
        self.default_dict = PodmanPodDefaults(self.module, self.version).default_dict()
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
        info_config = self.info
        before, after = diff_generic(self.params, info_config, module_arg, cmd_arg, boolean_type)
        return self._diff_update_and_compare(module_arg, before, after)

    def diffparam_add_host(self):
        return self._diff_generic("add_host", "--add-host")

    def diffparam_blkio_weight(self):
        return self._diff_generic("blkio_weight", "--blkio-weight")

    def diffparam_blkio_weight_device(self):
        return self._diff_generic("blkio_weight_device", "--blkio-weight-device")

    def diffparam_cgroup_parent(self):
        return self._diff_generic("cgroup_parent", "--cgroup-parent")

    def diffparam_cpu_shares(self):
        return self._diff_generic("cpu_shares", "--cpu-shares")

    def diffparam_cpus(self):
        return self._diff_generic("cpus", "--cpus")

    def diffparam_cpuset_cpus(self):
        return self._diff_generic("cpuset_cpus", "--cpuset-cpus")

    def diffparam_cpuset_mems(self):
        return self._diff_generic("cpuset_mems", "--cpuset-mems")

    def diffparam_device(self):
        return self._diff_generic("device", "--device")

    def diffparam_device_read_bps(self):
        return self._diff_generic("device_read_bps", "--device-read-bps")

    def diffparam_device_write_bps(self):
        return self._diff_generic("device_write_bps", "--device-write-bps")

    def diffparam_dns(self):
        return self._diff_generic("dns", "--dns")

    def diffparam_dns_opt(self):
        return self._diff_generic("dns_opt", "--dns-option")

    def diffparam_dns_search(self):
        return self._diff_generic("dns_search", "--dns-search")

    # Disabling idemotency check for exit policy as it's added by systemd generator
    # https://github.com/containers/ansible-podman-collections/issues/774
    # def diffparam_exit_policy(self):
    #     return self._diff_generic('exit_policy', '--exit-policy')

    def diffparam_gidmap(self):
        return self._diff_generic("gidmap", "--gidmap")

    def diffparam_gpus(self):
        return self._diff_generic("gpus", "--gpus")

    def diffparam_hostname(self):
        return self._diff_generic("hostname", "--hostname")

    # TODO(sshnaidm): https://github.com/containers/podman/issues/6968
    def diffparam_infra(self):
        if "state" in self.info and "infracontainerid" in self.info["state"]:
            before = self.info["state"]["infracontainerid"] != ""
        else:
            # TODO(sshnaidm): https://github.com/containers/podman/issues/6968
            before = "infracontainerid" in self.info
        after = self.params["infra"]
        return self._diff_update_and_compare("infra", before, after)

    def diffparam_infra_command(self):
        return self._diff_generic("infra_command", "--infra-command")

    # Disabling idemotency check for infra_conmon_pidfile as it's added by systemd generator
    # https://github.com/containers/ansible-podman-collections/issues/774
    # def diffparam_infra_conmon_pidfile(self):
    #     return self._diff_generic('infra_conmon_pidfile', '--infra-conmon-pidfile')

    def diffparam_infra_image(self):
        return self._diff_generic("infra_image", "--infra-image")

    def diffparam_infra_name(self):
        return self._diff_generic("infra_name", "--infra-name")

    def diffparam_ip(self):
        return self._diff_generic("ip", "--ip")

    def diffparam_ip6(self):
        return self._diff_generic("ip6", "--ip6")

    def diffparam_label(self):
        if "config" in self.info and "labels" in self.info["config"]:
            before = self.info["config"].get("labels") or {}
        else:
            before = self.info["labels"] if "labels" in self.info else {}
        after = self.params["label"]
        # Strip out labels that are coming from systemd files
        # https://github.com/containers/ansible-podman-collections/issues/276
        if "podman_systemd_unit" in before:
            after.pop("podman_systemd_unit", None)
            before.pop("podman_systemd_unit", None)
        return self._diff_update_and_compare("label", before, after)

    def diffparam_label_file(self):
        return self._diff_generic("label_file", "--label-file")

    def diffparam_mac_address(self):
        return self._diff_generic("mac_address", "--mac-address")

    def diffparam_memory(self):
        return self._diff_generic("memory", "--memory")

    def diffparam_memory_swap(self):
        return self._diff_generic("memory_swap", "--memory-swap")

    def diffparam_network(self):
        return self._diff_generic("network", "--network")

    def diffparam_network_alias(self):
        return self._diff_generic("network_alias", "--network-alias")

    def diffparam_no_hosts(self):
        return self._diff_generic("no_hosts", "--no-hosts", boolean_type=True)

    def diffparam_pid(self):
        return self._diff_generic("pid", "--pid")

    # Disabling idemotency check for pod id file as it's added by systemd generator
    # https://github.com/containers/ansible-podman-collections/issues/774
    # def diffparam_pod_id_file(self):
    #     return self._diff_generic('pod_id_file', '--pod-id-file')

    def diffparam_publish(self):
        return self._diff_generic("publish", "--publish")

    def diffparam_restart_policy(self):
        return self._diff_generic("restart_policy", "--restart")

    def diffparam_security_opt(self):
        return self._diff_generic("security_opt", "--security-opt")

    def diffparam_share(self):
        return self._diff_generic("share", "--share")

    def diffparam_share_parent(self):
        return self._diff_generic("share_parent", "--share-parent")

    def diffparam_shm_size(self):
        return self._diff_generic("shm_size", "--shm-size")

    def diffparam_shm_size_systemd(self):
        return self._diff_generic("shm_size_systemd", "--shm-size-systemd")

    def diffparam_subgidname(self):
        return self._diff_generic("subgidname", "--subgidname")

    def diffparam_subuidname(self):
        return self._diff_generic("subuidname", "--subuidname")

    def diffparam_sysctl(self):
        return self._diff_generic("sysctl", "--sysctl")

    def diffparam_uidmap(self):
        return self._diff_generic("uidmap", "--uidmap")

    def diffparam_userns(self):
        return self._diff_generic("userns", "--userns")

    def diffparam_uts(self):
        return self._diff_generic("uts", "--uts")

    def diffparam_volume(self):
        def clean_volume(x):
            """Remove trailing and double slashes from volumes."""
            if not x.rstrip("/"):
                return "/"
            return x.replace("//", "/").rstrip("/")

        before = createcommand("--volume", self.info)
        if before == []:
            before = None
        after = self.params["volume"]
        if after is not None:
            after = [":".join([clean_volume(i) for i in v.split(":")[:2]]) for v in self.params["volume"]]
        if before is not None:
            before = [":".join([clean_volume(i) for i in v.split(":")[:2]]) for v in before]
        self.module.log("PODMAN Before: %s and After: %s" % (before, after))
        if before is None and after is None:
            return self._diff_update_and_compare("volume", before, after)
        if after is not None:
            after = ",".join(sorted([str(i).lower() for i in after]))
            if before:
                before = ",".join(sorted([str(i).lower() for i in before]))
        return self._diff_update_and_compare("volume", before, after)

    def diffparam_volumes_from(self):
        return self._diff_generic("volumes_from", "--volumes-from")

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


class PodmanPod:
    """Perform pod tasks.

    Manages podman pod, inspects it and checks its current state
    """

    def __init__(self, module, name, module_params):
        """Initialize PodmanPod class.

        Arguments:
            module {obj} -- ansible module object
            name {str} -- name of pod
        """

        self.module = module
        self.module_params = module_params
        self.name = name
        self.stdout, self.stderr = "", ""
        self.info = self.get_info()
        self.infra_info = self.get_infra_info()
        self.version = self._get_podman_version()
        self.diff = {}
        self.actions = []

    @property
    def exists(self):
        """Check if pod exists."""
        return bool(self.info != {})

    @property
    def different(self):
        """Check if pod is different."""
        diffcheck = PodmanPodDiff(self.module, self.module_params, self.info, self.infra_info, self.version)
        is_different = diffcheck.is_different()
        diffs = diffcheck.diff
        if self.module._diff and is_different and diffs["before"] and diffs["after"]:
            self.diff["before"] = "\n".join(["%s - %s" % (k, v) for k, v in sorted(diffs["before"].items())]) + "\n"
            self.diff["after"] = "\n".join(["%s - %s" % (k, v) for k, v in sorted(diffs["after"].items())]) + "\n"
        return is_different

    @property
    def running(self):
        """Return True if pod is running now."""
        if "status" in self.info["State"]:
            return self.info["State"]["status"] == "Running"
        # older podman versions (1.6.x) don't have status in 'podman pod inspect'
        # if other methods fail, use 'podman pod ps'
        ps_info = self.get_ps()
        if "status" in ps_info:
            return ps_info["status"] == "Running"
        return self.info["State"] == "Running"

    @property
    def paused(self):
        """Return True if pod is paused now."""
        if "status" in self.info["State"]:
            return self.info["State"]["status"] == "Paused"
        return self.info["State"] == "Paused"

    @property
    def stopped(self):
        """Return True if pod exists and is not running now."""
        if not self.exists:
            return False
        if "status" in self.info["State"]:
            return not (self.info["State"]["status"] == "Running")
        return not (self.info["State"] == "Running")

    def get_info(self):
        """Inspect pod and gather info about it."""
        # pylint: disable=unused-variable
        rc, out, err = self.module.run_command([self.module_params["executable"], b"pod", b"inspect", self.name])
        if rc == 0:
            info = json.loads(out)
            # from podman 5 onwards, this is a list of dicts,
            # before it was just a single dict when querying
            # a single pod
            if isinstance(info, list):
                return info[0]
            else:
                return info
        return {}

    def get_ps(self):
        """Inspect pod process and gather info about it."""
        # pylint: disable=unused-variable
        rc, out, err = self.module.run_command(
            [
                self.module_params["executable"],
                b"pod",
                b"ps",
                b"--format",
                b"json",
                b"--filter",
                "name=" + self.name,
            ]
        )
        return json.loads(out)[0] if rc == 0 else {}

    def get_infra_info(self):
        """Inspect pod and gather info about it."""
        if not self.info:
            return {}
        if "InfraContainerID" in self.info:
            infra_container_id = self.info["InfraContainerID"]
        elif "State" in self.info and "infraContainerID" in self.info["State"]:
            infra_container_id = self.info["State"]["infraContainerID"]
        else:
            return {}
        # pylint: disable=unused-variable
        rc, out, err = self.module.run_command([self.module_params["executable"], b"inspect", infra_container_id])
        return json.loads(out)[0] if rc == 0 else {}

    def _get_podman_version(self):
        # pylint: disable=unused-variable
        rc, out, err = self.module.run_command([self.module_params["executable"], b"--version"])
        if rc != 0 or not out or "version" not in out:
            self.module.fail_json(msg="%s run failed!" % self.module_params["executable"])
        return out.split("version")[1].strip()

    def _perform_action(self, action):
        """Perform action with pod.

        Arguments:
            action {str} -- action to perform - start, create, stop, pause
                            unpause, delete, restart, kill
        """
        b_command = PodmanPodModuleParams(
            action,
            self.module_params,
            self.version,
            self.module,
        ).construct_command_from_params()
        full_cmd = " ".join([self.module_params["executable"], "pod"] + [to_native(i) for i in b_command])
        self.module.log("PODMAN-POD-DEBUG: %s" % full_cmd)
        self.actions.append(full_cmd)
        if not self.module.check_mode:
            rc, out, err = self.module.run_command(
                [self.module_params["executable"], b"pod"] + b_command,
                expand_user_and_vars=False,
            )
            self.stdout = out
            self.stderr = err
            if rc != 0:
                self.module.fail_json(msg="Can't %s pod %s" % (action, self.name), stdout=out, stderr=err)

    def delete(self):
        """Delete the pod."""
        self._perform_action("delete")

    def stop(self):
        """Stop the pod."""
        self._perform_action("stop")

    def start(self):
        """Start the pod."""
        self._perform_action("start")

    def create(self):
        """Create the pod."""
        self._perform_action("create")

    def recreate(self):
        """Recreate the pod."""
        self.delete()
        self.create()

    def restart(self):
        """Restart the pod."""
        self._perform_action("restart")

    def kill(self):
        """Kill the pod."""
        self._perform_action("kill")

    def pause(self):
        """Pause the pod."""
        self._perform_action("pause")

    def unpause(self):
        """Unpause the pod."""
        self._perform_action("unpause")


class PodmanPodManager:
    """Module manager class.

    Defines according to parameters what actions should be applied to pod
    """

    def __init__(self, module, params):
        """Initialize PodmanManager class.

        Arguments:
            module {obj} -- ansible module object
        """

        self.module = module
        self.module_params = params
        self.results = {
            "changed": False,
            "actions": [],
            "pod": {},
        }
        self.name = self.module_params["name"]
        self.executable = self.module.get_bin_path(self.module_params["executable"], required=True)
        self.state = self.module_params["state"]
        self.recreate = self.module_params["recreate"]
        self.pod = PodmanPod(self.module, self.name, self.module_params)

    def update_pod_result(self, changed=True):
        """Inspect the current pod, update results with last info, exit.

        Keyword Arguments:
            changed {bool} -- whether any action was performed
                              (default: {True})
        """
        facts = self.pod.get_info() if changed else self.pod.info
        if isinstance(facts, list):
            facts = facts[0]
        out, err = self.pod.stdout, self.pod.stderr
        self.results.update(
            {"changed": changed, "pod": facts, "podman_actions": self.pod.actions},
            stdout=out,
            stderr=err,
        )
        if self.pod.diff:
            self.results.update({"diff": self.pod.diff})
        if self.module.params["debug"] or self.module_params["debug"]:
            self.results.update({"podman_version": self.pod.version})
        sysd = generate_systemd(self.module, self.module_params, self.name, self.pod.version)
        self.results["changed"] = changed or sysd["changed"]
        self.results.update({"podman_systemd": sysd["systemd"]})
        if sysd["diff"]:
            if "diff" not in self.results:
                self.results.update({"diff": sysd["diff"]})
            else:
                self.results["diff"]["before"] += sysd["diff"]["before"]
                self.results["diff"]["after"] += sysd["diff"]["after"]
        quadlet = PodQuadlet(self.module_params)
        quadlet_content = quadlet.create_quadlet_content()
        self.results.update({"podman_quadlet": quadlet_content})

    def execute(self):
        """Execute the desired action according to map of actions & states."""
        states_map = {
            "created": self.make_created,
            "started": self.make_started,
            "stopped": self.make_stopped,
            "restarted": self.make_restarted,
            "absent": self.make_absent,
            "killed": self.make_killed,
            "paused": self.make_paused,
            "unpaused": self.make_unpaused,
            "quadlet": self.make_quadlet,
        }
        process_action = states_map[self.state]
        process_action()
        return self.results

    def _create_or_recreate_pod(self):
        """Ensure pod exists and is exactly as it should be by input params."""
        changed = False
        if self.pod.exists:
            if self.pod.different or self.recreate:
                self.pod.recreate()
                self.results["actions"].append("recreated %s" % self.pod.name)
                changed = True
        elif not self.pod.exists:
            self.pod.create()
            self.results["actions"].append("created %s" % self.pod.name)
            changed = True
        return changed

    def make_created(self):
        """Run actions if desired state is 'created'."""
        if self.pod.exists and not self.pod.different:
            self.update_pod_result(changed=False)
            return
        self._create_or_recreate_pod()
        self.update_pod_result()

    def make_killed(self):
        """Run actions if desired state is 'killed'."""
        self._create_or_recreate_pod()
        self.pod.kill()
        self.results["actions"].append("killed %s" % self.pod.name)
        self.update_pod_result()

    def make_paused(self):
        """Run actions if desired state is 'paused'."""
        changed = self._create_or_recreate_pod()
        if self.pod.paused:
            self.update_pod_result(changed=changed)
            return
        self.pod.pause()
        self.results["actions"].append("paused %s" % self.pod.name)
        self.update_pod_result()

    def make_unpaused(self):
        """Run actions if desired state is 'unpaused'."""
        changed = self._create_or_recreate_pod()
        if not self.pod.paused:
            self.update_pod_result(changed=changed)
            return
        self.pod.unpause()
        self.results["actions"].append("unpaused %s" % self.pod.name)
        self.update_pod_result()

    def make_started(self):
        """Run actions if desired state is 'started'."""
        changed = self._create_or_recreate_pod()
        if not changed and self.pod.running:
            self.update_pod_result(changed=changed)
            return

        # self.pod.unpause()  TODO(sshnaidm): to unpause if state == started?
        self.pod.start()
        self.results["actions"].append("started %s" % self.pod.name)
        self.update_pod_result()

    def make_stopped(self):
        """Run actions if desired state is 'stopped'."""
        if not self.pod.exists:
            self.module.fail_json("Pod %s doesn't exist!" % self.pod.name)
        if self.pod.running:
            self.pod.stop()
            self.results["actions"].append("stopped %s" % self.pod.name)
            self.update_pod_result()
        elif self.pod.stopped:
            self.update_pod_result(changed=False)

    def make_restarted(self):
        """Run actions if desired state is 'restarted'."""
        if self.pod.exists:
            self.pod.restart()
            self.results["actions"].append("restarted %s" % self.pod.name)
            self.results.update({"changed": True})
            self.update_pod_result()
        else:
            self.module.fail_json("Pod %s doesn't exist!" % self.pod.name)

    def make_absent(self):
        """Run actions if desired state is 'absent'."""
        if not self.pod.exists:
            self.results.update({"changed": False})
        elif self.pod.exists:
            delete_systemd(self.module, self.module_params, self.name, self.pod.version)
            self.pod.delete()
            self.results["actions"].append("deleted %s" % self.pod.name)
            self.results.update({"changed": True})
        self.results.update({"pod": {}, "podman_actions": self.pod.actions})

    def make_quadlet(self):
        results_update = create_quadlet_state(self.module, "pod")
        self.results.update(results_update)
