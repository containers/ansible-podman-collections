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
  driver:
    description:
      - Override default secrets driver, currently podman uses C(file)
        which is unencrypted.
    type: str
  driver_opts:
    description:
      - Driver-specific key-value options.
    type: dict
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
  skip_existing:
    description:
      - Use it when C(state) is C(present) and secret with the same name already exists.
        If set to C(true), the secret will NOT be recreated and remains as is.
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
  labels:
    description:
      - Labels to set on the secret.
    type: dict
  debug:
    description:
      - Enable debug mode for module.
    type: bool
    default: False
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
from ansible_collections.containers.podman.plugins.module_utils.podman.common import LooseVersion
from ansible_collections.containers.podman.plugins.module_utils.podman.common import get_podman_version

diff = {"before": '', "after": ''}


def podman_secret_exists(module, executable, name, version):
    if version is None or LooseVersion(version) < LooseVersion('4.5.0'):
        rc, out, err = module.run_command(
            [executable, 'secret', 'ls', "--format", "{{.Name}}"])
        return name in [i.strip() for i in out.splitlines()]
    rc, out, err = module.run_command(
        [executable, 'secret', 'exists', name])
    return rc == 0


def need_update(module, executable, name, data, driver, driver_opts, debug, labels):

    cmd = [executable, 'secret', 'inspect', '--showsecret', name]
    rc, out, err = module.run_command(cmd)
    if rc != 0:
        if debug:
            module.log("PODMAN-SECRET-DEBUG: Unable to get secret info: %s" % err)
        return True
    try:
        secret = module.from_json(out)[0]
        # We support only file driver for now
        if (driver and driver != 'file') or secret['Spec']['Driver']['Name'] != 'file':
            if debug:
                module.log("PODMAN-SECRET-DEBUG: Idempotency of driver %s is not supported" % driver)
            return True
        if secret['SecretData'] != data:
            diff['after'] = "<different-secret>"
            diff['before'] = "<secret>"
            return True
        if driver_opts:
            for k, v in driver_opts.items():
                if secret['Spec']['Driver']['Options'].get(k) != v:
                    diff['after'] = "=".join([k, v])
                    diff['before'] = "=".join(
                        [k, secret['Spec']['Driver']['Options'].get(k)])
                    return True
        if labels:
            for k, v in labels.items():
                if secret['Spec']['Labels'].get(k) != v:
                    diff['after'] = "=".join([k, v])
                    diff['before'] = "=".join(
                        [k, secret['Spec']['Labels'].get(k)])
                    return True
    except Exception:
        return True
    return False


def podman_secret_create(module, executable, name, data, force, skip,
                         driver, driver_opts, debug, labels):
    podman_version = get_podman_version(module, fail=False)
    if (podman_version is not None and
        LooseVersion(podman_version) >= LooseVersion('4.7.0')
            and (driver is None or driver == 'file')):
        if not skip and need_update(module, executable, name, data, driver, driver_opts, debug, labels):
            podman_secret_remove(module, executable, name)
        else:
            return {"changed": False}
    else:
        if force:
            podman_secret_remove(module, executable, name)
        if skip and podman_secret_exists(module, executable, name, podman_version):
            return {"changed": False}

    cmd = [executable, 'secret', 'create']
    if driver:
        cmd.append('--driver')
        cmd.append(driver)
    if driver_opts:
        cmd.append('--driver-opts')
        cmd.append(",".join("=".join(i) for i in driver_opts.items()))
    if labels:
        for k, v in labels.items():
            cmd.append('--label')
            cmd.append("=".join([k, v]))
    cmd.append(name)
    cmd.append('-')

    rc, out, err = module.run_command(cmd, data=data, binary_data=True)
    if rc != 0:
        module.fail_json(msg="Unable to create secret: %s" % err)

    return {
        "changed": True,
        "diff": {
            "before": diff['before'] + "\n",
            "after": diff['after'] + "\n",
        },
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
            skip_existing=dict(type='bool', default=False),
            driver=dict(type='str'),
            driver_opts=dict(type='dict'),
            labels=dict(type='dict'),
            debug=dict(type='bool', default=False),
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
        skip = module.params['skip_existing']
        driver = module.params['driver']
        driver_opts = module.params['driver_opts']
        debug = module.params['debug']
        labels = module.params['labels']
        results = podman_secret_create(module, executable,
                                       name, data, force, skip,
                                       driver, driver_opts, debug, labels)
    else:
        results = podman_secret_remove(module, executable, name)

    module.exit_json(**results)


if __name__ == '__main__':
    main()
