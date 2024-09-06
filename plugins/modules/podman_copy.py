#!/usr/bin/python
# coding: utf-8 -*-

# Copyright (c) 2021, Sagi Shnaidman <sshnaidm@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
module: podman_copy
short_description: Copy from/to containers
author: Thomas Dilasser (@DilasserT)
description:
  - podman copies files from/to the container from/to the local machine.
options:
  path:
    description:
    - Filesystem path.
    type: str
    required: true
  container_path:
    description:
    - Path inside the container
    type: str
    required: true
  into_container:
    description:
    - Copy in the container.
    type: bool
  from_container:
    description:
    - Copy from the container.
    type: bool
  container:
    description:
    - container name.
    type: str
    required: true
  archive:
    description:
    - Chown copied file to the primary uid/gid of the destined container.
    type: bool
    default: true
  overwrite:
    description:
    - Allow to overwrite directories with non-directories and vice versa
    type: bool
    default: False
  force:
    description:
    - Overwrite file if it exists.
    type: bool
    default: false
  executable:
    description:
      - Path to C(podman) executable if it is not in the C($PATH) on the
        machine running C(podman)
    default: 'podman'
    type: str
requirements:
  - "Podman installed on host"
'''

RETURN = '''
'''

EXAMPLES = '''
# What modules does for example
- containers.podman.podman_copy:
    path: /path/to/file
    container_path: /path/to/file/in/container
    container: container-name
    from_container: true
- containers.podman.podman_copy:
    path: /path/to/file
    container_path: /path/to/file/in/container
    container: container-name
    into_container: true
'''

import os  # noqa: E402
import json
from ansible.module_utils.basic import AnsibleModule  # noqa: E402


def copy(module, executable):
    changed = True
    command = [executable, 'cp']
    if not module.params['archive']:
        command += ["--archive=false"]
    if module.params['overwrite']:
        command += ["--overwrite=true"]
    container_name = module.params['container']
    if module.params['into_container']:
        command += [module.params['path']]
        command += [module.params['container'] + ":" + module.params['container_path']]
        command_inspect = [executable, 'container', 'inspect']
        command_inspect.extend([container_name])
        rc, out, err = module.run_command(command_inspect)
        if rc != 0:
            module.fail_json(msg="Unable to gather info for %s: %s" % (",".join(module.params['container']), err))
        else:
            json_out = json.loads(out) if out else None
            if json_out is None:
                module.fail_json(msg="Unable to gather info for %s: %s" % (",".join(module.params['container']), err))

        full_path = json_out[0]['GraphDriver']['Data']['MergedDir']
        if module.params['path'][0] == "/":
            full_path += module.params['container_path']
        else:
            full_path += "/"
            full_path += module.params['container_path']

        if os.path.exists(full_path) and not module.params['force']:
            changed = False
            return changed, '', ''

    else:
        command += [module.params['container'] + ":" + module.params['container_path']]
        command += [module.params['path']]
        if os.path.exists(module.params['path']) and not module.params['force']:
            changed = False
            return changed, '', ''

    rc, out, err = module.run_command(command)
    if rc != 0:
        module.fail_json(msg="Error during copy %s: %s" % (
                         module.params['container'], err))
    return changed, out, err


def main():
    module = AnsibleModule(
        argument_spec=dict(
            path=dict(type='str', required=True),
            container_path=dict(type='str', required=True),
            container=dict(type='str', required=True),
            into_container=dict(type='bool'),
            from_container=dict(type='bool'),
            force=dict(type='bool', default=False),
            archive=dict(type='bool', default=True),
            overwrite=dict(type='bool', default=False),
            executable=dict(type='str', default='podman')
        ),
        supports_check_mode=True,
        mutually_exclusive=[
            ('from_container', 'into_container'),
        ],
        required_one_of=[
            ('from_container', 'into_container'),
        ],
    )

    executable = module.get_bin_path(module.params['executable'], required=True)
    changed, out, err = copy(module, executable)

    results = {
        "changed": changed,
        "stdout": out,
        "stderr": err,
    }
    module.exit_json(**results)


if __name__ == '__main__':
    main()
