#!/usr/bin/python
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r"""
module: podman_login_info
author:
  - "Clemens Lange (@clelange)"
version_added: '1.0.0'
short_description: Return the logged-in user if any for a given registry
notes: []
description:
  - Return the logged-in user if any for a given registry.
requirements:
  - "Podman installed on host"
options:
  registry:
    description:
      - Registry server.
    type: str
    required: true
  authfile:
    description:
      - Path of the authentication file. Default is
        ``${XDG_RUNTIME_DIR}/containers/auth.json``
        (Not available for remote commands) You can also override the default
        path of the authentication file by setting the ``REGISTRY_AUTH_FILE``
        environment variable. ``export REGISTRY_AUTH_FILE=path``
    type: path
  executable:
    description:
      - Path to C(podman) executable if it is not in the C($PATH) on the
        machine running C(podman)
    default: 'podman'
    type: str
"""

EXAMPLES = r"""
- name: Return the logged-in user for docker hub registry
  containers.podman.podman_login_info:
    registry: docker.io

- name: Return the logged-in user for quay.io registry
  containers.podman.podman_login_info:
    registry: quay.io
"""

RETURN = r"""
login:
    description: Logged in user for a registry
    returned: always
    type: dict
    sample: {
              "logged_in": true,
              "registry": "docker.io",
              "username": "clelange",
            }
"""

from ansible.module_utils.basic import AnsibleModule


def get_login_info(module, executable, authfile, registry):
    command = [executable, 'login', '--get-login']
    result = dict(
        registry=registry,
        username='',
        logged_in=False,
    )
    if authfile:
        command.extend(['--authfile', authfile])
    if registry:
        command.append(registry)
    rc, out, err = module.run_command(command)
    if rc != 0:
        if 'Error: not logged into' in err:
            # The error message is e.g. 'Error: not logged into docker.io'
            # Therefore get last word to extract registry name
            result["registry"] = err.split()[-1]
            err = ''
            return result
        module.fail_json(msg="Unable to gather info for %s: %s" % (registry, err))
    result["username"] = out.strip()
    result["logged_in"] = True
    return result


def main():
    module = AnsibleModule(
        argument_spec=dict(
            executable=dict(type='str', default='podman'),
            authfile=dict(type='path'),
            registry=dict(type='str', required=True)
        ),
        supports_check_mode=True,
    )

    registry = module.params['registry']
    authfile = module.params['authfile']
    executable = module.get_bin_path(module.params['executable'], required=True)

    inspect_results = get_login_info(module, executable, authfile, registry)

    results = {
        "changed": False,
        "login": inspect_results,
    }

    module.exit_json(**results)


if __name__ == '__main__':
    main()
