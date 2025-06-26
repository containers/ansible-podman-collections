#!/usr/bin/python
# Copyright (c) 2024 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
module: podman_container_copy
author:
  - Alessandro Rossi (@kubealex)
short_description: Copy file to/from a container
notes:
  - Podman may required elevated privileges in order to run properly.
description:
  - Copy file or folder from the host to a container and vice-versa.
options:
  executable:
    description:
      - Path to C(podman) executable if it is not in the C($PATH) on the machine running C(podman)
    default: 'podman'
    type: str
  src:
    description:
      - Path of the file/folder to copy from/to the container
    type: str
    required: True
  dest:
    description:
      - Path of the destination file/folder to copy from/to the container
    required: True
    type: str
  container:
    description:
      - Name/ID of the container to copy from/to
    required: True
    type: str
  from_container:
    description:
      - Specify whether or not the file must be copied from the container to the host
    required: False
    default: False
    type: bool
  archive:
    description:
      - Chown copied files to the primary uid/gid of the destination container.
    required: False
    default: True
    type: bool
  overwrite:
    description:
      - Allow to overwrite directories with non-directories and vice versa
    required: False
    default: False
    type: bool
"""

EXAMPLES = r"""
- name: Copy file "test.yml" on the host to the "apache" container's root folder
  containers.podman.podman_container_copy:
    src: test.yml
    dest: /
    container: apache
- name: Copy file "test.yml" in the "apache" container's root folder to the playbook's folder
  containers.podman.podman_container_copy:
    src: /test.yml
    dest: ./
    container: apache
    from_container: True
"""

from ansible.module_utils.basic import AnsibleModule


def copy_file(module, executable, src, dest, container, from_container, archive, overwrite):
    if from_container:
        command = [executable, "cp", "{0}:{1}".format(container, src), dest]
    else:
        command = [executable, "cp", src, "{0}:{1}".format(container, dest)]

    if not archive:
        command.append("--archive=False")

    if overwrite:
        command.append("--overwrite")

    rc, out, err = module.run_command(command)

    if rc != 0:
        module.fail_json(msg="Unable to copy file to/from container - {out}".format(out=err))
    else:
        changed = True
    return changed, out, err


def main():
    module = AnsibleModule(
        argument_spec=dict(
            executable=dict(type="str", default="podman"),
            src=dict(type="str", required=True),
            dest=dict(type="str", required=True),
            container=dict(type="str", required=True),
            from_container=dict(type="bool", required=False, default=False),
            archive=dict(type="bool", required=False, default=True),
            overwrite=dict(type="bool", required=False, default=False),
        ),
        supports_check_mode=False,
    )

    executable = module.params["executable"]
    src = module.params["src"]
    dest = module.params["dest"]
    container = module.params["container"]
    from_container = module.params["from_container"]
    archive = module.params["archive"]
    overwrite = module.params["overwrite"]

    executable = module.get_bin_path(executable, required=True)

    changed, out, err = copy_file(module, executable, src, dest, container, from_container, archive, overwrite)

    results = dict(changed=changed)

    module.exit_json(**results)


if __name__ == "__main__":
    main()
