#!/usr/bin/python
# Copyright (c) 2025 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
module: podman_system_info
author:
  - Johnson Lien (@johnsonlien)
short_description: Get podman system information from host machine
description: Runs "podman system info" on host machine
'''

EXAMPLES = r'''
- name: Get Podman system information
  containers.podman.podman_system_info:
'''

RETURN = r'''
'''

import json

from ansible.module_utils.basic import AnsibleModule

def get_podman_system_info(module, executable):
    command = [executable, 'system', 'info']
    rc, out, err = module.run_command(command)
    out = out.strip()
    if out:
        return out

    return json.dumps([])

def main():
    module = AnsibleModule(
        argument_spec=dict(
            executable=dict(type='str', default='podman'),
            name=dict(type='list', elements='str')
        ),
        supports_check_mode=True,
    )

    executable = module.params['executable']
    name = module.params.get('name')
    executable = module.get_bin_path(executable, required=True)

    results = get_podman_system_info(module, executable)

    results = dict(
        changed=False,
        podman_system_info=results,
    )

    module.exit_json(**results)

if __name__ == '__main__':
    main()
