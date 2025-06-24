#!/usr/bin/python
# Copyright (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
module: podman_image_info
author:
  - Sam Doran (@samdoran)
short_description: Gather info about images using podman
notes:
  - Podman may required elevated privileges in order to run properly.
description:
  - Gather info about images using C(podman)
options:
  executable:
    description:
      - Path to C(podman) executable if it is not in the C($PATH) on the machine running C(podman)
    default: 'podman'
    type: str
  name:
    description:
      - List of tags or UID to gather info about. If no name is given return info about all images.
    type: list
    elements: str

"""

EXAMPLES = r"""
- name: Gather info for all images
  containers.podman.podman_image_info:

- name: Gather info on a specific image
  containers.podman.podman_image_info:
    name: nginx

- name: Gather info on several images
  containers.podman.podman_image_info:
    name:
      - redis
      - quay.io/bitnami/wildfly
"""

RETURN = r"""
images:
    description: info from all or specified images
    returned: always
    type: list
    sample: [
        {
            "Id": "029bed813f07be84fae0344cbf8076ced5ea3c929d5f064ba617ac7d8c610a4b",
            "Digest": "sha256:3362f865019db5f14ac5154cb0db2c3741ad1cce0416045be422ad4de441b081",
            "RepoTags": [
                "docker.io/library/alpine:3.15",
                "quay.io/podman/alpine:3.15",
                "quay.io/podman/alpine:3.15"
            ],
            "RepoDigests": [
                "docker.io/library/alpine@sha256:3362f865019db5f14ac5154cb0db2c3741ad1cce0416045be422ad4de441b081",
                "docker.io/library/alpine@sha256:c58a2fce65cb3487f965d2fb08eec4843384dbe29264f427b665421db1aabef2",
                "quay.io/podman/alpine@sha256:3362f865019db5f14ac5154cb0db2c3741ad1cce0416045be422ad4de441b081",
                "quay.io/podman/alpine@sha256:c58a2fce65cb3487f965d2fb08eec4843384dbe29264f427b665421db1aabef2",
                "quay.io/podman/alpine@sha256:3362f865019db5f14ac5154cb0db2c3741ad1cce0416045be422ad4de441b081",
                "quay.io/podman/alpine@sha256:c58a2fce65cb3487f965d2fb08eec4843384dbe29264f427b665421db1aabef2"
            ],
            "Parent": "",
            "Comment": "",
            "Created": "2023-06-14T20:42:13.993588153Z",
            "Config": {
                "Env": [
                        "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
                ],
                "Cmd": [
                        "/bin/sh"
                ]
            },
            "Version": "20.10.23",
            "Author": "",
            "Architecture": "amd64",
            "Os": "linux",
            "Size": 11745350,
            "VirtualSize": 11745350,
            "GraphDriver": {
                "Name": "overlay",
                "Data": {
                        "UpperDir": "/home/podman/.local/share/containers/storage/overlay/579b.../diff",
                        "WorkDir": "/home/podman/.local/share/containers/storage/overlay/579b.../work"
                }
            },
            "RootFS": {
                "Type": "layers",
                "Layers": [
                        "sha256:579b..."
                ]
            },
            "Labels": null,
            "Annotations": {},
            "ManifestType": "application/vnd.docker.distribution.manifest.v2+json",
            "User": "",
            "History": [
                {
                        "created": "2023-06-14T20:42:13.893052319Z",
                        "created_by": "/bin/sh -c #(nop) ADD file:234234234 in / "
                },
                {
                        "created": "2023-06-14T20:42:13.993588153Z",
                        "created_by": "/bin/sh -c #(nop)  CMD [\"/bin/sh\"]",
                        "empty_layer": true
                }
            ],
            "NamesHistory": [
                "quay.io/podman/alpine:3.15",
                "quay.io/podman/alpine:3.15",
                "docker.io/library/alpine:3.15"
            ]
        }
    ]
"""

import json

from ansible.module_utils.basic import AnsibleModule


def image_exists(module, executable, name):
    command = [executable, "image", "exists", name]
    rc, out, err = module.run_command(command)
    if rc == 1:
        return False
    elif 'Command "exists" not found' in err:
        # The 'exists' test is available in podman >= 0.12.1
        command = [executable, "image", "ls", "-q", name]
        rc2, out2, err2 = module.run_command(command)
        if rc2 != 0:
            return False
    return True


def filter_invalid_names(module, executable, name):
    valid_names = []
    names = name
    if not isinstance(name, list):
        names = [name]

    for name in names:
        if image_exists(module, executable, name):
            valid_names.append(name)

    return valid_names


def get_image_info(module, executable, name):
    names = name
    if not isinstance(name, list):
        names = [name]

    if len(names) > 0:
        command = [executable, "image", "inspect"]
        command.extend(names)
        rc, out, err = module.run_command(command)

        if rc != 0:
            module.fail_json(msg="Unable to gather info for '{0}': {1}".format(", ".join(names), err))
        return out

    else:
        return json.dumps([])


def get_all_image_info(module, executable):
    command = [executable, "image", "ls", "-q"]
    rc, out, err = module.run_command(command)
    out = out.strip()
    if out:
        name = out.split("\n")
        res = get_image_info(module, executable, name)
        return res
    return json.dumps([])


def main():
    module = AnsibleModule(
        argument_spec=dict(
            executable=dict(type="str", default="podman"),
            name=dict(type="list", elements="str"),
        ),
        supports_check_mode=True,
    )

    executable = module.params["executable"]
    name = module.params.get("name")
    executable = module.get_bin_path(executable, required=True)

    if name:
        valid_names = filter_invalid_names(module, executable, name)
        results = json.loads(get_image_info(module, executable, valid_names))
    else:
        results = json.loads(get_all_image_info(module, executable))

    results = dict(changed=False, images=results)

    module.exit_json(**results)


if __name__ == "__main__":
    main()
