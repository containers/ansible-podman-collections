#!/usr/bin/python
# Copyright (c) 2025 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
module: podman_system_connection
author:
  - "Sagi Shnaidman (@sshnaidm)"
version_added: '1.18.0'
short_description: Manage podman system connections
notes: []
description:
  - Manage podman system connections with podman system connection command.
  - Add, remove, rename and set default connections to Podman services.
requirements:
  - podman
options:
  name:
    description:
      - Name of the connection
    type: str
    required: True
  state:
    description:
      - State of the connection
    type: str
    choices:
      - present
      - absent
    default: present
  executable:
    description:
      - Path to C(podman) executable if it is not in the C($PATH) on the
        machine running C(podman)
    default: 'podman'
    type: str
  destination:
    description:
      - Destination for the connection. Required when I(state=present).
      - Can be in the format C([user@]hostname[:port]), C(ssh://[user@]hostname[:port]),
        C(unix://path), C(tcp://hostname:port)
    type: str
  default:
    description:
      - Make this connection the default for this user
    type: bool
  identity:
    description:
      - Path to SSH identity file
    type: str
  port:
    description:
      - SSH port (default is 22)
    type: int
  socket_path:
    description:
      - Path to the Podman service unix domain socket on the ssh destination host
    type: str
  new_name:
    description:
      - New name for the connection when renaming (used with I(state=present))
    type: str
"""

EXAMPLES = r"""
- name: Add a basic SSH connection
  containers.podman.podman_system_connection:
    name: production
    destination: root@server.example.com
    state: present

- name: Add SSH connection with custom port and identity
  containers.podman.podman_system_connection:
    name: staging
    destination: user@staging.example.com
    port: 2222
    identity: ~/.ssh/staging_rsa
    state: present

- name: Add connection and set as default
  containers.podman.podman_system_connection:
    name: development
    destination: dev@dev.example.com
    default: true
    state: present

- name: Add unix socket connection
  containers.podman.podman_system_connection:
    name: local
    destination: unix:///run/podman/podman.sock
    state: present

- name: Add TCP connection
  containers.podman.podman_system_connection:
    name: remote_tcp
    destination: tcp://remote.example.com:8080
    state: present

- name: Rename a connection
  containers.podman.podman_system_connection:
    name: old_name
    new_name: new_name
    state: present

- name: Remove a connection
  containers.podman.podman_system_connection:
    name: old_connection
    state: absent
"""

RETURN = r"""
connection:
    description: Connection information in podman JSON format
    returned: always
    type: dict
    sample: {
        "Name": "production",
        "URI": "ssh://root@server.example.com:22/run/user/0/podman/podman.sock",
        "Default": true,
        "ReadWrite": true
    }
actions:
    description: Actions performed on the connection
    returned: always
    type: list
    sample:
      - "Connection 'production' added"
      - "Connection 'production' set as default"
"""

import json
from ansible.module_utils.basic import AnsibleModule


def get_connection_info(module, executable, name):
    """Get specific connection information from podman system connection list.

    Retrieves connection information by executing 'podman system connection list --format json'
    and searches for a connection with the specified name.

    Args:
        module (AnsibleModule): The Ansible module instance for running commands and error handling
        executable (str): Path to the podman executable
        name (str): Name of the specific connection to search for

    Returns:
        dict or None: Connection dictionary if found, None if not found

    Connection dictionary may contain:
        - Name (str): Connection name
        - URI (str): Connection URI (ssh://, unix://, tcp://)
        - Default (bool): Whether this is the default connection
        - ReadWrite (bool, optional): Read/write access (Podman version dependent)
        - Identity (str, optional): SSH identity file path (Podman version dependent)
        - IsMachine (bool, optional): Whether this is a machine connection (Podman version dependent)

    Raises:
        AnsibleFailJson: If the podman command fails or JSON parsing fails

    Note:
        This function differs from the _info module's get_connection_info by returning
        a single connection dict or None, rather than a list of connections.
    """
    command = [executable, "system", "connection", "list", "--format", "json"]
    rc, out, err = module.run_command(command)
    if rc != 0:
        module.fail_json(msg="Failed to list connections: %s" % err)

    try:
        connections = json.loads(out) if out.strip() else []
        for conn in connections:
            if conn.get("Name") == name:
                return conn
        return None
    except json.JSONDecodeError as e:
        module.fail_json(msg="Failed to parse connection list JSON: %s" % str(e))


def connections_are_identical(conn1, conn2):
    """Check if two connections are identical by comparing their attributes (excluding Name).

    Compares all relevant connection attributes to determine if two connections
    represent the same configuration. The Name field is excluded from comparison
    to allow for rename operations.

    Args:
        conn1 (dict or None): First connection dictionary to compare
        conn2 (dict or None): Second connection dictionary to compare

    Returns:
        bool: True if connections have identical attributes, False otherwise

    Compared attributes:
        - URI (str): Connection URI (must match exactly)
        - Default (bool): Default status (must match)
        - ReadWrite (bool, optional): Read/write access (Podman version dependent)
        - Identity (str, optional): SSH identity file path (Podman version dependent)
        - IsMachine (bool, optional): Machine connection flag (Podman version dependent)

    Note:
        Returns False if either connection is None or empty. Optional fields
        (ReadWrite, Identity, IsMachine) are handled gracefully - missing fields
        are treated as None for comparison purposes.
    """
    if not conn1 or not conn2:
        return False
    # Compare all relevant attributes except Name
    return {**conn1, "Name": None} == {**conn2, "Name": None}


def destination_matches_uri(destination, current_uri):
    """Check if a destination specification matches an existing connection URI.

    Compares a user-provided destination with the current connection URI,
    handling both full protocol URIs and simplified hostname formats.

    Args:
        destination (str): User-provided destination specification
        current_uri (str): Existing connection URI from podman

    Returns:
        bool: True if destination matches the current URI, False otherwise

    Matching logic:
        - Full URIs (ssh://, unix://, tcp://): Requires exact match
        - Simple format (user@host): Checks if contained in expanded URI

    Examples:
        destination_matches_uri("ssh://user@host:22", "ssh://user@host:22/path") -> True
        destination_matches_uri("user@host", "ssh://user@host:22/path") -> True
        destination_matches_uri("unix:///tmp/sock", "unix:///tmp/sock") -> True
        destination_matches_uri("user@host", "ssh://other@host:22/path") -> False

    Note:
        Podman typically expands simple formats like "user@host" into full URIs
        like "ssh://user@host:22/run/user/uid/podman/podman.sock", so this
        function allows matching against the simplified form.
    """
    if destination.startswith(("ssh://", "unix://", "tcp://")):
        # Exact protocol match required for full URIs
        return current_uri == destination
    # Simple hostname format - check if it's contained in the expanded URI
    # podman expands "user@host" to "ssh://user@host:22/run/user/uid/podman/podman.sock"
    return destination in current_uri


def connection_needs_update(current_conn, params):
    """Check if a connection needs to be updated based on current vs desired state.

    Compares the current connection configuration with the desired module parameters
    to determine if changes are needed. Generates diff information for changed fields.

    Args:
        current_conn (dict or None): Current connection dictionary from podman, or None if not exists
        params (dict): Module parameters containing desired connection configuration

    Returns:
        tuple: A tuple containing:
            - needs_update (bool): True if connection needs changes, False if current state matches desired
            - diffs (dict): Dictionary with 'before' and 'after' keys containing changed fields

    Checked parameters:
        - destination: Compared against current URI using destination_matches_uri()
        - default: Compared against current Default field
        - identity: Compared against current Identity field (if provided)

    Examples:
        # Connection doesn't exist
        connection_needs_update(None, {...}) -> (True, {"before": {}, "after": {}})

        # URI change needed
        connection_needs_update({"URI": "old"}, {"destination": "new"}) ->
            (True, {"before": {"URI": "old"}, "after": {"URI": "new"}})

        # No changes needed
        connection_needs_update({"URI": "same", "Default": False}, {"destination": "same", "default": False}) ->
            (False, {"before": {}, "after": {}})

    Note:
        The identity parameter is only checked if explicitly provided (not None).
        Missing identity in params is not treated as a change requirement.
    """
    if not current_conn:
        return True, {"before": {}, "after": {}}

    destination = params["destination"]
    default = params["default"]
    diffs = {"before": {}, "after": {}}

    # Check if URI matches the expected destination format
    current_uri = current_conn.get("URI", "")
    if not destination_matches_uri(destination, current_uri):
        diffs["before"]["URI"] = current_uri
        diffs["after"]["URI"] = destination

    # Check if default status needs to change
    # Compare "Default" only when it's set explicitly in parameters,
    # first system connection is always default
    if default is not None and default != current_conn.get("Default"):
        diffs["before"]["Default"] = current_conn.get("Default")
        diffs["after"]["Default"] = default

    # Check Identity if provided
    identity = params.get("identity")
    if identity is not None and identity != current_conn.get("Identity", ""):
        diffs["before"]["Identity"] = current_conn.get("Identity", "")
        diffs["after"]["Identity"] = identity

    if diffs["before"] or diffs["after"]:
        return True, diffs

    return False, diffs


def add_connection(module, executable, name, destination, default, identity, port, socket_path):
    """Add a new podman system connection with specified parameters.

    Executes 'podman system connection add' with the provided configuration parameters.
    Supports all connection options including SSH settings and default flag.

    Args:
        module (AnsibleModule): The Ansible module instance for running commands and error handling
        executable (str): Path to the podman executable
        name (str): Name for the new connection
        destination (str): Connection destination (URI or simple hostname format)
        default (bool): Whether to set this connection as the default
        identity (str or None): Path to SSH identity file (optional)
        port (int or None): SSH port number (optional, defaults to 22 for SSH)
        socket_path (str or None): Path to podman socket on remote host (optional)

    Returns:
        tuple: A tuple containing:
            - changed (bool): Always True since a connection is being added
            - actions (list): List of action messages describing what was done

    Command construction:
        Base: 'podman system connection add'
        Options added conditionally:
            --default (if default=True)
            --identity <path> (if identity provided)
            --port <port> (if port provided)
            --socket-path <path> (if socket_path provided)
        Arguments: <name> <destination>

    Actions generated:
        - "Connection '<name>' added" (always)
        - "Connection '<name>' set as default" (if default=True)

    Raises:
        AnsibleFailJson: If the podman command fails

    Note:
        In check mode, the command is not executed but actions are still generated
        to show what would happen. This allows for proper diff and change reporting.
    """
    actions = []
    command = [executable, "system", "connection", "add"]

    if default:
        command.extend(["--default"])

    if identity:
        command.extend(["--identity", identity])

    if port:
        command.extend(["--port", str(port)])

    if socket_path:
        command.extend(["--socket-path", socket_path])

    command.extend([name, destination])

    if not module.check_mode:
        rc, out, err = module.run_command(command)
        if rc != 0:
            module.fail_json(msg="Failed to add connection '%s': %s" % (name, err))

    actions.append("Connection '%s' added" % name)

    if default:
        actions.append("Connection '%s' set as default" % name)

    return True, actions


def remove_connection(module, executable, name):
    """Remove an existing podman system connection.

    Executes 'podman system connection remove' to delete the specified connection.

    Args:
        module (AnsibleModule): The Ansible module instance for running commands and error handling
        executable (str): Path to the podman executable
        name (str): Name of the connection to remove

    Returns:
        tuple: A tuple containing:
            - changed (bool): Always True since a connection is being removed
            - actions (list): List containing single action message about the removal

    Command executed:
        'podman system connection remove <name>'

    Actions generated:
        - "Connection '<name>' removed"

    Raises:
        AnsibleFailJson: If the podman command fails (e.g., connection doesn't exist)

    Note:
        In check mode, the command is not executed but the action message is still
        generated to show what would happen. The caller should verify the connection
        exists before calling this function if idempotent behavior is required.
    """
    command = [executable, "system", "connection", "remove", name]

    if not module.check_mode:
        rc, out, err = module.run_command(command)
        if rc != 0:
            module.fail_json(msg="Failed to remove connection '%s': %s" % (name, err))

    return True, ["Connection '%s' removed" % name]


def rename_connection(module, executable, old_name, new_name):
    """Rename an existing podman system connection.

    Executes 'podman system connection rename' to change the name of an existing connection.
    All connection attributes (URI, default status, etc.) remain unchanged.

    Args:
        module (AnsibleModule): The Ansible module instance for running commands and error handling
        executable (str): Path to the podman executable
        old_name (str): Current name of the connection to rename
        new_name (str): New name for the connection

    Returns:
        tuple: A tuple containing:
            - changed (bool): Always True since a connection is being renamed
            - actions (list): List containing single action message about the rename

    Command executed:
        'podman system connection rename <old_name> <new_name>'

    Actions generated:
        - "Connection '<old_name>' renamed to '<new_name>'"

    Raises:
        AnsibleFailJson: If the podman command fails (e.g., old connection doesn't exist,
                        new name already exists, etc.)

    Note:
        In check mode, the command is not executed but the action message is still
        generated to show what would happen. The caller should verify the old connection
        exists and the new name is available before calling this function.
    """
    command = [executable, "system", "connection", "rename", old_name, new_name]

    if not module.check_mode:
        rc, out, err = module.run_command(command)
        if rc != 0:
            module.fail_json(msg="Failed to rename connection '%s' to '%s': %s" % (old_name, new_name, err))

    return True, ["Connection '%s' renamed to '%s'" % (old_name, new_name)]


def set_default_connection(module, executable, name):
    """Set an existing connection as the default connection.

    Executes 'podman system connection default' to mark the specified connection
    as the default for the current user. Any previously default connection will
    no longer be the default.

    Args:
        module (AnsibleModule): The Ansible module instance for running commands and error handling
        executable (str): Path to the podman executable
        name (str): Name of the connection to set as default

    Returns:
        tuple: A tuple containing:
            - changed (bool): Always True since default status is being changed
            - actions (list): List containing single action message about setting default

    Command executed:
        'podman system connection default <name>'

    Actions generated:
        - "Connection '<name>' set as default"

    Raises:
        AnsibleFailJson: If the podman command fails (e.g., connection doesn't exist)

    Note:
        In check mode, the command is not executed but the action message is still
        generated to show what would happen. This function does not verify that
        the connection exists - the caller should handle that validation.

        Setting a connection as default automatically unsets any previous default
        connection, but this function only reports the action for the specified connection.
    """
    command = [executable, "system", "connection", "default", name]

    if not module.check_mode:
        rc, out, err = module.run_command(command)
        if rc != 0:
            module.fail_json(msg="Failed to set connection '%s' as default: %s" % (name, err))

    return True, ["Connection '%s' set as default" % name]


def main():
    """Main entry point for the podman_system_connection Ansible module.

    This function sets up the Ansible module, validates parameters, and orchestrates
    the management of podman system connections based on the desired state.

    The module supports the following operations:
    - Creating new connections (state=present with destination)
    - Updating existing connections (state=present with different parameters)
    - Renaming connections (state=present with new_name)
    - Removing connections (state=absent)
    - Setting connections as default (default=true)

    Module Parameters:
        name (str, required): Name of the connection
        state (str): 'present' or 'absent' (default: 'present')
        executable (str): Path to podman executable (default: 'podman')
        destination (str): Connection destination (required for state=present, except rename)
        default (bool): Set as default connection (default: False)
        identity (str): SSH identity file path (optional)
        port (int): SSH port number (optional)
        socket_path (str): Remote podman socket path (optional)
        new_name (str): New name for rename operation (optional)

    Parameter constraints:
        - destination and new_name are mutually exclusive
        - destination is required when state=present (except for rename operations)

    Operation logic:
        state=present with new_name: Rename operation
            - Fails if source connection doesn't exist
            - Idempotent if target name exists with identical configuration
            - Performs rename if target name doesn't exist

        state=present with destination: Add/update operation
            - Checks if connection needs update using connection_needs_update()
            - Removes existing connection if changes needed
            - Adds new connection with desired parameters
            - Idempotent if existing connection matches desired state

        state=absent: Remove operation
            - Removes connection if it exists
            - Idempotent if connection doesn't exist

    Cross-version compatibility:
        Handles optional fields (ReadWrite, Identity, IsMachine) that may not be
        present in all Podman versions. Missing fields are treated gracefully.

    Note:
        The module follows the 'always require full description of desired state'
        design pattern, requiring destination for all present operations except rename.
    """
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type="str", required=True),
            state=dict(type="str", choices=["present", "absent"], default="present"),
            executable=dict(type="str", default="podman"),
            destination=dict(type="str"),
            default=dict(type="bool"),
            identity=dict(type="str"),
            port=dict(type="int"),
            socket_path=dict(type="str"),
            new_name=dict(type="str"),
        ),
        supports_check_mode=True,
        mutually_exclusive=[
            ("destination", "new_name"),
        ],
    )

    name = module.params["name"]
    state = module.params["state"]
    executable = module.get_bin_path(module.params["executable"], required=True)
    destination = module.params["destination"]
    default = module.params["default"]
    identity = module.params["identity"]
    port = module.params["port"]
    socket_path = module.params["socket_path"]
    new_name = module.params["new_name"]

    # Validate required parameters - always require destination when state=present (except for rename)
    if state == "present" and not new_name and not destination:
        module.fail_json(msg="destination is required when state=present")

    # Get current connection state
    current_conn = get_connection_info(module, executable, name)

    changed = False
    actions = []
    connection_info = {}
    diff = {"before": {}, "after": {}}

    if state == "present":
        if new_name:
            # Handle rename operation
            if not current_conn:
                module.fail_json(msg="Cannot rename non-existent connection '%s'" % name)

            # Check if new name already exists
            new_conn = get_connection_info(module, executable, new_name)
            if new_conn:
                # Check if the existing connection with new_name is identical to current_conn
                if connections_are_identical(current_conn, new_conn):
                    # Connections are identical - idempotent, no changes needed
                    connection_info = new_conn
                else:
                    # Different connection exists with the same name - fail
                    module.fail_json(msg="Connection with name '%s' already exists and is different" % new_name)
            else:
                # Perform rename
                changed, rename_actions = rename_connection(module, executable, name, new_name)
                actions.extend(rename_actions)

                # Get connection info after rename
                if not module.check_mode:
                    final_conn = get_connection_info(module, executable, new_name)
                    connection_info = final_conn
                else:
                    old_conn_info = get_connection_info(module, executable, name)
                    old_conn_info["Name"] = new_name
                    connection_info = old_conn_info

        else:
            # Handle add/update operation (destination is always provided)
            needs_update, diff = connection_needs_update(current_conn, module.params)
            if needs_update:
                # Remove existing connection if it exists with different parameters
                if current_conn:
                    changed, remove_actions = remove_connection(module, executable, name)
                    actions.extend(remove_actions)

                # Add the connection with desired parameters
                changed, add_actions = add_connection(
                    module, executable, name, destination, default, identity, port, socket_path
                )
                actions.extend(add_actions)

                # Get final connection state
                if not module.check_mode:
                    final_conn = get_connection_info(module, executable, name)
                    connection_info = final_conn
                else:
                    # In check mode, provide expected values
                    connection_info = {
                        "Name": name,
                        "URI": destination,
                        "Default": default,
                    }

            else:
                # Connection exists and matches desired state - idempotent
                connection_info = current_conn

    elif state == "absent":
        if current_conn:
            changed, remove_actions = remove_connection(module, executable, name)
            actions.extend(remove_actions)
        connection_info = {}
    module.log("PODMAN-SYSTEM-CONNECTION: changed=%s, actions=%s, diff=%s" % (changed, actions, diff))
    diff_info = {}
    if diff["before"] or diff["after"]:
        diff_info = {
            "before": "\n".join(["%s - %s" % (k, v) for k, v in sorted(diff["before"].items())]) + "\n",
            "after": "\n".join(["%s - %s" % (k, v) for k, v in sorted(diff["after"].items())]) + "\n",
        }
    module.exit_json(
        changed=changed,
        connection=connection_info,
        actions=actions,
        diff=diff_info,
    )


if __name__ == "__main__":
    main()
