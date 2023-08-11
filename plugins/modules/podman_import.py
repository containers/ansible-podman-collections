#!/usr/bin/python
# coding: utf-8 -*-

# Copyright (c) 2021, Sagi Shnaidman <sshnaidm@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
module: podman_import
short_description: Import Podman container from a tar file.
author: Sagi Shnaidman (@sshnaidm)
description:
  - podman import imports a tarball (.tar, .tar.gz, .tgz, .bzip, .tar.xz, .txz)
    and saves it as a filesystem image.
options:
  src:
    description:
    - Path to image file to load.
    type: str
    required: true
  commit_message:
    description:
    - Set commit message for imported image
    type: str
  change:
    description:
    - Set changes as list of key-value pairs, see example.
    type: list
    elements: dict
  volume:
    description:
    - Volume to import, cannot be used with change and commit_message
    type: str
  executable:
    description:
      - Path to C(podman) executable if it is not in the C($PATH) on the
        machine running C(podman)
    default: 'podman'
    type: str
requirements:
  - "Podman installed on host"
'''

RETURN = '''
image:
    description: info from loaded image
    returned: always
    type: dict
    sample: {
        "Id": "cbc6d73c4d232db6e8441df96af81855f62c74157b5db80a1d5...",
        "Digest": "sha256:8730c75be86a718929a658db4663d487e562d66762....",
        "RepoTags": [],
        "RepoDigests": [],
        "Parent": "",
        "Comment": "imported from tarball",
        "Created": "2021-09-07T04:45:38.749977105+03:00",
        "Config": {},
        "Version": "",
        "Author": "",
        "Architecture": "amd64",
        "Os": "linux",
        "Size": 5882449,
        "VirtualSize": 5882449,
        "GraphDriver": {
            "Name": "overlay",
            "Data": {
                "UpperDir": "/home/...34/diff",
                "WorkDir": "/home/.../work"
            }
        },
        "RootFS": {
            "Type": "layers",
            "Layers": [
                "sha256:...."
            ]
        },
        "Labels": null,
        "Annotations": {},
        "ManifestType": "application/vnd.oci.image.manifest.v1+json",
        "User": "",
        "History": [
            {
                "created": "2021-09-07T04:45:38.749977105+03:00",
                "created_by": "/bin/sh -c #(nop) ADD file:091... in /",
                "comment": "imported from tarball"
            }
        ],
        "NamesHistory": null
    }
'''

EXAMPLES = '''
# What modules does for example
- containers.podman.podman_import:
    src: /path/to/tar/file
    change:
      - "CMD": /bin/bash
      - "User": root
    commit_message: "Importing image"
- containers.podman.podman_import:
    src: /path/to/tar/file
    volume: myvolume
'''

import json  # noqa: E402
from ansible.module_utils.basic import AnsibleModule  # noqa: E402


def load(module, executable):
    changed = False
    command = [executable, 'import']
    if module.params['commit_message']:
        command.extend(['--message', module.params['commit_message']])
    if module.params['change']:
        for change in module.params['change']:
            command += ['--change', "=".join(list(change.items())[0])]
    command += [module.params['src']]
    changed = True
    if module.check_mode:
        return changed, '', '', '', command
    rc, out, err = module.run_command(command)
    if rc != 0:
        module.fail_json(msg="Image loading failed: %s" % (err))
    image_name_line = [i for i in out.splitlines() if 'sha256' in i][0]
    image_name = image_name_line.split(":", maxsplit=1)[1].strip()
    rc, out2, err2 = module.run_command([executable, 'image', 'inspect', image_name])
    if rc != 0:
        module.fail_json(msg="Image %s inspection failed: %s" % (image_name, err2))
    try:
        info = json.loads(out2)[0]
    except Exception as e:
        module.fail_json(msg="Could not parse JSON from image %s: %s" % (image_name, e))
    return changed, out, err, info, command


def volume_load(module, executable):
    changed = True
    command = [executable, 'volume', 'import', module.params['volume'], module.params['src']]
    src = module.params['src']
    if module.check_mode:
        return changed, '', '', '', command
    rc, out, err = module.run_command(command)
    if rc != 0:
        module.fail_json(msg="Error importing volume %s: %s" % (src, err))
    rc, out2, err2 = module.run_command([executable, 'volume', 'inspect', module.params['volume']])
    if rc != 0:
        module.fail_json(msg="Volume %s inspection failed: %s" % (module.params['volume'], err2))
    try:
        info = json.loads(out2)[0]
    except Exception as e:
        module.fail_json(msg="Could not parse JSON from volume %s: %s" % (module.params['volume'], e))
    return changed, out, err, info, command


def main():
    module = AnsibleModule(
        argument_spec=dict(
            src=dict(type='str', required=True),
            commit_message=dict(type='str'),
            change=dict(type='list', elements='dict'),
            executable=dict(type='str', default='podman'),
            volume=dict(type='str', required=False),
        ),
        mutually_exclusive=[
            ('volume', 'commit_message'),
            ('volume', 'change'),
        ],
        supports_check_mode=True,
    )

    executable = module.get_bin_path(module.params['executable'], required=True)
    volume_info = ''
    image_info = ''
    if module.params['volume']:
        changed, out, err, volume_info, command = volume_load(module, executable)
    else:
        changed, out, err, image_info, command = load(module, executable)

    results = {
        "changed": changed,
        "stdout": out,
        "stderr": err,
        "image": image_info,
        "volume": volume_info,
        "podman_command": " ".join(command)
    }

    module.exit_json(**results)


if __name__ == '__main__':
    main()
