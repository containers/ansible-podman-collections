from __future__ import (absolute_import, division, print_function)
import json  # noqa: F402
from distutils.version import LooseVersion  # noqa: F402

from ansible.module_utils._text import to_bytes, to_native  # noqa: F402
from ansible_collections.containers.podman.plugins.module_utils.podman.common import lower_keys

__metaclass__ = type

ARGUMENTS_SPEC_CONTAINER = dict(
    name=dict(required=True, type='str'),
    executable=dict(default='podman', type='str'),
    state=dict(type='str', default='started', choices=[
        'absent', 'present', 'stopped', 'started']),
    image=dict(type='str'),
    annotation=dict(type='dict'),
    authfile=dict(type='path'),
    blkio_weight=dict(type='int'),
    blkio_weight_device=dict(type='dict'),
    cap_add=dict(type='list', elements='str', aliases=['capabilities']),
    cap_drop=dict(type='list', elements='str'),
    cgroup_parent=dict(type='path'),
    cgroupns=dict(type='str'),
    cgroups=dict(type='str', choices=['default', 'disabled']),
    cidfile=dict(type='path'),
    cmd_args=dict(type='list', elements='str'),
    conmon_pidfile=dict(type='path'),
    command=dict(type='raw'),
    cpu_period=dict(type='int'),
    cpu_rt_period=dict(type='int'),
    cpu_rt_runtime=dict(type='int'),
    cpu_shares=dict(type='int'),
    cpus=dict(type='str'),
    cpuset_cpus=dict(type='str'),
    cpuset_mems=dict(type='str'),
    detach=dict(type='bool', default=True),
    debug=dict(type='bool', default=False),
    detach_keys=dict(type='str'),
    device=dict(type='list', elements='str'),
    device_read_bps=dict(type='list'),
    device_read_iops=dict(type='list'),
    device_write_bps=dict(type='list'),
    device_write_iops=dict(type='list'),
    dns=dict(type='list', elements='str', aliases=['dns_servers']),
    dns_option=dict(type='str', aliases=['dns_opts']),
    dns_search=dict(type='str', aliases=['dns_search_domains']),
    entrypoint=dict(type='str'),
    env=dict(type='dict'),
    env_file=dict(type='path'),
    env_host=dict(type='bool'),
    etc_hosts=dict(type='dict', aliases=['add_hosts']),
    expose=dict(type='list', elements='str', aliases=[
                'exposed', 'exposed_ports']),
    force_restart=dict(type='bool', default=False,
                       aliases=['restart']),
    gidmap=dict(type='list', elements='str'),
    group_add=dict(type='list', aliases=['groups']),
    healthcheck=dict(type='str'),
    healthcheck_interval=dict(type='str'),
    healthcheck_retries=dict(type='int'),
    healthcheck_start_period=dict(type='str'),
    healthcheck_timeout=dict(type='str'),
    hostname=dict(type='str'),
    http_proxy=dict(type='bool'),
    image_volume=dict(type='str', choices=['bind', 'tmpfs', 'ignore']),
    image_strict=dict(type='bool', default=False),
    init=dict(type='bool'),
    init_path=dict(type='str'),
    interactive=dict(type='bool'),
    ip=dict(type='str'),
    ipc=dict(type='str', aliases=['ipc_mode']),
    kernel_memory=dict(type='str'),
    label=dict(type='dict', aliases=['labels']),
    label_file=dict(type='str'),
    log_driver=dict(type='str', choices=[
        'k8s-file', 'journald', 'json-file']),
    log_level=dict(
        type='str',
        choices=["debug", "info", "warn", "error", "fatal", "panic"]),
    log_opt=dict(type='dict', aliases=['log_options'],
                 options=dict(
        max_size=dict(type='str'),
        path=dict(type='str'),
        tag=dict(type='str'))),
    mac_address=dict(type='str'),
    memory=dict(type='str'),
    memory_reservation=dict(type='str'),
    memory_swap=dict(type='str'),
    memory_swappiness=dict(type='int'),
    mount=dict(type='str'),
    network=dict(type='list', elements='str', aliases=['net', 'network_mode']),
    no_hosts=dict(type='bool'),
    oom_kill_disable=dict(type='bool'),
    oom_score_adj=dict(type='int'),
    pid=dict(type='str', aliases=['pid_mode']),
    pids_limit=dict(type='str'),
    pod=dict(type='str'),
    privileged=dict(type='bool'),
    publish=dict(type='list', elements='str', aliases=[
        'ports', 'published', 'published_ports']),
    publish_all=dict(type='bool'),
    read_only=dict(type='bool'),
    read_only_tmpfs=dict(type='bool'),
    recreate=dict(type='bool', default=False),
    restart_policy=dict(type='str'),
    rm=dict(type='bool', aliases=['remove', 'auto_remove']),
    rootfs=dict(type='bool'),
    security_opt=dict(type='list', elements='str'),
    shm_size=dict(type='str'),
    sig_proxy=dict(type='bool'),
    stop_signal=dict(type='int'),
    stop_timeout=dict(type='int'),
    subgidname=dict(type='str'),
    subuidname=dict(type='str'),
    sysctl=dict(type='dict'),
    systemd=dict(type='bool'),
    tmpfs=dict(type='dict'),
    tty=dict(type='bool'),
    uidmap=dict(type='list', elements='str'),
    ulimit=dict(type='list', aliases=['ulimits']),
    user=dict(type='str'),
    userns=dict(type='str', aliases=['userns_mode']),
    uts=dict(type='str'),
    volume=dict(type='list', elements='str', aliases=['volumes']),
    volumes_from=dict(type='list', elements='str'),
    workdir=dict(type='str', aliases=['working_dir'])
)


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
        for gidmap in self.params['gidmap']:
            c += ['--gidmap', gidmap]
        return c

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
        if self.params['init']:
            c += ['--init']
        return c

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
        for k, v in self.params['log_opt'].items():
            if v is not None:
                c += ['--log-opt',
                      b"=".join([to_bytes(k.replace('max_size', 'max-size'),
                                          errors='surrogate_or_strict'),
                                 to_bytes(v,
                                          errors='surrogate_or_strict')])]
        return c

    def addparam_log_level(self, c):
        return c + ['--log-level', self.params['log_level']]

    def addparam_mac_address(self, c):
        return c + ['--mac-address', self.params['mac_address']]

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
    def __init__(self, image_info, podman_version):
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
            "log_level": "error",
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
    def __init__(self, module, module_params, info, image_info, podman_version):
        self.module = module
        self.module_params = module_params
        self.version = podman_version
        self.default_dict = None
        self.info = lower_keys(info)
        self.image_info = lower_keys(image_info)
        self.params = self.defaultize()
        self.diff = {'before': {}, 'after': {}}
        self.non_idempotent = {
            'env_file',  # We can't get env vars from file to check
            'env_host',
        }

    def defaultize(self):
        params_with_defaults = {}
        self.default_dict = PodmanDefaults(
            self.image_info, self.version).default_dict()
        for p in self.module_params:
            if self.module_params[p] is None and p in self.default_dict:
                params_with_defaults[p] = self.default_dict[p]
            else:
                params_with_defaults[p] = self.module_params[p]
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
        if self.module_params['annotation'] is not None:
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
        if before == [] and self.module_params['blkio_weight_device'] is None:
            after = []
        else:
            after = self.params['blkio_weight_device']
        return self._diff_update_and_compare('blkio_weight_device', before, after)

    def diffparam_cap_add(self):
        before = self.info['effectivecaps'] or []
        after = []
        if self.module_params['cap_add'] is not None:
            after += ["cap_" + i.lower()
                      for i in self.module_params['cap_add']]
        after += before
        before, after = sorted(list(set(before))), sorted(list(set(after)))
        return self._diff_update_and_compare('cap_add', before, after)

    def diffparam_cap_drop(self):
        before = self.info['effectivecaps'] or []
        after = before[:]
        if self.module_params['cap_drop'] is not None:
            for c in ["cap_" + i.lower() for i in self.module_params['cap_drop']]:
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
        if self.module_params['command'] is not None:
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
        if self.module_params['conmon_pidfile'] is None:
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
        before = {i.split("=")[0]: "=".join(i.split("=")[1:])
                  for i in env_before}
        after = before.copy()
        if self.params['env']:
            after.update({
                k: v
                for k, v in self.params['env'].items()
            })
        return self._diff_update_and_compare('env', before, after)

    def diffparam_etc_hosts(self):
        if self.info['hostconfig']['extrahosts']:
            before = dict([i.split(":")
                           for i in self.info['hostconfig']['extrahosts']])
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
        before_id = self.info['image']
        after_id = self.image_info['id']
        if before_id == after_id:
            return self._diff_update_and_compare('image', before_id, after_id)
        before = self.info['config']['image']
        after = self.params['image']
        mode = self.params['image_strict']
        if mode is None or not mode:
            # In a idempotency 'lite mode' assume all images from different registries are the same
            before = before.replace(":latest", "")
            after = after.replace(":latest", "")
            before = before.split("/")[-1]
            after = after.split("/")[-1]
        else:
            return self._diff_update_and_compare('image', before_id, after_id)
        return self._diff_update_and_compare('image', before, after)

    def diffparam_ipc(self):
        before = self.info['hostconfig']['ipcmode']
        after = self.params['ipc']
        if self.params['pod'] and not self.module_params['ipc']:
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

    def diffparam_log_level(self):
        excom = self.info['exitcommand']
        if '--log-level' in excom:
            before = excom[excom.index('--log-level') + 1].lower()
        else:
            before = self.params['log_level']
        after = self.params['log_level']
        return self._diff_update_and_compare('log_level', before, after)

    # Parameter has limited idempotency, unable to guess the default log_path
    def diffparam_log_opt(self):
        before, after = {}, {}
        # Log path
        if 'logpath' in self.info:
            path_before = self.info['logpath']
            if (self.module_params['log_opt'] and
                    'path' in self.module_params['log_opt'] and
                    self.module_params['log_opt']['path'] is not None):
                path_after = self.params['log_opt']['path']
            else:
                path_after = path_before
            if path_before != path_after:
                before.update({'log-path': path_before})
                after.update({'log-path': path_after})

        # Log tag
        if 'logtag' in self.info:
            tag_before = self.info['logtag']
            if (self.module_params['log_opt'] and
                    'tag' in self.module_params['log_opt'] and
                    self.module_params['log_opt']['tag'] is not None):
                tag_after = self.params['log_opt']['tag']
            else:
                tag_after = ''
            if tag_before != tag_after:
                before.update({'log-tag': tag_before})
                after.update({'log-tag': tag_after})

        return self._diff_update_and_compare('log_opt', before, after)

    def diffparam_mac_address(self):
        before = str(self.info['networksettings']['macaddress'])
        if self.module_params['mac_address'] is not None:
            after = self.params['mac_address']
        else:
            after = before
        return self._diff_update_and_compare('mac_address', before, after)

    def diffparam_memory(self):
        before = str(self.info['hostconfig']['memory'])
        after = self.params['memory']
        return self._diff_update_and_compare('memory', before, after)

    def diffparam_memory_swap(self):
        # By default it's twice memory parameter
        before = str(self.info['hostconfig']['memoryswap'])
        after = self.params['memory_swap']
        if (self.module_params['memory_swap'] is None
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
        if not self.module_params['network'] and self.params['pod']:
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
        # For newer verions of Podman
        if 'resolvconfpath' in self.info:
            before = not bool(self.info['resolvconfpath'])
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
            before = signals[before.lower()]
        after = str(self.params['stop_signal'])
        if not after.isdigit():
            after = signals[after.lower()]
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
            after = {i.split('=')[0]: i.split('=')[1]
                     for i in self.params['ulimit']}
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
        if self.params['pod'] and not self.module_params['uts']:
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
            if self.module_params[p] is not None and self.module_params[p] not in [{}, [], '']:
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
    module_exec = module_params['executable']
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

    def __init__(self, module, name, module_params):
        """Initialize PodmanContainer class.

        Arguments:
            module {obj} -- ansible module object
            name {str} -- name of container
        """

        self.module = module
        self.module_params = module_params
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
            self.module_params,
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
            [self.module_params['executable'], b'container', b'inspect', self.name])
        return json.loads(out)[0] if rc == 0 else {}

    def get_image_info(self):
        """Inspect container image and gather info about it."""
        # pylint: disable=unused-variable
        rc, out, err = self.module.run_command(
            [self.module_params['executable'], b'image', b'inspect', self.module_params['image']])
        return json.loads(out)[0] if rc == 0 else {}

    def _get_podman_version(self):
        # pylint: disable=unused-variable
        rc, out, err = self.module.run_command(
            [self.module_params['executable'], b'--version'])
        if rc != 0 or not out or "version" not in out:
            self.module.fail_json(msg="%s run failed!" %
                                  self.module_params['executable'])
        return out.split("version")[1].strip()

    def _perform_action(self, action):
        """Perform action with container.

        Arguments:
            action {str} -- action to perform - start, create, stop, run,
                            delete
        """
        b_command = PodmanModuleParams(action,
                                       self.module_params,
                                       self.version,
                                       self.module,
                                       ).construct_command_from_params()
        if action == 'create':
            b_command.remove(b'--detach=True')
        full_cmd = " ".join([self.module_params['executable']]
                            + [to_native(i) for i in b_command])
        self.actions.append(full_cmd)
        if self.module.check_mode:
            self.module.log(
                "PODMAN-CONTAINER-DEBUG (check_mode): %s" % full_cmd)
        else:
            rc, out, err = self.module.run_command(
                [self.module_params['executable'], b'container'] + b_command,
                expand_user_and_vars=False)
            self.module.log("PODMAN-CONTAINER-DEBUG: %s" % full_cmd)
            if self.module_params['debug']:
                self.module.log("PODMAN-CONTAINER-DEBUG STDOUT: %s" % out)
                self.module.log("PODMAN-CONTAINER-DEBUG STDERR: %s" % err)
                self.module.log("PODMAN-CONTAINER-DEBUG RC: %s" % rc)
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
        self.start()


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
            'changed': False,
            'actions': [],
            'container': {},
        }
        self.module_params = params
        self.name = self.module_params['name']
        self.executable = \
            self.module.get_bin_path(self.module_params['executable'],
                                     required=True)
        self.image = self.module_params['image']
        image_actions = ensure_image_exists(
            self.module, self.image, self.module_params)
        self.results['actions'] += image_actions
        self.state = self.module_params['state']
        self.restart = self.module_params['force_restart']
        self.recreate = self.module_params['recreate']
        self.container = PodmanContainer(
            self.module, self.name, self.module_params)

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
        if self.module.params['debug'] or self.module_params['debug']:
            self.results.update({'podman_version': self.container.version})

    def make_started(self):
        """Run actions if desired state is 'started'."""
        if self.container.running and \
                (self.container.different or self.recreate):
            self.container.recreate()
            self.results['actions'].append('recreated %s' %
                                           self.container.name)
            self.update_container_result()
            return
        elif self.container.running and not self.container.different:
            if self.restart:
                self.container.restart()
                self.results['actions'].append('restarted %s' %
                                               self.container.name)
                self.update_container_result()
                return
            self.update_container_result(changed=False)
            return
        elif not self.container.exists:
            self.container.run()
            self.results['actions'].append('started %s' % self.container.name)
            self.update_container_result()
            return
        elif self.container.stopped and self.container.different:
            self.container.recreate()
            self.results['actions'].append('recreated %s' %
                                           self.container.name)
            self.update_container_result()
            return
        elif self.container.stopped and not self.container.different:
            self.container.start()
            self.results['actions'].append('started %s' % self.container.name)
            self.update_container_result()
            return

    def make_stopped(self):
        """Run actions if desired state is 'stopped'."""
        if not self.container.exists and not self.image:
            self.module.fail_json(msg='Cannot create container when image'
                                      ' is not specified!')
        if not self.container.exists:
            self.container.create()
            self.results['actions'].append('created %s' % self.container.name)
            self.update_container_result()
            return
        if self.container.stopped:
            self.update_container_result(changed=False)
            return
        elif self.container.running:
            self.container.stop()
            self.results['actions'].append('stopped %s' % self.container.name)
            self.update_container_result()
            return

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
        return self.results
