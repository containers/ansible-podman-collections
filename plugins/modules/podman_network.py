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
  force:
    description:
      - Remove all containers that use the network.
        If the container is running, it is stopped and removed.
    default: False
    type: bool
  gateway:
    description:
      - IPv4 or IPv6 gateway for the subnet
    type: str
  interface_name:
    description:
      - For bridge, it uses the bridge interface name.
        For macvlan, it is the parent device on the host (it is the same
        as 'opt.parent')
    type: str
  internal:
    description:
      - Restrict external access from this network (default "false")
    type: bool
  ip_range:
    description:
      - Allocate container IP from range
    type: str
  ipv6:
    description:
      - Enable IPv6 (Dual Stack) networking. You must pass a IPv6 subnet.
        The subnet option must be used with the ipv6 option.
    type: bool
  subnet:
    description:
      - Subnet in CIDR format
    type: str
  macvlan:
    description:
      - Create a Macvlan connection based on this device
    type: str
  opt:
    description:
      - Add network options. Currently 'vlan' and 'mtu' are supported.
    type: dict
    suboptions:
      isolate:
        description:
          - This option isolates networks by blocking traffic between those
            that have this option enabled.
        type: bool
        required: false
      metric:
        description:
          - Sets the Route Metric for the default route created in every
            container joined to this network.
            Can only be used with the Netavark network backend.
        type: int
        required: false
      mode:
        description:
          - This option sets the specified ip/macvlan mode on the interface.
        type: str
        required: false
      mtu:
        description:
          - MTU size for bridge network interface.
        type: int
        required: false
      parent:
        description:
          - The host device which should be used for the macvlan interface
            (it is the same as 'interface' in that case).
            Defaults to the default route interface.
        type: str
        required: false
      vlan:
        description:
          - VLAN tag for bridge which enables vlan_filtering.
        type: int
        required: false
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
      - Recreate network even if exists.
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
    ip_range: 192.168.22.128/25
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

import json  # noqa: F402
try:
    import ipaddress
    HAS_IP_ADDRESS_MODULE = True
except ImportError:
    HAS_IP_ADDRESS_MODULE = False

from ansible.module_utils.basic import AnsibleModule  # noqa: F402
from ansible.module_utils._text import to_bytes, to_native  # noqa: F402
from ansible_collections.containers.podman.plugins.module_utils.podman.common import LooseVersion
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
            return self._delete_action()
        if self.action in ['create']:
            return self._create_action()

    def _delete_action(self):
        cmd = ['rm', self.params['name']]
        if self.params['force']:
            cmd += ['--force']
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

    def addparam_ipv6(self, c):
        return c + ['--ipv6=%s' % self.params['ipv6']]

    def addparam_macvlan(self, c):
        return c + ['--macvlan', self.params['macvlan']]

    def addparam_interface_name(self, c):
        return c + ['--interface-name', self.params['interface_name']]

    def addparam_internal(self, c):
        return c + ['--internal=%s' % self.params['internal']]

    def addparam_opt(self, c):
        for opt in self.params['opt'].items():
            if opt[1] is not None:
                c += ['--opt',
                      b"=".join([to_bytes(k, errors='surrogate_or_strict')
                                 for k in opt])]
        return c

    def addparam_disable_dns(self, c):
        return c + ['--disable-dns=%s' % self.params['disable_dns']]


class PodmanNetworkDefaults:
    def __init__(self, module, podman_version):
        self.module = module
        self.version = podman_version
        self.defaults = {
            'driver': 'bridge',
            'internal': False,
            'ipv6': False
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
        # For v3 it's impossible to find out DNS settings.
        if LooseVersion(self.version) >= LooseVersion('4.0.0'):
            before = not self.info.get('dns_enabled', True)
            after = self.params['disable_dns']
            # compare only if set explicitly
            if self.params['disable_dns'] is None:
                after = before
            return self._diff_update_and_compare('disable_dns', before, after)
        before = after = self.params['disable_dns']
        return self._diff_update_and_compare('disable_dns', before, after)

    def diffparam_driver(self):
        # Currently only bridge is supported
        before = after = 'bridge'
        return self._diff_update_and_compare('driver', before, after)

    def diffparam_ipv6(self):
        if LooseVersion(self.version) >= LooseVersion('4.0.0'):
            before = self.info.get('ipv6_enabled', False)
            after = self.params['ipv6']
            return self._diff_update_and_compare('ipv6', before, after)
        before = after = ''
        return self._diff_update_and_compare('ipv6', before, after)

    def diffparam_gateway(self):
        # Disable idempotency of subnet for v4, subnets are added automatically
        # TODO(sshnaidm): check if it's still the issue in v5
        if LooseVersion(self.version) >= LooseVersion('4.0.0'):
            return self._diff_update_and_compare('gateway', '', '')
        try:
            before = self.info['plugins'][0]['ipam']['ranges'][0][0]['gateway']
        except (IndexError, KeyError):
            before = ''
        after = before
        if self.params['gateway'] is not None:
            after = self.params['gateway']
        return self._diff_update_and_compare('gateway', before, after)

    def diffparam_internal(self):
        if LooseVersion(self.version) >= LooseVersion('4.0.0'):
            before = self.info.get('internal', False)
            after = self.params['internal']
            return self._diff_update_and_compare('internal', before, after)
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
        # Disable idempotency of subnet for v4, subnets are added automatically
        # TODO(sshnaidm): check if it's still the issue in v5
        if LooseVersion(self.version) >= LooseVersion('4.0.0'):
            return self._diff_update_and_compare('subnet', '', '')
        try:
            before = self.info['plugins'][0]['ipam']['ranges'][0][0]['subnet']
        except (IndexError, KeyError):
            before = ''
        after = before
        if self.params['subnet'] is not None:
            after = self.params['subnet']
            if HAS_IP_ADDRESS_MODULE:
                after = ipaddress.ip_network(after).compressed
        return self._diff_update_and_compare('subnet', before, after)

    def diffparam_macvlan(self):
        before = after = ''
        return self._diff_update_and_compare('macvlan', before, after)

    def diffparam_opt(self):
        if LooseVersion(self.version) >= LooseVersion('4.0.0'):
            vlan_before = self.info.get('options', {}).get('vlan')
        else:
            try:
                vlan_before = self.info['plugins'][0].get('vlan')
            except (IndexError, KeyError):
                vlan_before = None
        vlan_after = self.params['opt'].get('vlan') if self.params['opt'] else None
        if vlan_before or vlan_after:
            before, after = {'vlan': str(vlan_before)}, {'vlan': str(vlan_after)}
        else:
            before, after = {}, {}
        if LooseVersion(self.version) >= LooseVersion('4.0.0'):
            mtu_before = self.info.get('options', {}).get('mtu')
        else:
            try:
                mtu_before = self.info['plugins'][0].get('mtu')
            except (IndexError, KeyError):
                mtu_before = None
        mtu_after = self.params['opt'].get('mtu') if self.params['opt'] else None
        if mtu_before or mtu_after:
            before.update({'mtu': str(mtu_before)})
            after.update({'mtu': str(mtu_after)})
        return self._diff_update_and_compare('opt', before, after)

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
            force=dict(type='bool', default=False),
            gateway=dict(type='str', required=False),
            interface_name=dict(type='str', required=False),
            internal=dict(type='bool', required=False),
            ip_range=dict(type='str', required=False),
            ipv6=dict(type='bool', required=False),
            subnet=dict(type='str', required=False),
            macvlan=dict(type='str', required=False),
            opt=dict(type='dict', required=False,
                     options=dict(
                         isolate=dict(type='bool', required=False),
                         mtu=dict(type='int', required=False),
                         metric=dict(type='int', required=False),
                         mode=dict(type='str', required=False),
                         parent=dict(type='str', required=False),
                         vlan=dict(type='int', required=False),
                     )),
            executable=dict(type='str', required=False, default='podman'),
            debug=dict(type='bool', default=False),
            recreate=dict(type='bool', default=False),
        ),
        required_by=dict(  # for IP range and GW to set 'subnet' is required
            ip_range=('subnet'),
            gateway=('subnet'),
        ))

    PodmanNetworkManager(module).execute()


if __name__ == '__main__':
    main()
