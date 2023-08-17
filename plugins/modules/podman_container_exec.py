#!/usr/bin/python
# coding: utf-8 -*-

# Copyright (c) 2023, Takuya Nishimura <@nishipy>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
from ansible_collections.containers.podman.plugins.module_utils.podman.common import compare_systemd_file_content
import json
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.module_utils.six import string_types
import shlex
import os
__metaclass__ = type


DOCUMENTATION = '''
module: podman_container_exec
author:
  - Takuya Nishimura (@nishipy)
short_description: Executes a command in a running container.
description:
  - Executes a command in a running container.
options:
  name:
    description:
      - Name of the container where the command is executed.
    type: str
    required: true
  command:
    description:
      - The command to run in the container.
      - One of the O(command) or O(args) is required.
    type: str
  argv:
    description:
      - Passes the command as a list rather than a string.
      - One of the O(command) or O(args) is required.
    type: list
    elements: str
  detach:
    description:
      - If true, the command runs in the background.
      - The exec session is automatically removed when it completes.
    type: bool
    default: false
  env:
    description:
      - Set environment variables.
    type: dict
  privileged:
    description:
      - Give extended privileges to the container.
    type: bool
    default: false
  tty:
    description:
      - Allocate a pseudo-TTY.
    type: bool
    default: false
  user:
    description:
      - The username or UID used and, optionally, the groupname or GID for the specified command.
      - Both user and group may be symbolic or numeric.
    type: str
  workdir:
    description:
      - Working directory inside the container.
    type: str
requirements:
  - podman
notes:
  - See L(the Podman documentation,https://docs.podman.io/en/latest/markdown/podman-exec.1.html) for details of podman-exec(1).
'''

EXAMPLES = '''
To Be Added.
'''

RETURN = '''
stdout:
  type: str
  returned: success and O(detach=false)
  description:
	- The standard output of the command executed in the container.
stderr:
  type: str
  returned: success and O(detach=false)
  description:
	- The standard output of the command executed in the container.
rc:
  type: int
  returned: success and O(detach=false)
  description:
	- The exit code of the command executed in the container.
exec_id:
  type: str
  returned: success and O(detach=true)
  sample: f99002e34c1087fd1aa08d5027e455bf7c2d6b74f019069acf6462a96ddf2a47
  description:
	- The ID of the exec session.
'''


def container_exec(module: AnsibleModule):
    exec_command = ['podman', 'container', 'exec']
    # always returns as changed
    changed = True
    command_options = []

    name = module.params['name']
    argv = module.params['argv']
    command = module.params['command']
    detach = module.params['detach']
    env = module.params['env']
    privileged = module.params['privileged']
    tty = module.params['tty']
    user = module.params['user']
    workdir = module.params['workdir']

    if command is not None:
        argv = shlex.split(command)

    if detach:
        command_options.append('--detach')

    if env is not None:
        for key, value in env.items():
            if not isinstance(value, string_types):
                module.fail_json(
                    msg="Specify string value %s on the env field" % (value))

            to_text(value, errors='surrogate_or_strict')
            command_options += ['--env',
                                '%s="%s"' % (key, value)]

    if privileged:
        command_options.append('--privileged')

    if tty:
        command_options.append('--tty')

    if user is not None:
        command_options += ['--user',
                            to_text(user, errors='surrogate_or_strict')]

    if workdir is not None:
        command_options += ['--workdir',
                            to_text(workdir, errors='surrogate_or_strict')]

    command_options.append(name)
    command_options.extend(argv)

    exec_command.extend(command_options)
    exec_command_str = ' '.join(exec_command)
    rc, stdout, stderr = module.run_command(exec_command_str)

    result = {
        'changed': changed,
        'podman_command': command_options,
        'rc': rc,
        'stdout': stdout,
        'stderr': stderr,
    }

    module.exit_json(**result)


def main():
    argument_spec = {
        'name': {
            'type': 'str',
            'required': True
        },
        'command': {
            'type': 'str',
        },
        'argv': {
            'type': 'list',
        },
        'detach': {
            'type': 'bool',
            'default': False
        },
        'env': {
            'type': 'dict',
        },
        'privileged': {
            'type': 'bool',
            'default': False
        },
        'privileged': {
            'type': 'bool',
            'default': False
        },
        'tty': {
            'type': 'bool',
            'default': False
        },
        'user': {
            'type': 'str',
        },
        'workdir': {
            'type': 'str',
        },
    }

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_one_of=[('argv', 'command')],
    )

    container_exec(module)


if __name__ == '__main__':
    main()
