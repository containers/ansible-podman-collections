#!/usr/bin/python
# Copyright (c) 2024 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
module: podman_search
author:
  - Derek Waters (@derekwaters)
short_description: Search for remote images using podman
notes:
  - Podman may required elevated privileges in order to run properly.
description:
  - Search for remote images using C(podman)
options:
  executable:
    description:
      - Path to C(podman) executable if it is not in the C($PATH) on the machine running C(podman)
    default: 'podman'
    type: str
  term:
    description:
      - The search term to look for. Will search all default registries unless a registry is defined in the search term.
    type: str
    required: True
  limit:
    description:
      - Limit the number of image results returned from the search (per image registry)
    required: False
    default: 25
    type: int
  list_tags:
    description:
      - Whether or not to return the list of tags associated with each image
    required: False
    default: False
    type: bool

"""

EXAMPLES = r"""
- name: Search for any rhel images
  containers.podman.podman_search:
    term: "rhel"
    limit: 3

- name: Gather info on a specific remote image
  containers.podman.podman_search:
    term: "myimageregistry.com/ansible-automation-platform/ee-minimal-rhel8"

- name: Gather tag info on a known remote image
  containers.podman.podman_search:
    term: "myimageregistry.com/ansible-automation-platform/ee-minimal-rhel8"
    list_tags: True
"""

RETURN = r"""
images:
    description: info from all or specified images
    returned: always
    type: list
    sample: [
        {
            "Automated": "",
            "Description": "Red Hat Enterprise Linux Atomic Image is a minimal, fully supported base image.",
            "Index": "registry.access.redhat.com",
            "Name": "registry.access.redhat.com/rhel7-atomic",
            "Official": "",
            "Stars": 0,
            "Tags": ["1.0", "1.1", "1.1.1-devel"]
        }
    ]
"""

import json

from ansible.module_utils.basic import AnsibleModule


def search_images(module, executable, term, limit, list_tags):
    command = [executable, "search", term, "--format", "json"]
    command.extend(["--limit", "{0}".format(limit)])
    if list_tags:
        command.extend(["--list-tags"])

    rc, out, err = module.run_command(command)
    if rc != 0 and list_tags and out == "" and "fetching tags list" in err:
        return out, err
    if rc != 0:
        module.fail_json(msg="Unable to gather info for '{0}': {1}".format(term, err))
    return out, err


def main():
    module = AnsibleModule(
        argument_spec=dict(
            executable=dict(type="str", default="podman"),
            term=dict(type="str", required=True),
            limit=dict(type="int", required=False, default=25),
            list_tags=dict(type="bool", required=False, default=False),
        ),
        supports_check_mode=True,
    )

    executable = module.params["executable"]
    term = module.params.get("term")
    limit = module.params.get("limit")
    list_tags = module.params.get("list_tags")
    executable = module.get_bin_path(executable, required=True)

    result_str, errors = search_images(module, executable, term, limit, list_tags)
    if result_str == "":
        results = []
    else:
        try:
            results = json.loads(result_str)
        except json.decoder.JSONDecodeError:
            module.fail_json(msg="Failed to parse JSON output from podman search: {out}".format(out=result_str))

    results = dict(
        changed=False,
        images=results,
        stderr=errors,
    )

    module.exit_json(**results)


if __name__ == "__main__":
    main()
