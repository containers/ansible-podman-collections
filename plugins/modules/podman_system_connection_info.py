#!/usr/bin/python
# Copyright (c) 2025 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
module: podman_system_connection_info
author:
  - "Sagi Shnaidman (@sshnaidm)"
version_added: '1.18.0'
short_description: Gather info about podman system connections
notes: []
description:
  - Gather info about podman system connections with podman system connection list command.
requirements:
  - "Podman installed on host"
options:
  name:
    description:
      - Name of the connection to gather info about
      - If not provided, info about all connections will be returned
    type: str
  executable:
    description:
      - Path to C(podman) executable if it is not in the C($PATH) on the
        machine running C(podman)
    default: 'podman'
    type: str
"""

EXAMPLES = r"""
- name: Gather info about all connections
  containers.podman.podman_system_connection_info:

- name: Gather info about specific connection
  containers.podman.podman_system_connection_info:
    name: production

- name: Get connection info and register result
  containers.podman.podman_system_connection_info:
    name: staging
  register: staging_connection

- name: Display connection URI
  debug:
    msg: "Staging connection URI: {{ staging_connection.connections[0].URI }}"
  when: staging_connection.connections | length > 0
"""

RETURN = r"""
connections:
    description: Facts from all or specified connections
    returned: always
    type: list
    sample: [
        {
            "Name": "production",
            "URI": "ssh://root@server.example.com:22/run/user/0/podman/podman.sock",
            "Identity": "/home/user/.ssh/id_rsa",
            "Default": true,
            "ReadWrite": true
        },
        {
            "Name": "local",
            "URI": "unix:///run/user/1000/podman/podman.sock",
            "Identity": "",
            "Default": false,
            "ReadWrite": false
        },
        {
            "Name": "development",
            "URI": "ssh://dev@dev.example.com:22/run/user/1000/podman/podman.sock",
            "Identity": "/home/user/.ssh/dev_rsa",
            "Default": false,
            "ReadWrite": true
        }
    ]
"""

import json
from ansible.module_utils.basic import AnsibleModule


def get_connection_info(module, executable, name):
    """Get connection information from podman system connection list.

    Retrieves connection information by executing 'podman system connection list --format json'
    and optionally filters the results for a specific connection by name.

    Args:
        module (AnsibleModule): The Ansible module instance for running commands and error handling
        executable (str): Path to the podman executable
        name (str or None): Name of specific connection to filter for, or None to get all connections

    Returns:
        tuple: A tuple containing:
            - connections (list): List of connection dictionaries matching the filter criteria
            - out (str): Raw stdout from the podman command
            - err (str): Raw stderr from the podman command

    Raises:
        AnsibleFailJson: If the podman command fails or JSON parsing fails

    Note:
        When a specific connection name is provided but not found, an empty list is returned
        rather than failing. This allows for idempotent behavior when checking if connections exist.
    """
    command = [executable, "system", "connection", "list", "--format", "json"]
    rc, out, err = module.run_command(command)

    if rc != 0:
        module.fail_json(msg="Unable to get list of connections: %s" % err)

    try:
        connections = json.loads(out) if out.strip() else []
    except json.JSONDecodeError as e:
        module.fail_json(msg="Failed to parse connection list JSON: %s" % str(e))

    if name:
        # Filter for specific connection
        filtered_connections = [conn for conn in connections if conn.get("Name") == name]
        # if not filtered_connections:
        #     module.fail_json(msg="Connection '%s' not found" % name)
        return filtered_connections, out, err

    return connections, out, err


def main():
    """Main entry point for the podman_system_connection_info Ansible module.

    This function sets up the Ansible module, validates parameters, retrieves connection
    information from podman, and returns the results in the expected format.

    The module supports check mode and never reports changes since it's an info-gathering
    module that doesn't modify system state.

    Module Parameters:
        executable (str): Path to podman executable (default: "podman")
        name (str, optional): Name of specific connection to get info about.
                              If not provided, returns info about all connections.

    Each connection dictionary may contain the following fields:
        - Name (str): Connection name
        - URI (str): Connection URI (ssh://, unix://, tcp://)
        - Default (bool): Whether this is the default connection
        - ReadWrite (bool, optional): Read/write access (Podman version dependent)
        - Identity (str, optional): SSH identity file path (Podman version dependent)
        - IsMachine (bool, optional): Whether this is a machine connection (Podman version dependent)

    Note:
        Some fields like ReadWrite, Identity, and IsMachine are optional and may not be present
        in all Podman versions. The module handles this gracefully.
    """
    module = AnsibleModule(
        argument_spec=dict(executable=dict(type="str", default="podman"), name=dict(type="str")),
        supports_check_mode=True,
    )

    name = module.params["name"]
    executable = module.get_bin_path(module.params["executable"], required=True)

    inspect_results, out, err = get_connection_info(module, executable, name)

    results = {"changed": False, "connections": inspect_results, "stderr": err}

    module.exit_json(**results)


if __name__ == "__main__":
    main()
