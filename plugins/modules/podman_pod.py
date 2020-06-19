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
# noqa: F402
import json  # noqa: F402
from distutils.version import LooseVersion  # noqa: F402
import yaml  # noqa: F402

from ansible.module_utils.basic import AnsibleModule  # noqa: F402
from ansible.module_utils._text import to_bytes, to_native  # noqa: F402


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
        if self.action in ['start', 'restart', 'stop', 'delete', 'pause',
                           'unpause', 'kill']:
            return self._simple_action()
        if self.action in ['create']:
            return self._create_action()
        self.module.fail_json(msg="Unknown action %s" % self.action)

    def _simple_action(self):
        if self.action in ['start', 'restart', 'stop', 'pause', 'unpause', 'kill']:
            cmd = [self.action, self.params['name']]
            return [to_bytes(i, errors='surrogate_or_strict') for i in cmd]

        if self.action == 'delete':
            cmd = ['rm', '-f', self.params['name']]
            return [to_bytes(i, errors='surrogate_or_strict') for i in cmd]
        self.module.fail_json(msg="Unknown action %s" % self.action)

    def _create_action(self):
        cmd = [self.action]
        all_param_methods = [func for func in dir(self)
                             if callable(getattr(self, func))
                             and func.startswith("addparam")]
        params_set = (i for i in self.params if self.params[i] is not None)
        for param in params_set:
            func_name = "_".join(["addparam", param])
            if func_name in all_param_methods:
                cmd = getattr(self, func_name)(cmd)
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

    def addparam_add_host(self, c):
        for g in self.params['add_host']:
            c += ['--add-host', g]
        return c

    def addparam_cgroup_parent(self, c):
        return c + ['--cgroup-parent', self.params['cgroup_parent']]

    def addparam_dns(self, c):
        for g in self.params['dns']:
            c += ['--dns', g]
        return c

    def addparam_dns_opt(self, c):
        for g in self.params['dns_opt']:
            c += ['--dns-opt', g]
        return c

    def addparam_dns_search(self, c):
        for g in self.params['dns_search']:
            c += ['--dns-search', g]
        return c

    def addparam_hostname(self, c):
        return c + ['--hostname', self.params['hostname']]

    def addparam_infra(self, c):
        return c + [b'='.join([b'--infra',
                              to_bytes(self.params['infra'],
                                       errors='surrogate_or_strict')])]

    def addparam_infra_conmon_pidfile(self, c):
        return c + ['--infra-conmon-pidfile', self.params['infra_conmon_pidfile']]

    def addparam_infra_command(self, c):
        return c + ['--infra-command', self.params['infra_command']]

    def addparam_infra_image(self, c):
        return c + ['--infra-image', self.params['infra_image']]

    def addparam_ip(self, c):
        return c + ['--ip', self.params['ip']]

    def addparam_label(self, c):
        for label in self.params['label'].items():
            c += ['--label', b'='.join(
                [to_bytes(l, errors='surrogate_or_strict') for l in label])]
        return c

    def addparam_label_file(self, c):
        return c + ['--label-file', self.params['label_file']]

    def addparam_mac_address(self, c):
        return c + ['--mac-address', self.params['mac_address']]

    def addparam_name(self, c):
        return c + ['--name', self.params['name']]

    def addparam_network(self, c):
        return c + ['--network', self.params['network']]

    def addparam_no_hosts(self, c):
        return c + ["=".join('--no-hosts', self.params['no_hosts'])]

    def addparam_pod_id_file(self, c):
        return c + ['--pod-id-file', self.params['pod_id_file']]

    def addparam_publish(self, c):
        for g in self.params['publish']:
            c += ['--publish', g]
        return c

    def addparam_share(self, c):
        return c + ['--share', self.params['share']]


class PodmanPodDefaults:
    def __init__(self, module, podman_version):
        self.module = module
        self.version = podman_version
        self.defaults = {
            'add_host': [],
            'dns': [],
            'dns_opt': [],
            'dns_search': [],
            'infra': True,
            'label': {},
        }

    def default_dict(self):
        # make here any changes to self.defaults related to podman version
        # https://github.com/containers/libpod/pull/5669
        # if (LooseVersion(self.version) >= LooseVersion('1.8.0')
        #         and LooseVersion(self.version) < LooseVersion('1.9.0')):
        #     self.defaults['cpu_shares'] = 1024
        return self.defaults


class PodmanPodDiff:
    def __init__(self, module, info, infra_info, podman_version):
        self.module = module
        self.version = podman_version
        self.default_dict = None
        self.info = yaml.safe_load(json.dumps(info).lower())
        self.infra_info = yaml.safe_load(json.dumps(infra_info).lower())
        self.params = self.defaultize()
        self.diff = {'before': {}, 'after': {}}
        self.non_idempotent = {}

    def defaultize(self):
        params_with_defaults = {}
        self.default_dict = PodmanPodDefaults(
            self.module, self.version).default_dict()
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

    def diffparam_add_host(self):
        if not self.infra_info:
            return self._diff_update_and_compare('add_host', '', '')
        before = self.infra_info['hostconfig']['extrahosts'] or []
        after = self.params['add_host']
        before, after = sorted(list(set(before))), sorted(list(set(after)))
        return self._diff_update_and_compare('add_host', before, after)

    def diffparam_cgroup_parent(self):
        if 'cgroupparent' in self.info:
            before = self.info['cgroupparent']
        elif 'config' in self.info and self.info['config'].get('cgroupparent'):
            before = self.info['config']['cgroupparent']
        after = self.params['cgroup_parent'] or before
        return self._diff_update_and_compare('cgroup_parent', before, after)

    def diffparam_dns(self):
        if not self.infra_info:
            return self._diff_update_and_compare('dns', '', '')
        before = self.infra_info['hostconfig']['dns'] or []
        after = self.params['dns']
        before, after = sorted(list(set(before))), sorted(list(set(after)))
        return self._diff_update_and_compare('dns', before, after)

    def diffparam_dns_opt(self):
        if not self.infra_info:
            return self._diff_update_and_compare('dns_opt', '', '')
        before = self.infra_info['hostconfig']['dnsoptions'] or []
        after = self.params['dns_opt']
        before, after = sorted(list(set(before))), sorted(list(set(after)))
        return self._diff_update_and_compare('dns_opt', before, after)

    def diffparam_dns_search(self):
        if not self.infra_info:
            return self._diff_update_and_compare('dns_search', '', '')
        before = self.infra_info['hostconfig']['dnssearch'] or []
        after = self.params['dns_search']
        before, after = sorted(list(set(before))), sorted(list(set(after)))
        return self._diff_update_and_compare('dns_search', before, after)

    def diffparam_hostname(self):
        if not self.infra_info:
            return self._diff_update_and_compare('hostname', '', '')
        before = self.infra_info['config']['hostname']
        after = self.params['hostname'] or before
        return self._diff_update_and_compare('hostname', before, after)

    # TODO(sshnaidm): https://github.com/containers/podman/issues/6968
    def diffparam_infra(self):
        if 'state' in self.info and 'infracontainerid' in self.info['state']:
            before = self.info['state']['infracontainerid'] != ""
        else:
            # TODO(sshnaidm): https://github.com/containers/podman/issues/6968
            before = 'infracontainerid' in self.info
        after = self.params['infra']
        return self._diff_update_and_compare('infra', before, after)

    # TODO(sshnaidm): https://github.com/containers/podman/issues/6969
    # def diffparam_infra_command(self):
    #     before = str(self.info['hostconfig']['infra_command'])
    #     after = self.params['infra_command']
    #     return self._diff_update_and_compare('infra_command', before, after)

    def diffparam_infra_image(self):
        if not self.infra_info:
            return self._diff_update_and_compare('infra_image', '', '')
        before = str(self.infra_info['imagename'])
        after = before
        if self.module.params['infra_image']:
            after = self.params['infra_image']
        before = before.replace(":latest", "")
        after = after.replace(":latest", "")
        before = before.split("/")[-1]
        after = after.split("/")[-1]
        return self._diff_update_and_compare('infra_image', before, after)

    # TODO(sshnaidm): https://github.com/containers/podman/pull/6956
    # def diffparam_ip(self):
    #     before = str(self.info['hostconfig']['ip'])
    #     after = self.params['ip']
    #     return self._diff_update_and_compare('ip', before, after)

    def diffparam_label(self):
        if 'config' in self.info and 'labels' in self.info['config']:
            before = self.info['config'].get('labels') or {}
        else:
            before = self.info['labels'] if 'labels' in self.info else {}
        after = self.params['label']
        return self._diff_update_and_compare('label', before, after)

    # TODO(sshnaidm): https://github.com/containers/podman/pull/6956
    # def diffparam_mac_address(self):
    #     before = str(self.info['hostconfig']['mac_address'])
    #     after = self.params['mac_address']
    #     return self._diff_update_and_compare('mac_address', before, after)

    def diffparam_network(self):
        if not self.infra_info:
            return self._diff_update_and_compare('network', [], [])
        net_mode_before = self.infra_info['hostconfig']['networkmode']
        net_mode_after = ''
        before = self.infra_info['networksettings'].get('networks', [])
        after = self.params['network']
        # Currently supported only 'host' and 'none' network modes idempotency
        if after in ['bridge', 'host', 'slirp4netns']:
            net_mode_after = after
        elif after:
            after = after.split(",")
        else:
            after = []
        if net_mode_after and not before:
            # Remove differences between v1 and v2
            net_mode_after = net_mode_after.replace('bridge', 'default')
            net_mode_after = net_mode_after.replace('slirp4netns', 'default')
            net_mode_before = net_mode_before.replace('bridge', 'default')
            net_mode_before = net_mode_before.replace('slirp4netns', 'default')
            return self._diff_update_and_compare('network', net_mode_before, net_mode_after)
        before, after = sorted(list(set(before))), sorted(list(set(after)))
        return self._diff_update_and_compare('network', before, after)

    # TODO(sshnaidm)
    # def diffparam_no_hosts(self):
    #     before = str(self.info['hostconfig']['no_hosts'])
    #     after = self.params['no_hosts']
    #     return self._diff_update_and_compare('no_hosts', before, after)

    # TODO(sshnaidm) Need to add port ranges support
    def diffparam_publish(self):
        if not self.infra_info:
            return self._diff_update_and_compare('publish', '', '')
        ports = self.infra_info['hostconfig']['portbindings']
        before = [":".join([
            j[0]['hostip'],
            str(j[0]["hostport"]),
            i.replace('/tcp', '')
        ]).strip(':') for i, j in ports.items()]
        after = self.params['publish'] or []
        after = [i.replace("/tcp", "") for i in after]
        # No support for port ranges yet
        for ports in after:
            if "-" in ports:
                return self._diff_update_and_compare('publish', '', '')
        before, after = sorted(list(set(before))), sorted(list(set(after)))
        return self._diff_update_and_compare('publish', before, after)

    def diffparam_share(self):
        if not self.infra_info:
            return self._diff_update_and_compare('share', '', '')
        if 'sharednamespaces' in self.info:
            before = self.info['sharednamespaces']
        elif 'config' in self.info:
            before = [
                i.split('shares')[1].lower()
                for i in self.info['config'] if 'shares' in i]
            # TODO(sshnaidm): to discover why in podman v1 'cgroup' appears
            before.remove('cgroup')
        else:
            before = []
        if self.params['share'] is not None:
            after = self.params['share'].split(",")
        else:
            after = ['uts', 'ipc', 'net']
        before, after = sorted(list(set(before))), sorted(list(set(after)))
        return self._diff_update_and_compare('share', before, after)

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


class PodmanPod:
    """Perform pod tasks.

    Manages podman pod, inspects it and checks its current state
    """

    def __init__(self, module, name):
        """Initialize PodmanPod class.

        Arguments:
            module {obj} -- ansible module object
            name {str} -- name of pod
        """

        super(PodmanPod, self).__init__()
        self.module = module
        self.name = name
        self.stdout, self.stderr = '', ''
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
        diffcheck = PodmanPodDiff(
            self.module,
            self.info,
            self.infra_info,
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
        """Return True if pod is running now."""
        if 'status' in self.info['State']:
            return self.info['State']['status'] == 'Running'
        return self.info['State'] == 'Running'

    @property
    def paused(self):
        """Return True if pod is paused now."""
        if 'status' in self.info['State']:
            return self.info['State']['status'] == 'Paused'
        return self.info['State'] == 'Paused'

    @property
    def stopped(self):
        """Return True if pod exists and is not running now."""
        if not self.exists:
            return False
        if 'status' in self.info['State']:
            return not (self.info['State']['status'] == 'Running')
        return not (self.info['State'] == 'Running')

    def get_info(self):
        """Inspect pod and gather info about it."""
        # pylint: disable=unused-variable
        rc, out, err = self.module.run_command(
            [self.module.params['executable'], b'pod', b'inspect', self.name])
        return json.loads(out) if rc == 0 else {}

    def get_infra_info(self):
        """Inspect pod and gather info about it."""
        if not self.info:
            return {}
        if 'InfraContainerID' in self.info:
            infra_container_id = self.info['InfraContainerID']
        elif 'State' in self.info and 'infraContainerID' in self.info['State']:
            infra_container_id = self.info['State']['infraContainerID']
        else:
            return {}
        # pylint: disable=unused-variable
        rc, out, err = self.module.run_command(
            [self.module.params['executable'], b'inspect', infra_container_id])
        return json.loads(out)[0] if rc == 0 else {}

    def _get_podman_version(self):
        # pylint: disable=unused-variable
        rc, out, err = self.module.run_command(
            [self.module.params['executable'], b'--version'])
        if rc != 0 or not out or "version" not in out:
            self.module.fail_json(msg="%s run failed!" % self.module.params['executable'])
        return out.split("version")[1].strip()

    def _perform_action(self, action):
        """Perform action with pod.

        Arguments:
            action {str} -- action to perform - start, create, stop, pause
                            unpause, delete, restart, kill
        """
        b_command = PodmanPodModuleParams(action,
                                          self.module.params,
                                          self.version,
                                          self.module,
                                          ).construct_command_from_params()
        full_cmd = " ".join([self.module.params['executable'], 'pod']
                            + [to_native(i) for i in b_command])
        self.module.log("PODMAN-POD-DEBUG: %s" % full_cmd)
        self.actions.append(full_cmd)
        if not self.module.check_mode:
            rc, out, err = self.module.run_command(
                [self.module.params['executable'], b'pod'] + b_command,
                expand_user_and_vars=False)
            self.stdout = out
            self.stderr = err
            if rc != 0:
                self.module.fail_json(
                    msg="Can't %s pod %s" % (action, self.name),
                    stdout=out, stderr=err)

    def delete(self):
        """Delete the pod."""
        self._perform_action('delete')

    def stop(self):
        """Stop the pod."""
        self._perform_action('stop')

    def start(self):
        """Start the pod."""
        self._perform_action('start')

    def create(self):
        """Create the pod."""
        self._perform_action('create')

    def recreate(self):
        """Recreate the pod."""
        self.delete()
        self.create()

    def restart(self):
        """Restart the pod."""
        self._perform_action('restart')

    def kill(self):
        """Kill the pod."""
        self._perform_action('kill')

    def pause(self):
        """Pause the pod."""
        self._perform_action('pause')

    def unpause(self):
        """Unpause the pod."""
        self._perform_action('unpause')


class PodmanPodManager:
    """Module manager class.

    Defines according to parameters what actions should be applied to pod
    """

    def __init__(self, module):
        """Initialize PodmanManager class.

        Arguments:
            module {obj} -- ansible module object
        """

        super(PodmanPodManager, self).__init__()

        self.module = module
        self.results = {
            'changed': False,
            'actions': [],
            'pod': {},
        }
        self.name = self.module.params['name']
        self.executable = \
            self.module.get_bin_path(self.module.params['executable'],
                                     required=True)
        self.state = self.module.params['state']
        self.recreate = self.module.params['recreate']
        self.pod = PodmanPod(self.module, self.name)

    def update_pod_result(self, changed=True):
        """Inspect the current pod, update results with last info, exit.

        Keyword Arguments:
            changed {bool} -- whether any action was performed
                              (default: {True})
        """
        facts = self.pod.get_info() if changed else self.pod.info
        out, err = self.pod.stdout, self.pod.stderr
        self.results.update({'changed': changed, 'pod': facts,
                             'podman_actions': self.pod.actions},
                            stdout=out, stderr=err)
        if self.pod.diff:
            self.results.update({'diff': self.pod.diff})
        if self.module.params['debug']:
            self.results.update({'podman_version': self.pod.version})
        self.module.exit_json(**self.results)

    def execute(self):
        """Execute the desired action according to map of actions & states."""
        states_map = {
            'created': self.make_created,
            'started': self.make_started,
            'stopped': self.make_stopped,
            'absent': self.make_absent,
            'killed': self.make_killed,
            'paused': self.make_paused,
            'unpaused': self.make_unpaused,

        }
        process_action = states_map[self.state]
        process_action()
        self.module.fail_json(msg="Unexpected logic error happened, "
                                  "please contact maintainers ASAP!")

    def _create_or_recreate_pod(self):
        """Ensure pod exists and is exactly as it should be by input params."""
        changed = False
        if self.pod.exists:
            if self.pod.different or self.recreate:
                self.pod.recreate()
                self.results['actions'].append('recreated %s' % self.pod.name)
                changed = True
        elif not self.pod.exists:
            self.pod.create()
            self.results['actions'].append('created %s' % self.pod.name)
            changed = True
        return changed

    def make_created(self):
        """Run actions if desired state is 'created'."""
        if self.pod.exists and not self.pod.different:
            self.update_pod_result(changed=False)
        self._create_or_recreate_pod()
        self.update_pod_result()

    def make_killed(self):
        """Run actions if desired state is 'killed'."""
        self._create_or_recreate_pod()
        self.pod.kill()
        self.results['actions'].append('killed %s' % self.pod.name)
        self.update_pod_result()

    def make_paused(self):
        """Run actions if desired state is 'paused'."""
        changed = self._create_or_recreate_pod()
        if self.pod.paused:
            self.update_pod_result(changed=changed)
        self.pod.pause()
        self.results['actions'].append('paused %s' % self.pod.name)
        self.update_pod_result()

    def make_unpaused(self):
        """Run actions if desired state is 'unpaused'."""
        changed = self._create_or_recreate_pod()
        if not self.pod.paused:
            self.update_pod_result(changed=changed)
        self.pod.unpause()
        self.results['actions'].append('unpaused %s' % self.pod.name)
        self.update_pod_result()

    def make_started(self):
        """Run actions if desired state is 'started'."""
        changed = self._create_or_recreate_pod()
        if not changed and self.pod.running:
            self.update_pod_result(changed=changed)
        # self.pod.unpause()  TODO(sshnaidm): to unpause if state == started?
        self.pod.start()
        self.results['actions'].append('started %s' % self.pod.name)
        self.update_pod_result()

    def make_stopped(self):
        """Run actions if desired state is 'stopped'."""
        changed = self._create_or_recreate_pod()
        if changed or self.pod.stopped:
            self.update_pod_result(changed=changed)
        elif self.pod.running:
            self.pod.stop()
            self.results['actions'].append('stopped %s' % self.pod.name)
            self.update_pod_result()

    def make_absent(self):
        """Run actions if desired state is 'absent'."""
        if not self.pod.exists:
            self.results.update({'changed': False})
        elif self.pod.exists:
            self.pod.delete()
            self.results['actions'].append('deleted %s' % self.pod.name)
            self.results.update({'changed': True})
        self.results.update({'pod': {},
                             'podman_actions': self.pod.actions})
        self.module.exit_json(**self.results)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(
                type='str',
                default="created",
                choices=[
                    'created',
                    'killed',
                    'restarted',
                    'absent',
                    'started',
                    'stopped',
                    'paused',
                    'unpaused',
                ]),
            recreate=dict(type='bool', default=False),
            add_host=dict(type='list', required=False, elements='str'),
            cgroup_parent=dict(type='str', required=False),
            dns=dict(type='list', elements='str', required=False),
            dns_opt=dict(type='list', elements='str', required=False),
            dns_search=dict(type='list', elements='str', required=False),
            hostname=dict(type='str', required=False),
            infra=dict(type='bool', required=False),
            infra_conmon_pidfile=dict(type='str', required=False),
            infra_command=dict(type='str', required=False),
            infra_image=dict(type='str', required=False),
            ip=dict(type='str', required=False),
            label=dict(type='dict', required=False),
            label_file=dict(type='str', required=False),
            mac_address=dict(type='str', required=False),
            name=dict(type='str', required=True),
            network=dict(type='str', required=False),
            no_hosts=dict(type='bool', required=False),
            pod_id_file=dict(type='str', required=False),
            publish=dict(type='list', required=False, elements='str', aliases=['ports']),
            share=dict(type='str', required=False),
            executable=dict(type='str', required=False, default='podman'),
            debug=dict(type='bool', default=False),
        )
        # ),

        # # Optional arguments requirements

        # required_if=[
        #     ['action', 'rebuild', ['image']],  # if need to rebuild image (only), the 'image' is required
        #     ["state", "present", ["username", "user_roles"]],  # for creating user 'user_roles' is required
        #     ["state", "absent", ["username"]],  # for state 'absent' only username is required
        # ],
        # required_by=dict(  # for weather and population 'city' is required to set
        #     weather=('city'),
        #     population=('city'),
        # ),
        # mutually_exclusive=[
        #     ['use_cloud1', 'use_cloud2']  # can't run on both, choose only one to set
        # ],
        # required_together=[
        #     ['remove_image', 'image_name']  # if need to remove image, must to specify which one
        # ],
        # required_one_of_args=[["password", "password_hash"]],  # one of these args must be set
        # supports_check_mode=True,  # good practice is to support check_mode
    )
    PodmanPodManager(module).execute()


if __name__ == '__main__':
    main()
