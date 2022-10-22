#!/usr/bin/env python

# 2022, Sébastien Gendre <seb@k-7.ch>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# TODO: Write DOCUMENTATION, EXAMPLES and RETURN

DOCUMENTATION = '''
'''

EXAMPLES = '''
'''

RETURN = '''
'''

import os
from ansible.module_utils.basic import AnsibleModule
import json

RESTART_POLICY_CHOICES = [
    'no',
    'on-success',
    'on-failure',
    'on-abnormal',
    'on-watchdog',
    'on-abort',
    'always',
]

def generate_systemd(module: AnsibleModule) -> tuple[bool, list[str]]:
    '''Generate systemd .service unit file from a pod or container.

    Parameter:
    - module: An AnsibleModule object

    Returns:
    - A boolean which indicate whether the targeted systemd state is modified
    - A copy of the generated systemd .service units content
    '''
    # Flag which indicate whether the targeted system state is modified
    changed = False
    
    # Build the podman command, based on the module parameters
    command_options = []

    #  New option
    if module.params.get('new'):
        command_options.append('--new')
    
    #  Restart policy option
    restart_policy = module.params.get('restart_policy')
    if restart_policy:
        # If the restart policy requested is not supported by podman
        if restart_policy not in RESTART_POLICY_CHOICES:
            # Then stop the module execution and return an error message
            modul.fail_json(
                msg=f'Restart policy requested is "{restart_policy}"'
                f',  but must be one of: {RESTART_POLICY_CHOICES}'
            )
        # Else add the restart policy to options
        command_options.append(f'--restart-policy={restart_policy}')

    #  Restart-sec option (only for Podman 4.0.0 and above)
    restart_sec = module.params.get('restart_sec')
    if restart_sec:
        command_options.append(f'--restart-sec={restart_sec}')

    #  Start-timeout option (only for Podman 4.0.0 and above)
    start_timeout = module.params.get('start_timeout')
    if start_timeout:
        command_options.append(f'--start-timeout={start_timeout}')

    #  Stop-timeout option
    stop_timeout = module.params.get('stop_timeout')
    if stop_timeout:
        command_options.append(f'--stop-timeout={stop_timeout}')

    #  Use container name(s) option
    if module.params.get('use_names'):
        command_options.append('--name')

    #  Container-prefix option
    container_prefix = module.params.get('container_prefix')
    if container_prefix:
        command_options.append(f'--container-prefix={container_prefix}')

    #  Pod-prefix option
    pod_prefix = module.params.get('pod_prefix')
    if pod_prefix:
        command_options.append(f'--pod-prefix={pod_prefix}')

    #  Separator option
    separator = module.params.get('separator')
    if separator:
        command_options.append(f'--separator={separator}')

    #  No-header option
    if module.params.get('no_header'):
        command_options.append('--no-header')

    #  After option (only for Podman 4.0.0 and above)
    after = module.params.get('after')
    if after:
        # If after is a single string
        if isinstance(after, str):
            command_options.append(f'--after={after}')
        # If wants is a list
        if isinstance(after, list):
            for item in after:
                command_options.append(f'--after={item}')

    #  Wants option (only for Podman 4.0.0 and above)
    wants = module.params.get('wants')
    if wants:
        # If wants is a single string
        if isinstance(wants, str):
            command_options.append(f'--wants={wants}')
        # If wants is a list
        if isinstance(wants, list):
            for item in wants:
                command_options.append(f'--wants={item}')
                
    #  Requires option (only for Podman 4.0.0 and above)
    requires = module.params.get('requires')
    if requires:
        # If requires is a single string
        if isinstance(requires, str):
            command_options.append(f'--requires={requires}')
        # If requires is a list
        if isinstance(requires, list):
            for item in requires:
                command_options.append(f'--requires={item}')
    
    #  Full command, with option include
    command_options.extend(['--format', 'json'])
    command = [
        module.params.get('executable'), 'generate', 'systemd',
        *command_options,
        module.params['name'],
    ]

    # If debug enabled
    if module.params.get('debug'):
        module.log('PODMAN-GENERATE-SYSTEMD-DEBUG:'
                   f' Command for generate systemd .service unit: {command}')
    
    # Run the podman command to generated systemd .service unit(s) content
    return_code, stdout, stderr = module.run_command(command)

    # In case of error in running the command
    if return_code != 0:
        # Print informations about the error and return and empty dictionary
        module.fail_json(
            'Error generating systemd .service unit(s).'
            f' Command executed: {command}'
            f' Command returned with code: {return_code}.'
            f' Error message: {stderr}.'
        )
        return changed, {}

def main():
    pass

if __name__ == '__main__':
    main()
