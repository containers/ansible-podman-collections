#!/usr/bin/python
# coding: utf-8 -*-

# Copyright (c) 2020, Sagi Shnaidman <sshnaidm@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
module: podman_save
short_description: Saves podman image to tar file
author: Sagi Shnaidman (@sshnaidm)
description:
  - podman save saves an image to either docker-archive, oci-archive, oci-dir
    (directory with oci manifest type), or docker-dir (directory with v2s2 manifest type)
    on the local machine, default is docker-archive.

options:
  image:
    description:
    - Image to save.
    type: list
    elements: str
    required: true
  compress:
    description:
    - Compress tarball image layers when pushing to a directory using the 'dir' transport.
      (default is same compression type, compressed or uncompressed, as source)
    type: bool
  dest:
    description:
    - Destination file to write image to.
    type: str
    required: true
    aliases:
      - path
  format:
    description:
    - Save image to docker-archive, oci-archive (see containers-transports(5)), oci-dir
      (oci transport), or docker-dir (dir transport with v2s2 manifest type).
    type: str
    choices:
    - docker-archive
    - oci-archive
    - oci-dir
    - docker-dir
  multi_image_archive:
    description:
    - Allow for creating archives with more than one image. Additional names will be
      interpreted as images instead of tags. Only supported for docker-archive.
    type: bool
  force:
    description:
    - Force saving to file even if it exists.
    type: bool
    default: True
  executable:
    description:
      - Path to C(podman) executable if it is not in the C($PATH) on the
        machine running C(podman)
    default: 'podman'
    type: str
requirements:
  - "Podman installed on host"
"""

RETURN = """
"""

EXAMPLES = """
# What modules does for example
- containers.podman.podman_save:
    image: nginx
    dest: /tmp/file123.tar
- containers.podman.podman_save:
    image:
      - nginx
      - fedora
    dest: /tmp/file456.tar
    multi_image_archive: true
"""

import os  # noqa: E402
from ansible.module_utils.basic import AnsibleModule  # noqa: E402
from ..module_utils.podman.common import remove_file_or_dir  # noqa: E402


def save(module, executable):
    changed = False
    command = [executable, "save"]
    cmd_args = {
        "compress": ["--compress"],
        "dest": ["-o=%s" % module.params["dest"]],
        "format": ["--format=%s" % module.params["format"]],
        "multi_image_archive": ["--multi-image-archive"],
    }
    for param in module.params:
        if module.params[param] is not None and param in cmd_args:
            command += cmd_args[param]
    for img in module.params["image"]:
        command.append(img)
    if module.params["force"]:
        changed = True
        dest = module.params["dest"]
        if os.path.exists(dest):
            if module.check_mode:
                return changed, "", ""
            try:
                remove_file_or_dir(dest)
            except Exception as e:
                module.fail_json(msg="Error deleting %s path: %s" % (dest, e))
    else:
        changed = not os.path.exists(module.params["dest"])
    if module.check_mode:
        return changed, "", ""
    rc, out, err = module.run_command(command)
    if rc != 0:
        module.fail_json(msg="Error: %s" % (err))
    return changed, out, err


def main():
    module = AnsibleModule(
        argument_spec=dict(
            image=dict(type="list", elements="str", required=True),
            compress=dict(type="bool"),
            dest=dict(type="str", required=True, aliases=["path"]),
            format=dict(
                type="str",
                choices=["docker-archive", "oci-archive", "oci-dir", "docker-dir"],
            ),
            multi_image_archive=dict(type="bool"),
            force=dict(type="bool", default=True),
            executable=dict(type="str", default="podman"),
        ),
        supports_check_mode=True,
    )
    if module.params["compress"] and module.params["format"] not in [
        "oci-dir",
        "docker-dir",
    ]:
        module.fail_json(msg="Compression is only supported for oci-dir and docker-dir format")

    executable = module.get_bin_path(module.params["executable"], required=True)
    changed, out, err = save(module, executable)

    results = {
        "changed": changed,
        "stdout": out,
        "stderr": err,
    }

    module.exit_json(**results)


if __name__ == "__main__":
    main()
