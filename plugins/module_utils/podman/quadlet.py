# Copyright (c) 2024 Sagi Shnaidman (@sshnaidm)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import os

from ansible_collections.containers.podman.plugins.module_utils.podman.common import compare_systemd_file_content

QUADLET_ROOT_PATH = "/etc/containers/systemd/"
QUADLET_NON_ROOT_PATH = "~/.config/containers/systemd/"


class Quadlet:
    param_map = {}

    def __init__(self, section: str, params: dict):
        self.section = section
        self.custom_params = self.custom_prepare_params(params)
        self.dict_params = self.prepare_params()

    def custom_prepare_params(self, params: dict) -> dict:
        """
        Custom parameter processing for specific Quadlet types.
        """
        # This should be implemented in child classes if needed.
        return params

    def prepare_params(self) -> dict:
        """
        Convert parameter values as per param_map.
        """
        processed_params = []
        for param_key, quadlet_key in self.param_map.items():
            value = self.custom_params.get(param_key)
            if value is not None:
                if isinstance(value, list):
                    # Add an entry for each item in the list
                    for item in value:
                        processed_params.append([quadlet_key, item])
                else:
                    if isinstance(value, bool):
                        value = str(value).lower()
                    # Add a single entry for the key
                    processed_params.append([quadlet_key, value])
        return processed_params

    def create_quadlet_content(self) -> str:
        """
        Construct the quadlet content as a string.
        """
        custom_user_options = self.custom_params.get("quadlet_options")
        custom_text = "\n" + "\n".join(custom_user_options) if custom_user_options else ""
        return f"[{self.section}]\n" + "\n".join(
            f"{key}={value}" for key, value in self.dict_params
        ) + custom_text + "\n"

    def write_to_file(self, path: str):
        """
        Write the quadlet content to a file at the specified path.
        """
        content = self.create_quadlet_content()
        with open(path, 'w') as file:
            file.write(content)


class ContainerQuadlet(Quadlet):
    param_map = {
        'cap_add': 'AddCapability',
        'device': 'AddDevice',
        'annotation': 'Annotation',
        'name': 'ContainerName',
        # the following are not implemented yet in Podman module
        'AutoUpdate': 'AutoUpdate',
        'ContainersConfModule': 'ContainersConfModule',
        # end of not implemented yet
        'dns': 'DNS',
        'dns_option': 'DNSOption',
        'dns_search': 'DNSSearch',
        'cap_drop': 'DropCapability',
        'entrypoint': 'Entrypoint',
        'env': 'Environment',
        'env_file': 'EnvironmentFile',
        'env_host': 'EnvironmentHost',
        'command': 'Exec',
        'expose': 'ExposeHostPort',
        'gidmap': 'GIDMap',
        'global_args': 'GlobalArgs',
        'group': 'Group',  # Does not exist in module parameters
        'healthcheck': 'HealthCheckCmd',
        'healthcheck_interval': 'HealthInterval',
        'healthcheck_failure_action': 'HealthOnFailure',
        'healthcheck_retries': 'HealthRetries',
        'healthcheck_start_period': 'HealthStartPeriod',
        'healthcheck_timeout': 'HealthTimeout',
        # the following are not implemented yet in Podman module
        'HealthStartupCmd': 'HealthStartupCmd',
        'HealthStartupInterval': 'HealthStartupInterval',
        'HealthStartupRetries': 'HealthStartupRetries',
        'HealthStartupSuccess': 'HealthStartupSuccess',
        'HealthStartupTimeout': 'HealthStartupTimeout',
        # end of not implemented yet
        'hostname': 'HostName',
        'image': 'Image',
        'ip': 'IP',
        # the following are not implemented yet in Podman module
        'IP6': 'IP6',
        # end of not implemented yet
        'label': 'Label',
        'log_driver': 'LogDriver',
        "Mask": "Mask",  # add it in security_opt
        'mount': 'Mount',
        'network': 'Network',
        'no_new_privileges': 'NoNewPrivileges',
        'sdnotify': 'Notify',
        'pids_limit': 'PidsLimit',
        'pod': 'Pod',
        'publish': 'PublishPort',
        # the following are not implemented yet in Podman module
        "Pull": "Pull",
        # end of not implemented yet
        'read_only': 'ReadOnly',
        'read_only_tmpfs': 'ReadOnlyTmpfs',
        'rootfs': 'Rootfs',
        'init': 'RunInit',
        'SeccompProfile': 'SeccompProfile',
        'secrets': 'Secret',
        # All these are in security_opt
        'SecurityLabelDisable': 'SecurityLabelDisable',
        'SecurityLabelFileType': 'SecurityLabelFileType',
        'SecurityLabelLevel': 'SecurityLabelLevel',
        'SecurityLabelNested': 'SecurityLabelNested',
        'SecurityLabelType': 'SecurityLabelType',
        'shm_size': 'ShmSize',
        'stop_timeout': 'StopTimeout',
        'subgidname': 'SubGIDMap',
        'subuidname': 'SubUIDMap',
        'sysctl': 'Sysctl',
        'timezone': 'Timezone',
        'tmpfs': 'Tmpfs',
        'uidmap': 'UIDMap',
        'ulimit': 'Ulimit',
        'Unmask': 'Unmask',  # --security-opt unmask=ALL
        'user': 'User',
        'userns': 'UserNS',
        'volume': 'Volume',
        'workdir': 'WorkingDir',
        'podman_args': 'PodmanArgs',
    }

    def __init__(self, params: dict):
        super().__init__("Container", params)

    def custom_prepare_params(self, params: dict) -> dict:
        """
        Custom parameter processing for container-specific parameters.
        """
        # Work on params in params_map and convert them to a right form
        if params["annotation"]:
            params['annotation'] = ["%s=%s" %
                                    (k, v) for k, v in params['annotation'].items()]
        if params["cap_add"]:
            params["cap_add"] = " ".join(params["cap_add"])
        if params["cap_drop"]:
            params["cap_drop"] = " ".join(params["cap_drop"])
        if params["command"]:
            params["command"] = (" ".join(params["command"])
                                 if isinstance(params["command"], list)
                                 else params["command"])
        if params["label"]:
            params["label"] = ["%s=%s" % (k, v) for k, v in params["label"].items()]
        if params["env"]:
            params["env"] = ["%s=%s" % (k, v) for k, v in params["env"].items()]
        if params["sysctl"]:
            params["sysctl"] = ["%s=%s" % (k, v) for k, v in params["sysctl"].items()]
        if params["tmpfs"]:
            params["tmpfs"] = ["%s:%s" % (k, v) if v else k for k, v in params["tmpfs"].items()]

        # Work on params which are not in the param_map but can be calculated
        params["global_args"] = []
        if params["user"] and len(str(params["user"]).split(":")) > 1:
            user, group = params["user"].split(":")
            params["user"] = user
            params["group"] = group
        if params["security_opt"]:
            if "no-new-privileges" in params["security_opt"]:
                params["no_new_privileges"] = True
                params["security_opt"].remove("no-new-privileges")
        if params["log_level"]:
            params["global_args"].append(f"--log-level {params['log_level']}")
        if params["debug"]:
            params["global_args"].append("--log-level debug")

        # Work on params which are not in the param_map and add them to PodmanArgs
        params["podman_args"] = []
        if params["authfile"]:
            params["podman_args"].append(f"--authfile {params['authfile']}")
        if params["attach"]:
            for attach in params["attach"]:
                params["podman_args"].append(f"--attach {attach}")
        if params["blkio_weight"]:
            params["podman_args"].append(f"--blkio-weight {params['blkio_weight']}")
        if params["blkio_weight_device"]:
            params["podman_args"].append(" ".join([
                f"--blkio-weight-device {':'.join(blkio)}" for blkio in params["blkio_weight_device"].items()]))
        if params["cgroupns"]:
            params["podman_args"].append(f"--cgroupns {params['cgroupns']}")
        if params["cgroup_parent"]:
            params["podman_args"].append(f"--cgroup-parent {params['cgroup_parent']}")
        if params["cidfile"]:
            params["podman_args"].append(f"--cidfile {params['cidfile']}")
        if params["conmon_pidfile"]:
            params["podman_args"].append(f"--conmon-pidfile {params['conmon_pidfile']}")
        if params["cpuset_cpus"]:
            params["podman_args"].append(f"--cpuset-cpus {params['cpuset_cpus']}")
        if params["cpuset_mems"]:
            params["podman_args"].append(f"--cpuset-mems {params['cpuset_mems']}")
        if params["cpu_period"]:
            params["podman_args"].append(f"--cpu-period {params['cpu_period']}")
        if params["cpu_quota"]:
            params["podman_args"].append(f"--cpu-quota {params['cpu_quota']}")
        if params["cpu_rt_period"]:
            params["podman_args"].append(f"--cpu-rt-period {params['cpu_rt_period']}")
        if params["cpu_rt_runtime"]:
            params["podman_args"].append(f"--cpu-rt-runtime {params['cpu_rt_runtime']}")
        if params["cpu_shares"]:
            params["podman_args"].append(f"--cpu-shares {params['cpu_shares']}")
        if params["device_read_bps"]:
            for i in params["device_read_bps"]:
                params["podman_args"].append(f"--device-read-bps {i}")
        if params["device_read_iops"]:
            for i in params["device_read_iops"]:
                params["podman_args"].append(f"--device-read-iops {i}")
        if params["device_write_bps"]:
            for i in params["device_write_bps"]:
                params["podman_args"].append(f"--device-write-bps {i}")
        if params["device_write_iops"]:
            for i in params["device_write_iops"]:
                params["podman_args"].append(f"--device-write-iops {i}")
        if params["etc_hosts"]:
            for host_ip in params['etc_hosts'].items():
                params["podman_args"].append(f"--add-host {':'.join(host_ip)}")
        if params["hooks_dir"]:
            for hook in params["hooks_dir"]:
                params["podman_args"].append(f"--hooks-dir {hook}")
        if params["http_proxy"]:
            params["podman_args"].append(f"--http-proxy {params['http_proxy']}")
        if params["image_volume"]:
            params["podman_args"].append(f"--image-volume {params['image_volume']}")
        if params["init_path"]:
            params["podman_args"].append(f"--init-path {params['init_path']}")
        if params["interactive"]:
            params["podman_args"].append("--interactive")
        if params["ipc"]:
            params["podman_args"].append(f"--ipc {params['ipc']}")
        if params["kernel_memory"]:
            params["podman_args"].append(f"--kernel-memory {params['kernel_memory']}")
        if params["label_file"]:
            params["podman_args"].append(f"--label-file {params['label_file']}")
        if params["log_opt"]:
            for k, v in params['log_opt'].items():
                params["podman_args"].append(f"--log-opt {k.replace('max_size', 'max-size')}={v}")
        if params["mac_address"]:
            params["podman_args"].append(f"--mac-address {params['mac_address']}")
        if params["memory"]:
            params["podman_args"].append(f"--memory {params['memory']}")
        if params["memory_reservation"]:
            params["podman_args"].append(f"--memory-reservation {params['memory_reservation']}")
        if params["memory_swap"]:
            params["podman_args"].append(f"--memory-swap {params['memory_swap']}")
        if params["memory_swappiness"]:
            params["podman_args"].append(f"--memory-swappiness {params['memory_swappiness']}")
        if params["network_aliases"]:
            for alias in params["network_aliases"]:
                params["podman_args"].append(f"--network-alias {alias}")
        if params["no_hosts"] is not None:
            params["podman_args"].append(f"--no-hosts={params['no_hosts']}")
        if params["oom_kill_disable"]:
            params["podman_args"].append(f"--oom-kill-disable={params['oom_kill_disable']}")
        if params["oom_score_adj"]:
            params["podman_args"].append(f"--oom-score-adj {params['oom_score_adj']}")
        if params["pid"]:
            params["podman_args"].append(f"--pid {params['pid']}")
        if params["privileged"]:
            params["podman_args"].append("--privileged")
        if params["publish_all"]:
            params["podman_args"].append("--publish-all")
        if params["requires"]:
            params["podman_args"].append(f"--requires {','.join(params['requires'])}")
        if params["restart_policy"]:
            params["podman_args"].append(f"--restart-policy {params['restart_policy']}")
        if params["rm"]:
            params["podman_args"].append("--rm")
        if params["security_opt"]:
            for security_opt in params["security_opt"]:
                params["podman_args"].append(f"--security-opt {security_opt}")
        if params["sig_proxy"]:
            params["podman_args"].append(f"--sig-proxy {params['sig_proxy']}")
        if params["stop_signal"]:
            params["podman_args"].append(f"--stop-signal {params['stop_signal']}")
        if params["systemd"]:
            params["podman_args"].append(f"--systemd={str(params['systemd']).lower()}")
        if params["tty"]:
            params["podman_args"].append("--tty")
        if params["uts"]:
            params["podman_args"].append(f"--uts {params['uts']}")
        if params["volumes_from"]:
            for volume in params["volumes_from"]:
                params["podman_args"].append(f"--volumes-from {volume}")
        if params["cmd_args"]:
            params["podman_args"].append(params["cmd_args"])

        # Return params with custom processing applied
        return params


class NetworkQuadlet(Quadlet):
    param_map = {
        'name': 'NetworkName',
        'internal': 'Internal',
        'driver': 'Driver',
        'gateway': 'Gateway',
        'disable_dns': 'DisableDNS',
        'subnet': 'Subnet',
        'ip_range': 'IPRange',
        'ipv6': 'IPv6',
        "opt": "Options",
        # Add more parameter mappings specific to networks
        'ContainersConfModule': 'ContainersConfModule',
        "DNS": "DNS",
        "IPAMDriver": "IPAMDriver",
        "Label": "Label",
        "global_args": "GlobalArgs",
        "podman_args": "PodmanArgs",
    }

    def __init__(self, params: dict):
        super().__init__("Network", params)

    def custom_prepare_params(self, params: dict) -> dict:
        """
        Custom parameter processing for network-specific parameters.
        """
        # Work on params in params_map and convert them to a right form
        if params["debug"]:
            params["global_args"].append("--log-level debug")
        if params["opt"]:
            new_opt = []
            for k, v in params["opt"].items():
                if v is not None:
                    new_opt.append(f"{k}={v}")
            params["opt"] = new_opt
        return params


# This is a inherited class that represents a Quadlet file for the Podman pod
class PodQuadlet(Quadlet):
    param_map = {
        'name': 'PodName',
        "network": "Network",
        "publish": "PublishPort",
        "volume": "Volume",
        'ContainersConfModule': 'ContainersConfModule',
        "global_args": "GlobalArgs",
        "podman_args": "PodmanArgs",
    }

    def __init__(self, params: dict):
        super().__init__("Pod", params)

    def custom_prepare_params(self, params: dict) -> dict:
        """
        Custom parameter processing for pod-specific parameters.
        """
        # Work on params in params_map and convert them to a right form
        params["global_args"] = []
        params["podman_args"] = []

        if params["add_host"]:
            for host in params['add_host']:
                params["podman_args"].append(f"--add-host {host}")
        if params["cgroup_parent"]:
            params["podman_args"].append(f"--cgroup-parent {params['cgroup_parent']}")
        if params["blkio_weight"]:
            params["podman_args"].append(f"--blkio-weight {params['blkio_weight']}")
        if params["blkio_weight_device"]:
            params["podman_args"].append(" ".join([
                f"--blkio-weight-device {':'.join(blkio)}" for blkio in params["blkio_weight_device"].items()]))
        if params["cpuset_cpus"]:
            params["podman_args"].append(f"--cpuset-cpus {params['cpuset_cpus']}")
        if params["cpuset_mems"]:
            params["podman_args"].append(f"--cpuset-mems {params['cpuset_mems']}")
        if params["cpu_shares"]:
            params["podman_args"].append(f"--cpu-shares {params['cpu_shares']}")
        if params["cpus"]:
            params["podman_args"].append(f"--cpus {params['cpus']}")
        if params["device"]:
            for device in params["device"]:
                params["podman_args"].append(f"--device {device}")
        if params["device_read_bps"]:
            for i in params["device_read_bps"]:
                params["podman_args"].append(f"--device-read-bps {i}")
        if params["device_write_bps"]:
            for i in params["device_write_bps"]:
                params["podman_args"].append(f"--device-write-bps {i}")
        if params["dns"]:
            for dns in params["dns"]:
                params["podman_args"].append(f"--dns {dns}")
        if params["dns_opt"]:
            for dns_option in params["dns_opt"]:
                params["podman_args"].append(f"--dns-option {dns_option}")
        if params["dns_search"]:
            for dns_search in params["dns_search"]:
                params["podman_args"].append(f"--dns-search {dns_search}")
        if params["gidmap"]:
            for gidmap in params["gidmap"]:
                params["podman_args"].append(f"--gidmap {gidmap}")
        if params["hostname"]:
            params["podman_args"].append(f"--hostname {params['hostname']}")
        if params["infra"]:
            params["podman_args"].append(f"--infra {params['infra']}")
        if params["infra_command"]:
            params["podman_args"].append(f"--infra-command {params['infra_command']}")
        if params["infra_conmon_pidfile"]:
            params["podman_args"].append(f"--infra-conmon-pidfile {params['infra_conmon_pidfile']}")
        if params["infra_image"]:
            params["podman_args"].append(f"--infra-image {params['infra_image']}")
        if params["infra_name"]:
            params["podman_args"].append(f"--infra-name {params['infra_name']}")
        if params["ip"]:
            params["podman_args"].append(f"--ip {params['ip']}")
        if params["label"]:
            for label, label_v in params["label"].items():
                params["podman_args"].append(f"--label {label}={label_v}")
        if params["label_file"]:
            params["podman_args"].append(f"--label-file {params['label_file']}")
        if params["mac_address"]:
            params["podman_args"].append(f"--mac-address {params['mac_address']}")
        if params["memory"]:
            params["podman_args"].append(f"--memory {params['memory']}")
        if params["memory_swap"]:
            params["podman_args"].append(f"--memory-swap {params['memory_swap']}")
        if params["no_hosts"]:
            params["podman_args"].append(f"--no-hosts {params['no_hosts']}")
        if params["pid"]:
            params["podman_args"].append(f"--pid {params['pid']}")
        if params["pod_id_file"]:
            params["podman_args"].append(f"--pod-id-file {params['pod_id_file']}")
        if params["share"]:
            params["podman_args"].append(f"--share {params['share']}")
        if params["subgidname"]:
            params["podman_args"].append(f"--subgidname {params['subgidname']}")
        if params["subuidname"]:
            params["podman_args"].append(f"--subuidname {params['subuidname']}")
        if params["uidmap"]:
            for uidmap in params["uidmap"]:
                params["podman_args"].append(f"--uidmap {uidmap}")
        if params["userns"]:
            params["podman_args"].append(f"--userns {params['userns']}")
        if params["debug"]:
            params["global_args"].append("--log-level debug")

        return params


# This is a inherited class that represents a Quadlet file for the Podman volume
class VolumeQuadlet(Quadlet):
    param_map = {
        'name': 'VolumeName',
        'driver': 'Driver',
        'label': 'Label',
        # 'opt': 'Options',
        'ContainersConfModule': 'ContainersConfModule',
        'global_args': 'GlobalArgs',
        'podman_args': 'PodmanArgs',
    }

    def __init__(self, params: dict):
        super().__init__("Volume", params)

    def custom_prepare_params(self, params: dict) -> dict:
        """
        Custom parameter processing for volume-specific parameters.
        """
        # Work on params in params_map and convert them to a right form
        params["global_args"] = []
        params["podman_args"] = []

        if params["debug"]:
            params["global_args"].append("--log-level debug")
        if params["label"]:
            params["label"] = ["%s=%s" % (k, v) for k, v in params["label"].items()]
        if params["options"]:
            for opt in params["options"]:
                params["podman_args"].append(f"--opt {opt}")

        return params


# This is a inherited class that represents a Quadlet file for the Podman kube
class KubeQuadlet(Quadlet):
    param_map = {
        'configmap': 'ConfigMap',
        'log_driver': 'LogDriver',
        'network': 'Network',
        'kube_file': 'Yaml',
        'userns': 'UserNS',
        'AutoUpdate': 'AutoUpdate',
        'ExitCodePropagation': 'ExitCodePropagation',
        'KubeDownForce': 'KubeDownForce',
        'PublishPort': 'PublishPort',
        'SetWorkingDirectory': 'SetWorkingDirectory',
        'ContainersConfModule': 'ContainersConfModule',
        'global_args': 'GlobalArgs',
        'podman_args': 'PodmanArgs',
    }

    def __init__(self, params: dict):
        super().__init__("Kube", params)

    def custom_prepare_params(self, params: dict) -> dict:
        """
        Custom parameter processing for kube-specific parameters.
        """
        # Work on params in params_map and convert them to a right form
        params["global_args"] = []
        params["podman_args"] = []

        if params["debug"]:
            params["global_args"].append("--log-level debug")

        return params


# This is a inherited class that represents a Quadlet file for the Podman image
class ImageQuadlet(Quadlet):
    param_map = {
        'AllTags': 'AllTags',
        'arch': 'Arch',
        'authfile': 'AuthFile',
        'ca_cert_dir': 'CertDir',
        'creds': 'Creds',
        'DecryptionKey': 'DecryptionKey',
        'name': 'Image',
        'ImageTag': 'ImageTag',
        'OS': 'OS',
        'validate_certs': 'TLSVerify',
        'Variant': 'Variant',
        'ContainersConfModule': 'ContainersConfModule',
        'global_args': 'GlobalArgs',
        'podman_args': 'PodmanArgs',
    }

    def __init__(self, params: dict):
        super().__init__("Image", params)

    def custom_prepare_params(self, params: dict) -> dict:
        """
        Custom parameter processing for image-specific parameters.
        """
        # Work on params in params_map and convert them to a right form
        params["global_args"] = []
        params["podman_args"] = []

        if params["username"] and params["password"]:
            params["creds"] = f"{params['username']}:{params['password']}"
        # if params['validate_certs'] is not None:
        #     params['validate_certs'] = str(params['validate_certs']).lower()

        return params


def check_quadlet_directory(module, quadlet_dir):
    '''Check if the directory exists and is writable. If not, fail the module.'''
    if not os.path.exists(quadlet_dir):
        try:
            os.makedirs(quadlet_dir)
        except Exception as e:
            module.fail_json(
                msg="Directory for quadlet_file can't be created: %s" % e)
    if not os.access(quadlet_dir, os.W_OK):
        module.fail_json(
            msg="Directory for quadlet_file is not writable: %s" % quadlet_dir)


def create_quadlet_state(module, issuer):
    '''Create a quadlet file for the specified issuer.'''
    class_map = {
        "container": ContainerQuadlet,
        "network": NetworkQuadlet,
        "pod": PodQuadlet,
        "volume": VolumeQuadlet,
        "kube": KubeQuadlet,
        "image": ImageQuadlet,
    }
    # Let's detect which user is running
    user = "root" if os.geteuid() == 0 else "user"
    quadlet_dir = module.params.get('quadlet_dir')
    if not quadlet_dir:
        if user == "root":
            quadlet_dir = QUADLET_ROOT_PATH
        else:
            quadlet_dir = os.path.expanduser(QUADLET_NON_ROOT_PATH)
    # Create a filename based on the issuer
    if not module.params.get('name') and not module.params.get('quadlet_filename'):
        module.fail_json(msg=f"Filename for {issuer} is required for creating a quadlet file.")
    if issuer == "image":
        name = module.params['name'].split("/")[-1].split(":")[0]
    else:
        name = module.params.get('name')
    quad_file_name = module.params['quadlet_filename']
    if quad_file_name and not quad_file_name.endswith(f".{issuer}"):
        quad_file_name = f"{quad_file_name}.{issuer}"
    filename = quad_file_name or f"{name}.{issuer}"
    quadlet_file_path = os.path.join(quadlet_dir, filename)
    # Check if the directory exists and is writable
    check_quadlet_directory(module, quadlet_dir)
    # Check if file already exists and if it's different
    quadlet = class_map[issuer](module.params)
    quadlet_content = quadlet.create_quadlet_content()
    file_diff = compare_systemd_file_content(quadlet_file_path, quadlet_content)
    if bool(file_diff):
        quadlet.write_to_file(quadlet_file_path)
        results_update = {
            'changed': True,
            "diff": {
                "before": "\n".join(file_diff[0]) if isinstance(file_diff[0], list) else file_diff[0] + "\n",
                "after": "\n".join(file_diff[1]) if isinstance(file_diff[1], list) else file_diff[1] + "\n",
            }}
    else:
        results_update = {}
    return results_update

# Check with following command:
# QUADLET_UNIT_DIRS=<Directory> /usr/lib/systemd/system-generators/podman-system-generator {--user} --dryrun
