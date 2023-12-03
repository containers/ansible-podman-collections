#!/usr/bin/python
# Copyright (c) 2020 Red Hat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# flake8: noqa: E501
from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = '''
---
module: podman_volume
short_description: Manage Podman volumes
author:
  - "Sagi Shnaidman (@sshnaidm)"
version_added: '1.1.0'
description:
  - Manage Podman volumes
options:
  state:
    description:
      - State of volume, default 'present'
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
  name:
    description:
      - Name of volume.
    type: str
    required: true
  label:
    description:
      - Add metadata to a pod volume (e.g., label com.example.key=value).
    type: dict
    required: false
  driver:
    description:
      - Specify volume driver name (default local).
    type: str
    required: false
  options:
    description:
      - Set driver specific options. For example 'device=tpmfs', 'type=tmpfs'.
        UID and GID idempotency is not supported due to changes in podman.
    type: list
    elements: str
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
volume:
  description: Volume inspection results if exists.
  returned: always
  type: dict
  sample:
    CreatedAt: '2020-06-05T16:38:55.277628769+03:00'
    Driver: local
    Labels:
      key.com: value
      key.org: value2
    Mountpoint: /home/user/.local/share/containers/storage/volumes/test/_data
    Name: test
    Options: {}
    Scope: local

'''

EXAMPLES = '''
# What modules does for example
- podman_volume:
    state: present
    name: volume1
    label:
      key: value
      key2: value2
    options:
      - "device=/dev/loop1"
      - "type=ext4"
'''
# noqa: F402
import json  # noqa: F402

from ansible.module_utils.basic import AnsibleModule  # noqa: F402
from ansible.module_utils._text import to_bytes, to_native  # noqa: F402
from ansible_collections.containers.podman.plugins.module_utils.podman.common import LooseVersion
from ansible_collections.containers.podman.plugins.module_utils.podman.common import lower_keys


class PodmanVolumeModuleParams:
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

    def addparam_label(self, c):
        for label in self.params['label'].items():
            c += ['--label', b'='.join(
                [to_bytes(l, errors='surrogate_or_strict') for l in label])]
        return c

    def addparam_driver(self, c):
        return c + ['--driver', self.params['driver']]

    def addparam_options(self, c):
        for opt in self.params['options']:
            c += ['--opt', opt]
        return c


class PodmanVolumeDefaults:
    def __init__(self, module, podman_version):
        self.module = module
        self.version = podman_version
        self.defaults = {
            'driver': 'local',
            'label': {},
            'options': {}
        }

    def default_dict(self):
        # make here any changes to self.defaults related to podman version
        return self.defaults


class PodmanVolumeDiff:
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
        self.default_dict = PodmanVolumeDefaults(
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

    def diffparam_label(self):
        before = self.info['labels'] if 'labels' in self.info else {}
        after = self.params['label']
        return self._diff_update_and_compare('label', before, after)

    def diffparam_driver(self):
        before = self.info['driver']
        after = self.params['driver']
        return self._diff_update_and_compare('driver', before, after)

    def diffparam_options(self):
        before = self.info['options'] if 'options' in self.info else {}
        # Removing GID and UID from options list
        before.pop('uid', None)
        before.pop('gid', None)
        # Collecting all other options in the list
        before = ["=".join((k, v)) for k, v in before.items()]
        after = self.params['options']
        # # For UID, GID
        # if 'uid' in self.info or 'gid' in self.info:
        #     ids = []
        #     if 'uid' in self.info and self.info['uid']:
        #         before = [i for i in before if 'uid' not in i]
        #         before += ['uid=%s' % str(self.info['uid'])]
        #     if 'gid' in self.info and self.info['gid']:
        #         before = [i for i in before if 'gid' not in i]
        #         before += ['gid=%s' % str(self.info['gid'])]
        #     if self.params['options']:
        #         for opt in self.params['options']:
        #             if 'uid=' in opt or 'gid=' in opt:
        #                 ids += opt.split("o=")[1].split(",")
        #     after = [i for i in after if 'gid' not in i and 'uid' not in i]
        #     after += ids
        before, after = sorted(list(set(before))), sorted(list(set(after)))
        return self._diff_update_and_compare('options', before, after)

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
                else:
                    different = True
        # Check non idempotent parameters
        for p in self.non_idempotent:
            if self.module.params[p] is not None and self.module.params[p] not in [{}, [], '']:
                different = True
        return different


class PodmanVolume:
    """Perform volume tasks.

    Manages podman volume, inspects it and checks its current state
    """

    def __init__(self, module, name):
        """Initialize PodmanVolume class.

        Arguments:
            module {obj} -- ansible module object
            name {str} -- name of volume
        """

        super(PodmanVolume, self).__init__()
        self.module = module
        self.name = name
        self.stdout, self.stderr = '', ''
        self.info = self.get_info()
        self.version = self._get_podman_version()
        self.diff = {}
        self.actions = []

    @property
    def exists(self):
        """Check if volume exists."""
        return bool(self.info != {})

    @property
    def different(self):
        """Check if volume is different."""
        diffcheck = PodmanVolumeDiff(
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
        """Inspect volume and gather info about it."""
        # pylint: disable=unused-variable
        rc, out, err = self.module.run_command(
            [self.module.params['executable'], b'volume', b'inspect', self.name])
        if rc == 0:
            data = json.loads(out)
            if data:
                data = data[0]
                if data.get("Name") == self.name:
                    return data
        return {}

    def _get_podman_version(self):
        # pylint: disable=unused-variable
        rc, out, err = self.module.run_command(
            [self.module.params['executable'], b'--version'])
        if rc != 0 or not out or "version" not in out:
            self.module.fail_json(msg="%s run failed!" %
                                  self.module.params['executable'])
        return out.split("version")[1].strip()

    def _perform_action(self, action):
        """Perform action with volume.

        Arguments:
            action {str} -- action to perform - create, stop, delete
        """
        b_command = PodmanVolumeModuleParams(action,
                                             self.module.params,
                                             self.version,
                                             self.module,
                                             ).construct_command_from_params()
        full_cmd = " ".join([self.module.params['executable'], 'volume']
                            + [to_native(i) for i in b_command])
        self.module.log("PODMAN-VOLUME-DEBUG: %s" % full_cmd)
        self.actions.append(full_cmd)
        if not self.module.check_mode:
            rc, out, err = self.module.run_command(
                [self.module.params['executable'], b'volume'] + b_command,
                expand_user_and_vars=False)
            self.stdout = out
            self.stderr = err
            if rc != 0:
                self.module.fail_json(
                    msg="Can't %s volume %s" % (action, self.name),
                    stdout=out, stderr=err)

    def delete(self):
        """Delete the volume."""
        self._perform_action('delete')

    def create(self):
        """Create the volume."""
        self._perform_action('create')

    def recreate(self):
        """Recreate the volume."""
        self.delete()
        self.create()


class PodmanVolumeManager:
    """Module manager class.

    Defines according to parameters what actions should be applied to volume
    """

    def __init__(self, module):
        """Initialize PodmanManager class.

        Arguments:
            module {obj} -- ansible module object
        """

        super(PodmanVolumeManager, self).__init__()

        self.module = module
        self.results = {
            'changed': False,
            'actions': [],
            'volume': {},
        }
        self.name = self.module.params['name']
        self.executable = \
            self.module.get_bin_path(self.module.params['executable'],
                                     required=True)
        self.state = self.module.params['state']
        self.recreate = self.module.params['recreate']
        self.volume = PodmanVolume(self.module, self.name)

    def update_volume_result(self, changed=True):
        """Inspect the current volume, update results with last info, exit.

        Keyword Arguments:
            changed {bool} -- whether any action was performed
                              (default: {True})
        """
        facts = self.volume.get_info() if changed else self.volume.info
        out, err = self.volume.stdout, self.volume.stderr
        self.results.update({'changed': changed, 'volume': facts,
                             'podman_actions': self.volume.actions},
                            stdout=out, stderr=err)
        if self.volume.diff:
            self.results.update({'diff': self.volume.diff})
        if self.module.params['debug']:
            self.results.update({'podman_version': self.volume.version})
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
        if not self.volume.exists:
            self.volume.create()
            self.results['actions'].append('created %s' % self.volume.name)
            self.update_volume_result()
        elif self.recreate or self.volume.different:
            self.volume.recreate()
            self.results['actions'].append('recreated %s' %
                                           self.volume.name)
            self.update_volume_result()
        else:
            self.update_volume_result(changed=False)

    def make_absent(self):
        """Run actions if desired state is 'absent'."""
        if not self.volume.exists:
            self.results.update({'changed': False})
        elif self.volume.exists:
            self.volume.delete()
            self.results['actions'].append('deleted %s' % self.volume.name)
            self.results.update({'changed': True})
        self.results.update({'volume': {},
                             'podman_actions': self.volume.actions})
        self.module.exit_json(**self.results)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(type='str', default="present",
                       choices=['present', 'absent']),
            name=dict(type='str', required=True),
            label=dict(type='dict', required=False),
            driver=dict(type='str', required=False),
            options=dict(type='list', elements='str', required=False),
            recreate=dict(type='bool', default=False),
            executable=dict(type='str', required=False, default='podman'),
            debug=dict(type='bool', default=False),
        ))

    PodmanVolumeManager(module).execute()


if __name__ == '__main__':
    main()
