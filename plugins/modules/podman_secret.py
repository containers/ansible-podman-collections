#!/usr/bin/python
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: podman_secret
author:
  - "Aliaksandr Mianzhynski (@amenzhinsky)"
version_added: '1.7.0'
short_description: Manage podman secrets
notes: []
description:
  - Manage podman secrets
requirements:
  - podman
options:
  data:
    description:
      - The value of the secret. Required when C(state) is C(present).
    type: str
  executable:
    description:
      - Path to C(podman) executable if it is not in the C($PATH) on the
        machine running C(podman)
    type: str
    default: 'podman'
  force:
    description:
      - Use it when C(state) is C(present) to remove and recreate an existing secret.
    type: bool
    default: false
  name:
    description:
      - The name of the secret.
    required: True
    type: str
  state:
    description:
      - Whether to create or remove the named secret.
    type: str
    default: present
    choices:
      - absent
      - present
'''

EXAMPLES = r"""
- name: Create secret
  containers.podman.podman_secret:
    state: present
    name: mysecret
    data: "my super secret content"

- name: Create container that uses the secret
  containers.podman.podman_container:
    name: showmysecret
    image: docker.io/alpine:3.14
    secrets:
      - mysecret
    detach: false
    command: cat /run/secrets/mysecret
    register: container

- name: Output secret data
  debug:
    msg: '{{ container.stdout }}'

- name: Remove secret
  containers.podman.podman_secret:
    state: absent
    name: mysecret
    """

from ansible.module_utils.basic import AnsibleModule


def podman_secret_create(module, executable, name, data, force):
    if force:
        module.run_command([executable, 'secret', 'rm', name])

    rc, out, err = module.run_command(
        [executable, 'secret', 'create', name, '-'], data=data)

    if rc != 0:
        module.fail_json(msg="Unable to create secret: %s" % err)

    return {
        "changed": True,
    }


def podman_secret_remove(module, executable, name):
    changed = False
    rc, out, err = module.run_command([executable, 'secret', 'rm', name])
    if rc == 0:
        changed = True
    elif 'no such secret' in err:
        pass
    else:
        module.fail_json(msg="Unable to remove secret: %s" % err)

    return {
        "changed": changed,
    }


def main():
    module = AnsibleModule(
        argument_spec=dict(
            executable=dict(type='str', default='podman'),
            state=dict(type='str', default='present', choices=['absent', 'present']),
            name=dict(type='str', required=True),
            data=dict(type='str', no_log=True),
            force=dict(type='bool', default=False),
        ),
    )

    state = module.params['state']
    name = module.params['name']
    executable = module.get_bin_path(module.params['executable'], required=True)

    if state == 'present':
        data = module.params['data']
        if data is None:
            raise Exception("'data' is required when 'state' is 'present'")
        force = module.params['force']
        results = podman_secret_create(module, executable, name, data, force)
    else:
        results = podman_secret_remove(module, executable, name)

    module.exit_json(**results)


if __name__ == '__main__':
    main()
