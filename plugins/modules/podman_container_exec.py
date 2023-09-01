#!/usr/bin/python
# coding: utf-8 -*-

# Copyright (c) 2023, Takuya Nishimura <@nishipy>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
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
      - One of the I(command) or I(args) is required.
    type: str
  argv:
    description:
      - Passes the command as a list rather than a string.
      - One of the I(command) or I(args) is required.
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

EXAMPLES = r'''
- name: Execute a command with workdir
  containers.podman.podman_container_exec:
    name: ubi8
    command: "cat redhat-release"
    workdir: /etc

- name: Execute a command with a list of args and environment variables
  containers.podman.podman_container_exec:
    name: test_container
    argv:
      - /bin/sh
      - -c
      - echo $HELLO $BYE
    env:
      HELLO: hello world
      BYE: goodbye world

- name: Execute command in background by using detach
  containers.podman.podman_container_exec:
    name: detach_container
    command: "cat redhat-release"
    detach: true
'''

RETURN = r'''
stdout:
  type: str
  returned: success
  description:
  - The standard output of the command executed in the container.
stderr:
  type: str
  returned: success
  description:
  - The standard output of the command executed in the container.
rc:
  type: int
  returned: success
  sample: 0
  description:
  - The exit code of the command executed in the container.
exec_id:
  type: str
  returned: success and I(detach=true)
  sample: f99002e34c1087fd1aa08d5027e455bf7c2d6b74f019069acf6462a96ddf2a47
  description:
  - The ID of the exec session.
'''


import shlex
from ansible.module_utils.six import string_types
from ansible.module_utils._text import to_text
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.containers.podman.plugins.module_utils.podman.common import run_podman_command


def run_container_exec(module: AnsibleModule) -> dict:
    '''
    Execute podman-container-exec for the given options
    '''
    exec_with_args = ['container', 'exec']
    # podman_container_exec always returns changed=true
    changed = True
    exec_options = []

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
        exec_options.append('--detach')

    if env is not None:
        for key, value in env.items():
            if not isinstance(value, string_types):
                module.fail_json(
                    msg="Specify string value %s on the env field" % (value))

            to_text(value, errors='surrogate_or_strict')
            exec_options += ['--env',
                             '%s="%s"' % (key, value)]

    if privileged:
        exec_options.append('--privileged')

    if tty:
        exec_options.append('--tty')

    if user is not None:
        exec_options += ['--user',
                         to_text(user, errors='surrogate_or_strict')]

    if workdir is not None:
        exec_options += ['--workdir',
                         to_text(workdir, errors='surrogate_or_strict')]

    exec_options.append(name)
    exec_options.extend(argv)

    exec_with_args.extend(exec_options)

    rc, stdout, stderr = run_podman_command(
        module=module, executable='podman', args=exec_with_args)

    result = {
        'changed': changed,
        'podman_command': exec_options,
        'rc': rc,
        'stdout': stdout,
        'stderr': stderr,
    }

    if detach:
        result['exec_id'] = stdout.replace('\n', '')

    return result


def main():
    argument_spec = {
        'name': {
            'type': 'str',
            'required': True,
        },
        'command': {
            'type': 'str',
        },
        'argv': {
            'type': 'list',
            'elements': 'str',
        },
        'detach': {
            'type': 'bool',
            'default': False,
        },
        'env': {
            'type': 'dict',
        },
        'privileged': {
            'type': 'bool',
            'default': False,
        },
        'tty': {
            'type': 'bool',
            'default': False,
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

    result = run_container_exec(module)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
