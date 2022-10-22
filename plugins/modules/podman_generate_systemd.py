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

    # In case of command execution success, its stdout is a json
    # dictionary. This dictionary is all the generated systemd units.
    # Each key value pair is one systemd unit. The key is the unit name
    # and the value is the unit content.

    # Load the returned json dictionary as a python dictionary
    systemd_units = json.loads(stdout)
    
    # Write the systemd .service unit(s) content to file(s), if
    # requested and not in check mode
    if module.params.get('dest') and not module.check_mode:
        try:
            systemd_units_dest = os.path.expanduser(module.params.get('dest'))
            # If destination don't exist and not in check mode
            if not os.path.exists(systemd_units_dest):
                # Make it
                os.makedirs(systemd_units_dest)
                changed = True
            # If destination exist but not a directory
            if not os.path.isdir(systemd_units_dest):
                # Stop and tell user that the destination is not a directry
                module.fail_json(
                    f'Destination {systemd_units_dest} is not a directory.'
                    "Can't save systemd unit files in."
                )

            # Write each systemd unit, if needed
            for unit_name, unit_content in systemd_units.items():
                # Build full path to unit file
                unit_file_name = unit_name + '.service'
                unit_file_full_path = os.path.join(
                    systemd_units_dest,
                    unit_file_name,
                )
                
                # See if we need to write the unit file, default yes
                need_to_write_file = True
                # If the unit file already exist, compare it with the
                # generated content
                if os.path.exists(unit_file_full_path):
                    # Read the file
                    with open(unit_file_full_path, 'r') as unit_file:
                        current_unit_file_content = unit_file.read()                    
                    # If current unit file content is the same as the
                    # generated content
                    if current_unit_file_content == unit_content:
                        # We don't need to write it
                        need_to_write_file = False

                # Write the file, if needed
                if need_to_write_file:
                    with open(unit_file_full_path, 'w') as unit_file:
                        unit_file.write(unit_content)
                        changed = True

        except Exception as exception:
            # When exception occurs while trying to write units file
            module.log(
                'PODMAN-GENERATE-SYSTEMD-DEBUG: '
                'Error writing systemd units files: '
                f'{exception}'
            )
    # Return the systemd .service unit(s) content
    return changed, systemd_units

def run_module():
    '''Run the module on the target'''
    # Build the list of parameters user can use
    module_parameters = {
        'name': {
            'type': 'str',
            'required': True,
        },
        'dest': {
            'type': 'str',
            'required': False,
        },
        'new': {
            'type': 'bool',
            'required': False,
            'default': False,
        },
        'restart_policy': {
            'type': 'str',
            'required': False,
            'default': 'on-failure',
            'choices': RESTART_POLICY_CHOICES,
        },
        'restart_sec': {
            'type': 'int',
            'required': False,
        },
        'start_timeout': {
            'type': 'int',
            'required': False,
        },
        'stop_timeout': {
            'type': 'int',
            'required': False,
        },
        'use_names': {
            'type': 'bool',
            'required': False,
            'default': True,
        },
        'container_prefix': {
            'type': 'str',
            'required': False,
        },
        'pod_prefix': {
            'type': 'str',
            'required': False,
        },
        'separator': {
            'type': 'str',
            'required': False,
        },
        'no_header': {
            'type': 'bool',
            'required': False,
            'default': False,
        },
        'after': {
            'type': 'list',
            'elements': 'str',
            'required': False,
        },
        'wants': {
            'type': 'list',
            'elements': 'str',
            'required': False,
        },
        'requires': {
            'type': 'list',
            'elements': 'str',
            'required': False,
        },
        'debug': {
            'type': 'bool',
            'required': False,
            'default': False,
        },
        'executable': {
            'type': 'str',
            'required': False,
            'default': 'podman',
        },
    }
    
    # Build result dictionary
    result = {
        'changed': False,
        'systemd_units': {},
    }

    # Build the Ansible Module
    module = AnsibleModule(
        argument_spec=module_parameters,
        supports_check_mode=True
    )

    # Generate the systemd units
    state_changed, systemd_units = generate_systemd(module)

    result['changed'] = state_changed
    result['systemd_units'] = systemd_units

    # Return the result
    module.exit_json(**result)

def main():
    pass

if __name__ == '__main__':
    main()
