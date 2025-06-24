#!/usr/bin/python
# coding: utf-8 -*-

# 2022, Sébastien Gendre <seb@k-7.ch>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = """
module: podman_generate_systemd
author:
  - Sébastien Gendre (@CyberFox001)
short_description: Generate systemd unit from a pod or a container
description:
  - Generate systemd .service unit file(s) from a pod or a container
  - Support Ansible check mode
options:
  name:
    description:
      - Name of the pod or container to export
    type: str
    required: true
  dest:
    description:
      - Destination of the generated systemd unit file(s).
      - Use C(/etc/systemd/system) for the system-wide systemd instance.
      - Use C(/etc/systemd/user) or C(~/.config/systemd/user) for use with per-user instances of systemd.
    type: path
  force:
    description:
      - Replace the systemd unit file(s) even if it already exists.
      - This works with dest option.
    type: bool
    default: false
  new:
    description:
      - Generate unit files that create containers and pods, not only start them.
      - Refer to podman-generate-systemd(1) man page for more information.
    type: bool
    default: false
  restart_policy:
    description:
      - Restart policy of the service
    type: str
    choices:
      - no-restart
      - on-success
      - on-failure
      - on-abnormal
      - on-watchdog
      - on-abort
      - always
  restart_sec:
    description:
      - Configures the time to sleep before restarting a service (as configured with restart-policy).
      - Takes a value in seconds.
      - Only with Podman 4.0.0 and above
    type: int
  start_timeout:
    description:
      - Override the default start timeout for the container with the given value in seconds.
      - Only with Podman 4.0.0 and above
    type: int
  stop_timeout:
    description:
      - Override the default stop timeout for the container with the given value in seconds.
    type: int
  env:
    description:
      - Set environment variables to the systemd unit files.
      - Keys are the environment variable names, and values are the environment variable values
      - Only with Podman 4.3.0 and above
    type: dict
  use_names:
    description:
      - Use name of the containers for the start, stop, and description in the unit file.
    type: bool
    default: true
  container_prefix:
    description:
      - Set the systemd unit name prefix for containers.
      - If not set, use the default defined by podman, C(container).
      - Refer to podman-generate-systemd(1) man page for more information.
    type: str
  pod_prefix:
    description:
      - Set the systemd unit name prefix for pods.
      - If not set, use the default defined by podman, C(pod).
      - Refer to podman-generate-systemd(1) man page for more information.
    type: str
  separator:
    description:
      - Systemd unit name separator between the name/id of a container/pod and the prefix.
      - If not set, use the default defined by podman, C(-).
      - Refer to podman-generate-systemd(1) man page for more information.
    type: str
  no_header:
    description:
      - Do not generate the header including meta data such as the Podman version and the timestamp.
    type: bool
    default: false
  after:
    description:
      - Add the systemd unit after (C(After=)) option, that ordering dependencies between the list of dependencies and this service.
      - This option may be specified more than once.
      - User-defined dependencies will be appended to the generated unit file
      - But any existing options such as needed or defined by default (e.g. C(online.target)) will not be removed or overridden.
      - Only with Podman 4.0.0 and above
    type: list
    elements: str
  wants:
    description:
      - Add the systemd unit wants (C(Wants=)) option, that this service is (weak) dependent on.
      - This option may be specified more than once.
      - This option does not influence the order in which services are started or stopped.
      - User-defined dependencies will be appended to the generated unit file
      - But any existing options such as needed or defined by default (e.g. C(online.target)) will not be removed or overridden.
      - Only with Podman 4.0.0 and above
    type: list
    elements: str
  requires:
    description:
      - Set the systemd unit requires (Requires=) option.
      - Similar to wants, but declares a stronger requirement dependency.
      - Only with Podman 4.0.0 and above
    type: list
    elements: str
  executable:
    description:
      - C(Podman) executable name or full path
    type: str
    default: podman
requirements:
  - Podman installed on target host
notes:
  - If you indicate a pod, the systemd units for it and all its containers will be generated
  - Create all your pods, containers and their dependencies before generating the systemd files
  - If a container or pod is already started before you do a C(systemctl daemon-reload),
    systemd will not see the container or pod as started
  - Stop your container or pod before you do a C(systemctl daemon-reload),
    then you can start them with C(systemctl start my_container.service)
"""

EXAMPLES = """
# Example of creating a container and systemd unit file.
# When using podman_generate_systemd with new:true then
# the container needs rm:true for idempotence.
- name: Create postgres container
  containers.podman.podman_container:
    name: postgres
    image: docker.io/library/postgres:latest
    rm: true
    state: created

- name: Generate systemd unit file for postgres container
  containers.podman.podman_generate_systemd:
    name: postgres
    new: true
    no_header: true
    dest: /etc/systemd/system

- name: Ensure postgres container is started and enabled
  ansible.builtin.systemd:
    name: container-postgres
    daemon_reload: true
    state: started
    enabled: true


# Example of creating a container and integrate it into systemd
- name: A postgres container must exist, stopped
  containers.podman.podman_container:
    name: postgres_local
    image: docker.io/library/postgres:latest
    state: stopped

- name: Systemd unit files for postgres container must exist
  containers.podman.podman_generate_systemd:
    name: postgres_local
    dest: ~/.config/systemd/user/

- name: Postgres container must be started and enabled on systemd
  ansible.builtin.systemd:
    name: container-postgres_local
    scope: user
    daemon_reload: true
    state: started
    enabled: true


# Generate the unit files, but store them on an Ansible variable
# instead of writing them on target host
- name: Systemd unit files for postgres container must be generated
  containers.podman.podman_generate_systemd:
    name: postgres_local
  register: postgres_local_systemd_unit

# Generate the unit files with environment variables sets
- name: Systemd unit files for postgres container must be generated
  containers.podman.podman_generate_systemd:
    name: postgres_local
    env:
      POSTGRES_USER: my_app
      POSTGRES_PASSWORD: example
  register: postgres_local_systemd_unit
"""

RETURN = """
systemd_units:
  description: A copy of the generated systemd .service unit(s)
  returned: always
  type: dict
  sample: {
    "container-postgres_local": " #Content of the systemd .servec unit for postgres_local container",
    "pod-my_webapp": " #Content of the systemd .servec unit for my_webapp pod",
    }
podman_command:
  description: A copy of the podman command used to generate the systemd unit(s)
  returned: always
  type: str
  sample: "podman generate systemd my_webapp"
"""


import os
from ansible.module_utils.basic import AnsibleModule
import json
from ansible_collections.containers.podman.plugins.module_utils.podman.common import (
    compare_systemd_file_content,
)

RESTART_POLICY_CHOICES = [
    "no-restart",
    "on-success",
    "on-failure",
    "on-abnormal",
    "on-watchdog",
    "on-abort",
    "always",
]


def generate_systemd(module):
    """Generate systemd .service unit file from a pod or container.

    Parameter:
    - module (AnsibleModule): An AnsibleModule object

    Returns (tuple[bool, list[str], str]):
    - A boolean which indicate whether the targeted systemd state is modified
    - A copy of the generated systemd .service units content
    - A copy of the command, as a string
    """
    # Flag which indicate whether the targeted system state is modified
    changed = False

    # Build the podman command, based on the module parameters
    command_options = []

    #  New option
    if module.params["new"]:
        command_options.append("--new")

    #  Restart policy option
    restart_policy = module.params["restart_policy"]
    if restart_policy:
        # add the restart policy to options
        if restart_policy == "no-restart":
            restart_policy = "no"
        command_options.append(
            "--restart-policy={restart_policy}".format(
                restart_policy=restart_policy,
            ),
        )

    #  Restart-sec option (only for Podman 4.0.0 and above)
    restart_sec = module.params["restart_sec"]
    if restart_sec:
        command_options.append(
            "--restart-sec={restart_sec}".format(
                restart_sec=restart_sec,
            ),
        )

    #  Start-timeout option (only for Podman 4.0.0 and above)
    start_timeout = module.params["start_timeout"]
    if start_timeout:
        command_options.append(
            "--start-timeout={start_timeout}".format(
                start_timeout=start_timeout,
            ),
        )

    #  Stop-timeout option
    stop_timeout = module.params["stop_timeout"]
    if stop_timeout:
        command_options.append(
            "--stop-timeout={stop_timeout}".format(
                stop_timeout=stop_timeout,
            ),
        )

    #  Use container name(s) option
    if module.params["use_names"]:
        command_options.append("--name")

    #  Container-prefix option
    container_prefix = module.params["container_prefix"]
    if container_prefix is not None:
        command_options.append(
            "--container-prefix={container_prefix}".format(
                container_prefix=container_prefix,
            ),
        )

    #  Pod-prefix option
    pod_prefix = module.params["pod_prefix"]
    if pod_prefix is not None:
        command_options.append(
            "--pod-prefix={pod_prefix}".format(
                pod_prefix=pod_prefix,
            ),
        )

    #  Separator option
    separator = module.params["separator"]
    if separator is not None:
        command_options.append(
            "--separator={separator}".format(
                separator=separator,
            ),
        )

    #  No-header option
    if module.params["no_header"]:
        command_options.append("--no-header")

    #  After option (only for Podman 4.0.0 and above)
    after = module.params["after"]
    if after:
        for item in after:
            command_options.append(
                "--after={item}".format(
                    item=item,
                ),
            )

    #  Wants option (only for Podman 4.0.0 and above)
    wants = module.params["wants"]
    if wants:
        for item in wants:
            command_options.append(
                "--wants={item}".format(
                    item=item,
                )
            )

    #  Requires option (only for Podman 4.0.0 and above)
    requires = module.params["requires"]
    if requires:
        for item in requires:
            command_options.append(
                "--requires={item}".format(
                    item=item,
                ),
            )

    # Environment variables (only for Podman 4.3.0 and above)
    environment_variables = module.params["env"]
    if environment_variables:
        for env_var_name, env_var_value in environment_variables.items():
            command_options.append(
                "-e='{env_var_name}={env_var_value}'".format(
                    env_var_name=env_var_name,
                    env_var_value=env_var_value,
                ),
            )

    #   Set output format, of podman command, to json
    command_options.extend(["--format", "json"])

    #  Full command build, with option included
    #   Base of the command
    command = [
        module.params["executable"],
        "generate",
        "systemd",
    ]
    #   Add the options to the commande
    command.extend(command_options)
    #   Add pod or container name to the command
    command.append(module.params["name"])
    #   Build the string version of the command, only for module return
    command_str = " ".join(command)

    # Run the podman command to generated systemd .service unit(s) content
    return_code, stdout, stderr = module.run_command(command)

    # In case of error in running the command
    if return_code != 0:
        # Print information about the error and return and empty dictionary
        message = "Error generating systemd .service unit(s)."
        message += " Command executed: {command_str}"
        message += " Command returned with code: {return_code}."
        message += " Error message: {stderr}."
        module.fail_json(
            msg=message.format(
                command_str=command_str,
                return_code=return_code,
                stderr=stderr,
            ),
            changed=changed,
            systemd_units={},
            podman_command=command_str,
        )

    # In case of command execution success, its stdout is a json
    # dictionary. This dictionary is all the generated systemd units.
    # Each key value pair is one systemd unit. The key is the unit name
    # and the value is the unit content.

    # Load the returned json dictionary as a python dictionary
    systemd_units = json.loads(stdout)

    # Write the systemd .service unit(s) content to file(s), if
    # requested
    if module.params["dest"]:
        try:
            systemd_units_dest = module.params["dest"]
            # If destination don't exist
            if not os.path.exists(systemd_units_dest):
                # If  not in check mode, make it
                if not module.check_mode:
                    os.makedirs(systemd_units_dest)
                changed = True
            # If destination exist but not a directory
            if not os.path.isdir(systemd_units_dest):
                # Stop and tell user that the destination is not a directory
                message = "Destination {systemd_units_dest} is not a directory."
                message += " Can't save systemd unit files in."
                module.fail_json(
                    msg=message.format(
                        systemd_units_dest=systemd_units_dest,
                    ),
                    changed=changed,
                    systemd_units=systemd_units,
                    podman_command=command_str,
                )

            # Write each systemd unit, if needed
            for unit_name, unit_content in systemd_units.items():
                # Build full path to unit file
                unit_file_name = unit_name + ".service"
                unit_file_full_path = os.path.join(
                    systemd_units_dest,
                    unit_file_name,
                )

                if module.params["force"]:
                    # Force to replace the existing unit file
                    need_to_write_file = True
                else:
                    # See if we need to write the unit file, default yes
                    need_to_write_file = bool(compare_systemd_file_content(unit_file_full_path, unit_content))

                # Write the file, if needed
                if need_to_write_file:
                    with open(unit_file_full_path, "w") as unit_file:
                        # If not in check mode, write the file
                        if not module.check_mode:
                            unit_file.write(unit_content)
                        changed = True

        except Exception as exception:
            # When exception occurs while trying to write units file
            message = "PODMAN-GENERATE-SYSTEMD-DEBUG: "
            message += "Error writing systemd units files: "
            message += "{exception}"
            module.log(
                message.format(exception=exception),
            )
    # Return the systemd .service unit(s) content
    return changed, systemd_units, command_str


def run_module():
    """Run the module on the target"""
    # Build the list of parameters user can use
    module_parameters = {
        "name": {
            "type": "str",
            "required": True,
        },
        "dest": {
            "type": "path",
            "required": False,
        },
        "new": {
            "type": "bool",
            "required": False,
            "default": False,
        },
        "force": {
            "type": "bool",
            "required": False,
            "default": False,
        },
        "restart_policy": {
            "type": "str",
            "required": False,
            "choices": RESTART_POLICY_CHOICES,
        },
        "restart_sec": {
            "type": "int",
            "required": False,
        },
        "start_timeout": {
            "type": "int",
            "required": False,
        },
        "stop_timeout": {
            "type": "int",
            "required": False,
        },
        "env": {
            "type": "dict",
            "required": False,
        },
        "use_names": {
            "type": "bool",
            "required": False,
            "default": True,
        },
        "container_prefix": {
            "type": "str",
            "required": False,
        },
        "pod_prefix": {
            "type": "str",
            "required": False,
        },
        "separator": {
            "type": "str",
            "required": False,
        },
        "no_header": {
            "type": "bool",
            "required": False,
            "default": False,
        },
        "after": {
            "type": "list",
            "elements": "str",
            "required": False,
        },
        "wants": {
            "type": "list",
            "elements": "str",
            "required": False,
        },
        "requires": {
            "type": "list",
            "elements": "str",
            "required": False,
        },
        "executable": {
            "type": "str",
            "required": False,
            "default": "podman",
        },
    }

    # Build result dictionary
    result = {
        "changed": False,
        "systemd_units": {},
        "podman_command": "",
    }

    # Build the Ansible Module
    module = AnsibleModule(argument_spec=module_parameters, supports_check_mode=True)

    # Generate the systemd units
    state_changed, systemd_units, podman_command = generate_systemd(module)

    result["changed"] = state_changed
    result["systemd_units"] = systemd_units
    result["podman_command"] = podman_command

    # Return the result
    module.exit_json(**result)


def main():
    """Main function of this script."""
    run_module()


if __name__ == "__main__":
    main()
