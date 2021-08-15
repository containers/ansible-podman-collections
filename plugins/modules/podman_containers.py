#!/usr/bin/python
# Copyright (c) 2020 Red Hat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = '''
---
module: podman_containers
author:
  - "Sagi Shnaidman (@sshnaidm)"
version_added: '1.4.0'
short_description: Manage podman containers in a batch
description:
  - Manage groups of podman containers
requirements:
  - "podman"
options:
  containers:
    description:
    - List of dictionaries with data for running containers for podman_container module.
    required: True
    type: list
    elements: dict
  debug:
    description:
    - Return additional information which can be helpful for investigations.
    type: bool
    default: False
'''

EXAMPLES = '''
- name: Run three containers at once
  podman_containers:
    containers:
      - name: alpine
        image: alpine
        command: sleep 1d
      - name: web
        image: nginx
      - name: test
        image: python:3-alpine
        command: python -V
'''

from copy import deepcopy  # noqa: F402

from ansible.module_utils.basic import AnsibleModule  # noqa: F402
from ..module_utils.podman.podman_container_lib import PodmanManager  # noqa: F402
from ..module_utils.podman.podman_container_lib import set_container_opts  # noqa: F402


def combine(results):
    changed = any(i.get('changed', False) for i in results)
    failed = any(i.get('failed', False) for i in results)
    actions = []
    podman_actions = []
    containers = []
    podman_version = ''
    diffs = {}
    stderr = ''
    stdout = ''
    for i in results:
        if 'actions' in i and i['actions']:
            actions += i['actions']
        if 'podman_actions' in i and i['podman_actions']:
            podman_actions += i['podman_actions']
        if 'container' in i and i['container']:
            containers.append(i['container'])
        if 'podman_version' in i:
            podman_version = i['podman_version']
        if 'diff' in i:
            diffs[i['container']['Name']] = i['diff']
        if 'stderr' in i:
            stderr += i['stderr']
        if 'stdout' in i:
            stdout += i['stdout']

    total = {
        'changed': changed,
        'failed': failed,
        'actions': actions,
        'podman_actions': podman_actions,
        'containers': containers,
        'stdout': stdout,
        'stderr': stderr,
    }
    if podman_version:
        total['podman_version'] = podman_version
    if diffs:
        before = after = ''
        for k, v in diffs.items():
            before += "".join([str(k), ": ", str(v['before']), "\n"])
            after += "".join([str(k), ": ", str(v['after']), "\n"])
        total['diff'] = {
            'before': before,
            'after': after
        }
    return total


def check_input_strict(container):
    if container['state'] in ['started', 'present'] and not container['image']:
        return "State '%s' required image to be configured!" % container['state']


def main():
    module = AnsibleModule(
        argument_spec=dict(
            containers=dict(type='list', elements='dict', required=True),
            debug=dict(type='bool', default=False),
        ),
        supports_check_mode=True,
    )
    # work on input vars

    results = []
    for container in module.params['containers']:
        options_dict = set_container_opts(container)
        options_dict['debug'] = module.params['debug'] or options_dict['debug']
        test_input = check_input_strict(options_dict)
        if test_input:
            module.fail_json(
                msg="Failed to run container %s because: %s" % (options_dict['name'], test_input))
        res = PodmanManager(module, options_dict).execute()
        results.append(res)
    total_results = combine(results)
    module.exit_json(**total_results)


if __name__ == '__main__':
    main()
