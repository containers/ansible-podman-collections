#!/usr/bin/python
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
module: podman_logout
author:
  - "Clemens Lange (@clelange)"
short_description: Log out of a container registry using podman
notes: []
description:
  - Log out of a container registry server using the podman logout command
    by deleting the cached credentials stored in the `auth.json` file.
    If the registry is not specified, the first registry under
    `[registries.search]` from `registries.conf `will be used. The path of
    the authentication file can be overridden by the user by setting the
    `authfile` flag. The default path used is
    `${XDG_RUNTIME_DIR}/containers/auth.json`.
    All the cached credentials can be removed by setting the `all` flag.
    Warning - podman will use credentials in `${HOME}/.docker/config.json`
    to authenticate in case they are not found in the default `authfile`.
    However, the logout command will only removed credentials in the
    `authfile` specified.
requirements:
  - "Podman installed on host"
options:
  registry:
    description:
      - Registry server. If the registry is not specified,
        the first registry under `[registries.search]` from
        `registries.conf` will be used.
    type: str
  authfile:
    description:
      - Path of the authentication file. Default is
        ``${XDG_RUNTIME_DIR}/containers/auth.json``
        You can also override the default path of the authentication
        file by setting the ``REGISTRY_AUTH_FILE`` environment
        variable. ``export REGISTRY_AUTH_FILE=path``
    type: path
  all:
    description:
      - Remove the cached credentials for all registries in the auth file.
    type: bool
  ignore_docker_credentials:
    description:
      - Credentials created using other tools such as `docker login` are not
        removed unless the corresponding `authfile` is explicitly specified.
        Since podman also uses existing credentials in these files by default
        (for docker e.g. `${HOME}/.docker/config.json`), module execution will
        fail if a docker login exists for the registry specified in any
        `authfile` is used by podman. This can be ignored by setting
        `ignore_docker_credentials` to `true` - the credentials will be kept and
        `changed` will be false.
        This option cannot be used together with `all` since in this case
        podman will not check for existing `authfiles` created by other tools.
    type: bool
  executable:
    description:
      - Path to C(podman) executable if it is not in the C($PATH) on the
        machine running C(podman)
    default: 'podman'
    type: str
'''

EXAMPLES = r"""
- name: Log out of default registry
  podman_logout:

- name: Log out of quay.io
  podman_logout:
    registry: quay.io

- name: Log out of all registries in auth file
  podman_logout:
    all: true

- name: Log out of all registries in specified auth file
  podman_logout:
    authfile: $HOME/.docker/config.json
    all: true
"""
# noqa: F402

from ansible.module_utils.basic import AnsibleModule


def logout(module, executable, registry, authfile, all_registries, ignore_docker_credentials):
    command = [executable, 'logout']
    changed = False
    if authfile:
        command.extend(['--authfile', authfile])
    if registry:
        command.append(registry)
    if all_registries:
        command.append("--all")
    rc, out, err = module.run_command(command)
    if rc != 0:
        if 'Error: Not logged into' not in err:
            module.fail_json(msg="Unable to gather info for %s: %s" % (registry, err))
    else:
        # If the command is successful, we managed to log out
        # Mind: This also applied if --all flag is used, while in this case
        # there is no check whether one has been logged into any registry
        changed = True
    if 'Existing credentials were established via' in out:
        # The command will return successfully but not log out the user if the
        # credentials were initially created using docker. Catch this behaviour:
        if not ignore_docker_credentials:
            module.fail_json(msg="Unable to log out %s: %s" % (registry or '', out))
        else:
            changed = False
    return changed, out, err


def main():
    module = AnsibleModule(
        argument_spec=dict(
            executable=dict(type='str', default='podman'),
            registry=dict(type='str'),
            authfile=dict(type='path'),
            all=dict(type='bool'),
            ignore_docker_credentials=dict(type='bool'),
        ),
        supports_check_mode=True,
        mutually_exclusive=(
            ['registry', 'all'],
            ['ignore_docker_credentials', 'all'],
        ),
    )

    registry = module.params['registry']
    authfile = module.params['authfile']
    all_registries = module.params['all']
    ignore_docker_credentials = module.params['ignore_docker_credentials']
    executable = module.get_bin_path(module.params['executable'], required=True)

    changed, out, err = logout(module, executable, registry, authfile,
                               all_registries, ignore_docker_credentials)

    results = {
        "changed": changed,
        "stdout": out,
        "stderr": err,
    }

    module.exit_json(**results)


if __name__ == '__main__':
    main()
