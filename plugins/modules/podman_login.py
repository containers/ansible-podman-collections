#!/usr/bin/python
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
module: podman_login
author:
  - "Jason Hiatt (@jthiatt)"
  - "Clemens Lange (@clelange)"
  - "Michael Fox (@spmfox)"
short_description: Login to a container registry using podman
notes: []
description:
  - Login to a container registry server using the podman login command
    If the registry is not specified, the first registry under
    `[registries.search]` from `registries.conf `will be used. The path of
    the authentication file can be overridden by the user by setting the
    `authfile` flag. The default path used is
    `${XDG_RUNTIME_DIR}/containers/auth.json`.
requirements:
  - "Podman installed on host"
options:
  authfile:
    description:
      - Path of the authentication file. Default is
        ``${XDG_RUNTIME_DIR}/containers/auth.json``
        You can also override the default path of the authentication
        file by setting the ``REGISTRY_AUTH_FILE`` environment
        variable. ``export REGISTRY_AUTH_FILE=path``
    type: path
  certdir:
    description:
      - Use certificates at path (*.crt, *.cert, *.key) to connect
        to the registry.  Default certificates directory
        is /etc/containers/certs.d.
    type: path
  password:
    description:
      - Password for the registry server.
    required: True
    type: str
  registry:
    description:
      - Registry server. If the registry is not specified,
        the first registry under `[registries.search]` from
        `registries.conf` will be used.
    type: str
  tlsverify:
    description:
      - Require HTTPS and verify certificates when
        contacting registries.  If explicitly set to true,
        then TLS verification will be used. If set to false,
        then TLS verification will not be used.  If not specified,
        TLS verification will be used unless the target registry
        is listed as an insecure registry in registries.conf.
    type: bool
  username:
    description:
      - Username for the registry server.
    required: True
    type: str
  executable:
    description:
      - Path to C(podman) executable if it is not in the C($PATH) on the
        machine running C(podman)
    default: 'podman'
    type: str
'''

EXAMPLES = r"""
- name: Login to default registry and create ${XDG_RUNTIME_DIR}/containers/auth.json
  containers.podman.podman_login:
    username: user
    password: 'p4ssw0rd'

- name: Login to default registry and create ${XDG_RUNTIME_DIR}/containers/auth.json
  containers.podman.podman_login:
    username: user
    password: 'p4ssw0rd'
    registry: quay.io

"""
# noqa: F402

import hashlib
import os
from ansible.module_utils.basic import AnsibleModule


def login(module, executable, registry, authfile,
          certdir, tlsverify, username, password):

    command = [executable, 'login']
    changed = False

    if username:
        command.extend(['--username', username])
    if password:
        command.extend(['--password', password])
    if authfile:
        command.extend(['--authfile', authfile])
        authfile = os.path.expandvars(authfile)
    else:
        authfile = os.getenv('XDG_RUNTIME_DIR', '') + '/containers/auth.json'
    if registry:
        command.append(registry)
    if certdir:
        command.extend(['--cert-dir', certdir])
    if tlsverify is not None:
        if tlsverify:
            command.append('--tls-verify')
        else:
            command.append('--tls-verify=False')
    # Use a checksum to check if the auth JSON has changed
    checksum = None
    docker_authfile = os.path.expandvars('$HOME/.docker/config.json')
    # podman falls back to ~/.docker/config.json if the default authfile doesn't exist
    check_file = authfile if os.path.exists(authfile) else docker_authfile
    if os.path.exists(check_file):
        content = open(check_file, 'rb').read()
        checksum = hashlib.sha256(content).hexdigest()
    rc, out, err = module.run_command(command)
    if rc != 0:
        if 'Error: Not logged into' not in err:
            module.fail_json(msg="Unable to gather info for %s: %s" % (registry, err))
    else:
        # If the command is successful, we managed to login
        changed = True
        if 'Existing credentials are valid' in out:
            changed = False
        # If we have managed to calculate a checksum before, check if it has changed
        # due to the login
        if checksum:
            content = open(check_file, 'rb').read()
            new_checksum = hashlib.sha256(content).hexdigest()
            if new_checksum == checksum:
                changed = False
    return changed, out, err


def main():
    module = AnsibleModule(
        argument_spec=dict(
            executable=dict(type='str', default='podman'),
            registry=dict(type='str'),
            authfile=dict(type='path'),
            username=dict(type='str', required=True),
            password=dict(type='str', required=True, no_log=True),
            certdir=dict(type='path'),
            tlsverify=dict(type='bool'),
        ),
        supports_check_mode=True,
        required_together=(
            ['username', 'password'],
        ),
        mutually_exclusive=(
            ['certdir', 'tlsverify'],
        ),
    )

    registry = module.params['registry']
    authfile = module.params['authfile']
    username = module.params['username']
    password = module.params['password']
    certdir = module.params['certdir']
    tlsverify = module.params['tlsverify']
    executable = module.get_bin_path(module.params['executable'], required=True)

    changed, out, err = login(module, executable, registry, authfile,
                              certdir, tlsverify, username, password)

    results = {
        "changed": changed,
        "stdout": out,
        "stderr": err,
    }

    module.exit_json(**results)


if __name__ == '__main__':
    main()
