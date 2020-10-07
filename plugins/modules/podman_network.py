#!/usr/bin/python
# Copyright (c) 2020 Red Hat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r"""
module: podman_network
author:
  - "Sagi Shnaidman (@sshnaidm)"
version_added: '1.0.0'
short_description: Manage podman networks
notes: []
description:
  - Manage podman networks with podman network command.
requirements:
  - podman
options:
  name:
    description:
      - Name of the network
    type: str
    required: True
  executable:
    description:
      - Path to C(podman) executable if it is not in the C($PATH) on the
        machine running C(podman)
    default: 'podman'
    type: str
  disable_dns:
    description:
      - disable dns plugin (default "false")
    type: bool
  driver:
    description:
      - Driver to manage the network (default "bridge")
    type: str
  gateway:
    description:
      - IPv4 or IPv6 gateway for the subnet
    type: str
  internal:
    description:
      - Restrict external access from this network (default "false")
    type: bool
  ip_range:
    description:
      - Allocate container IP from range
    type: str
  subnet:
    description:
      - Subnet in CIDR format
    type: str
  macvlan:
    description:
      - Create a Macvlan connection based on this device
    type: str
  debug:
    description:
      - Return additional information which can be helpful for investigations.
    type: bool
    default: False
  state:
    description:
      - State of network, default 'present'
    type: str
    default: present
    choices:
      - present
      - absent
  recreate:
    description:
      - Recreate volume even if exists.
    type: bool
    default: false
"""

EXAMPLES = r"""
- name: Create a podman network
  containers.podman.podman_network:
    name: podman_network
  become: true

- name: Create internal podman network
  containers.podman.podman_network:
    name: podman_internal
    internal: true
    ip_range: 192.168.22.50-192.168.22.150
    subnet: 192.168.22.0/24
    gateway: 192.168.22.1
  become: true
"""

RETURN = r"""
network:
    description: Facts from created or updated networks
    returned: always
    type: list
    sample: [
              {
                "cniVersion": "0.4.0",
                "name": "podman",
                "plugins": [
                    {
                        "bridge": "cni-podman0",
                        "ipMasq": true,
                        "ipam": {
                            "ranges": [
                                [
                                    {
                                        "gateway": "10.88.0.1",
                                        "subnet": "10.88.0.0/16"
                                    }
                                ]
                            ],
                            "routes": [
                                {
                                    "dst": "0.0.0.0/0"
                                }
                            ],
                            "type": "host-local"
                        },
                        "isGateway": true,
                        "type": "bridge"
                    },
                    {
                        "capabilities": {
                            "portMappings": true
                        },
                        "type": "portmap"
                    },
                    {
                        "backend": "iptables",
                        "type": "firewall"
                    }
                ]
            }
        ]
"""

# noqa: F402
import json  # noqa: F402
from distutils.version import LooseVersion  # noqa: F402
import os  # noqa: F402

from ansible.module_utils.basic import AnsibleModule  # noqa: F402
from ansible.module_utils._text import to_bytes, to_native  # noqa: F402

from ansible_collections.containers.podman.plugins.module_utils.podman.common import lower_keys


class PodmanNetworkModuleParams:
    """Creates list of arguments for podman CLI command.

       Arguments:
           action {str} -- action type from 'create', 'delete'
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
        if self.action in ['delete']:
            return self._simple_action()
        if self.action in ['create']:
            return self._create_action()

    def _simple_action(self):
        if self.action == 'delete':
            cmd = ['rm', '-f', self.params['name']]
            return [to_bytes(i, errors='surrogate_or_strict') for i in cmd]

    def _create_action(self):
        cmd = [self.action, self.params['name']]
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

    def addparam_gateway(self, c):
        return c + ['--gateway', self.params['gateway']]

    def addparam_driver(self, c):
        return c + ['--driver', self.params['driver']]

    def addparam_subnet(self, c):
        return c + ['--subnet', self.params['subnet']]

    def addparam_ip_range(self, c):
        return c + ['--ip-range', self.params['ip_range']]

    def addparam_macvlan(self, c):
        return c + ['--macvlan', self.params['macvlan']]

    def addparam_internal(self, c):
        return c + ['--internal=%s' % self.params['internal']]

    def addparam_disable_dns(self, c):
        return c + ['--disable-dns=%s' % self.params['disable_dns']]


class PodmanNetworkDefaults:
    def __init__(self, module, podman_version):
        self.module = module
        self.version = podman_version
        self.defaults = {
            'driver': 'bridge',
            'disable_dns': False,
            'internal': False,
        }

    def default_dict(self):
        # make here any changes to self.defaults related to podman version
        return self.defaults


class PodmanNetworkDiff:
    def __init__(self, module, info, podman_version):
        self.module = module
        self.version = podman_version
        self.default_dict = None
        self.info = lower_keys(info)
        self.params = self.defaultize()
        self.diff = {'before': {}, 'after': {}}
        self.non_idempotent = {}

    def defaultize(self):
        params_with_defaults = {}
        self.default_dict = PodmanNetworkDefaults(
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

    def diffparam_disable_dns(self):
        dns_installed = False
        for f in [
            '/usr/libexec/cni/dnsname',
            '/usr/lib/cni/dnsname',
            '/opt/cni/bin/dnsname',
            '/opt/bridge/bin/dnsname'
        ]:
            if os.path.exists(f):
                dns_installed = True
        before = not bool(
            [k for k in self.info['plugins'] if 'domainname' in k])
        after = self.params['disable_dns']
        # If dnsname plugin is not installed, default is disable_dns=True
        if not dns_installed and self.module.params['disable_dns'] is None:
            after = True
        return self._diff_update_and_compare('disable_dns', before, after)

    def diffparam_driver(self):
        # Currently only bridge is supported
        before = after = 'bridge'
        return self._diff_update_and_compare('driver', before, after)

    def diffparam_gateway(self):
        try:
            before = self.info['plugins'][0]['ipam']['ranges'][0][0]['gateway']
        except (IndexError, KeyError):
            before = ''
        after = before
        if self.params['gateway'] is not None:
            after = self.params['gateway']
        return self._diff_update_and_compare('gateway', before, after)

    def diffparam_internal(self):
        try:
            before = not self.info['plugins'][0]['isgateway']
        except (IndexError, KeyError):
            before = False
        after = self.params['internal']
        return self._diff_update_and_compare('internal', before, after)

    def diffparam_ip_range(self):
        # TODO(sshnaidm): implement IP to CIDR convert and vice versa
        before = after = ''
        return self._diff_update_and_compare('ip_range', before, after)

    def diffparam_subnet(self):
        try:
            before = self.info['plugins'][0]['ipam']['ranges'][0][0]['subnet']
        except (IndexError, KeyError):
            before = ''
        after = before
        if self.params['subnet'] is not None:
            after = self.params['subnet']
        return self._diff_update_and_compare('subnet', before, after)

    def diffparam_macvlan(self):
        before = after = ''
        return self._diff_update_and_compare('macvlan', before, after)

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


class PodmanNetwork:
    """Perform network tasks.

    Manages podman network, inspects it and checks its current state
    """

    def __init__(self, module, name):
        """Initialize PodmanNetwork class.

        Arguments:
            module {obj} -- ansible module object
            name {str} -- name of network
        """

        super(PodmanNetwork, self).__init__()
        self.module = module
        self.name = name
        self.stdout, self.stderr = '', ''
        self.info = self.get_info()
        self.version = self._get_podman_version()
        self.diff = {}
        self.actions = []

    @property
    def exists(self):
        """Check if network exists."""
        return bool(self.info != {})

    @property
    def different(self):
        """Check if network is different."""
        diffcheck = PodmanNetworkDiff(
            self.module,
            self.info,
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

    def get_info(self):
        """Inspect network and gather info about it."""
        # pylint: disable=unused-variable
        rc, out, err = self.module.run_command(
            [self.module.params['executable'], b'network', b'inspect', self.name])
        return json.loads(out)[0] if rc == 0 else {}

    def _get_podman_version(self):
        # pylint: disable=unused-variable
        rc, out, err = self.module.run_command(
            [self.module.params['executable'], b'--version'])
        if rc != 0 or not out or "version" not in out:
            self.module.fail_json(msg="%s run failed!" %
                                  self.module.params['executable'])
        return out.split("version")[1].strip()

    def _perform_action(self, action):
        """Perform action with network.

        Arguments:
            action {str} -- action to perform - create, stop, delete
        """
        b_command = PodmanNetworkModuleParams(action,
                                              self.module.params,
                                              self.version,
                                              self.module,
                                              ).construct_command_from_params()
        full_cmd = " ".join([self.module.params['executable'], 'network']
                            + [to_native(i) for i in b_command])
        self.module.log("PODMAN-NETWORK-DEBUG: %s" % full_cmd)
        self.actions.append(full_cmd)
        if not self.module.check_mode:
            rc, out, err = self.module.run_command(
                [self.module.params['executable'], b'network'] + b_command,
                expand_user_and_vars=False)
            self.stdout = out
            self.stderr = err
            if rc != 0:
                self.module.fail_json(
                    msg="Can't %s network %s" % (action, self.name),
                    stdout=out, stderr=err)

    def delete(self):
        """Delete the network."""
        self._perform_action('delete')

    def create(self):
        """Create the network."""
        self._perform_action('create')

    def recreate(self):
        """Recreate the network."""
        self.delete()
        self.create()


class PodmanNetworkManager:
    """Module manager class.

    Defines according to parameters what actions should be applied to network
    """

    def __init__(self, module):
        """Initialize PodmanManager class.

        Arguments:
            module {obj} -- ansible module object
        """

        super(PodmanNetworkManager, self).__init__()

        self.module = module
        self.results = {
            'changed': False,
            'actions': [],
            'network': {},
        }
        self.name = self.module.params['name']
        self.executable = \
            self.module.get_bin_path(self.module.params['executable'],
                                     required=True)
        self.state = self.module.params['state']
        self.recreate = self.module.params['recreate']
        self.network = PodmanNetwork(self.module, self.name)

    def update_network_result(self, changed=True):
        """Inspect the current network, update results with last info, exit.

        Keyword Arguments:
            changed {bool} -- whether any action was performed
                              (default: {True})
        """
        facts = self.network.get_info() if changed else self.network.info
        out, err = self.network.stdout, self.network.stderr
        self.results.update({'changed': changed, 'network': facts,
                             'podman_actions': self.network.actions},
                            stdout=out, stderr=err)
        if self.network.diff:
            self.results.update({'diff': self.network.diff})
        if self.module.params['debug']:
            self.results.update({'podman_version': self.network.version})
        self.module.exit_json(**self.results)

    def execute(self):
        """Execute the desired action according to map of actions & states."""
        states_map = {
            'present': self.make_present,
            'absent': self.make_absent,
        }
        process_action = states_map[self.state]
        process_action()
        self.module.fail_json(msg="Unexpected logic error happened, "
                                  "please contact maintainers ASAP!")

    def make_present(self):
        """Run actions if desired state is 'started'."""
        if not self.network.exists:
            self.network.create()
            self.results['actions'].append('created %s' % self.network.name)
            self.update_network_result()
        elif self.recreate or self.network.different:
            self.network.recreate()
            self.results['actions'].append('recreated %s' %
                                           self.network.name)
            self.update_network_result()
        else:
            self.update_network_result(changed=False)

    def make_absent(self):
        """Run actions if desired state is 'absent'."""
        if not self.network.exists:
            self.results.update({'changed': False})
        elif self.network.exists:
            self.network.delete()
            self.results['actions'].append('deleted %s' % self.network.name)
            self.results.update({'changed': True})
        self.results.update({'network': {},
                             'podman_actions': self.network.actions})
        self.module.exit_json(**self.results)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(type='str', default="present",
                       choices=['present', 'absent']),
            name=dict(type='str', required=True),
            disable_dns=dict(type='bool', required=False),
            driver=dict(type='str', required=False),
            gateway=dict(type='str', required=False),
            internal=dict(type='bool', required=False),
            ip_range=dict(type='str', required=False),
            subnet=dict(type='str', required=False),
            macvlan=dict(type='str', required=False),
            executable=dict(type='str', required=False, default='podman'),
            debug=dict(type='bool', default=False),
            recreate=dict(type='bool', default=False),
        ),
        required_by=dict(  # for IP range to set 'subnet' is required
            ip_range=('subnet'),
        ))

    PodmanNetworkManager(module).execute()


if __name__ == '__main__':
    main()
