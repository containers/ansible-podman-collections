#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# Copyright (c) 2023, Roberto Alfieri <ralfieri@redhat.com>

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
module: podman_prune
author:
    - "Roberto Alfieri (@rebtoor)"
version_added: '1.10.0'
short_description: Allows to prune various podman objects
notes: []
description:
    - Allows to run C(podman container prune), C(podman image prune), C(podman network prune), C(podman volume prune) and C(podman system prune)
requirements:
    - "Podman installed on host"
options:
    executable:
        description:
            - Podman binary.
        type: str
        default: podman
    container:
        description:
            - Whether to prune containers.
        type: bool
        default: false
    container_filters:
        description:
            - A dictionary of filter values used for selecting containers to delete.
            - "For example, C(until: 24h)."
            - See L(the podman documentation, https://docs.podman.io/en/latest/markdown/podman-container-prune.1.html#filter-filters)
              for more information on possible filters.
        type: dict
    image:
        description:
            - Whether to prune images.
        type: bool
        default: false
    image_filters:
        description:
            - A dictionary of filter values used for selecting images to delete.
            - "For example, C(dangling: true)."
            - See L(the podman documentation,https://docs.podman.io/en/latest/markdown/podman-image-prune.1.html#filter-filters)
              for more information on possible filters.
        type: dict
    network:
        description:
            - Whether to prune networks.
        type: bool
        default: false
    network_filters:
        description:
            - A dictionary of filter values used for selecting networks to delete.
            - See L(the podman documentation,https://docs.podman.io/en/latest/markdown/podman-network-prune.1.html#filter)
              for more information on possible filters.
        type: dict
    system:
        description:
            - Wheter to prune unused pods, containers, image, networks and volume data
        type: bool
        default: false
    system_all:
        description:
            - Wheter to prune all unused images, not only dangling images.
        type: bool
        default: false
    system_volumes:
        description:
            - Wheter to prune volumes currently unused by any container.
        type: bool
        default: false
    volume:
        description:
            - Whether to prune volumes.
        type: bool
        default: false
    volume_filters:
        description:
            - A dictionary of filter values used for selecting volumes to delete.
            - See L(the podman documentation,https://docs.podman.io/en/latest/markdown/podman-volume-prune.1.html#filter)
              for more information on possible filters.
        type: dict
"""

EXAMPLES = r"""
- name: Prune containers older than 24h
  containers.podman.podman_prune:
      containers: true
      containers_filters:
          # only consider containers created more than 24 hours ago
          until: 24h

- name: Prune everything
  containers.podman.podman_prune:
      system: true

- name: Prune everything (including non-dangling images)
  containers.podman.podman_prune:
      system: true
      system_all: true
      system_volumes: true
"""

RETURN = r"""
# containers
containers:
    description:
      - List of IDs of deleted containers.
    returned: I(containers) is C(true)
    type: list
    elements: str
    sample: []

# images
images:
    description:
      - List of IDs of deleted images.
    returned: I(images) is C(true)
    type: list
    elements: str
    sample: []

# networks
networks:
    description:
      - List of IDs of deleted networks.
    returned: I(networks) is C(true)
    type: list
    elements: str
    sample: []

# volumes
volumes:
    description:
      - List of IDs of deleted volumes.
    returned: I(volumes) is C(true)
    type: list
    elements: str
    sample: []

# system
system:
  description:
    - List of ID of deleted containers, volumes, images, network and total reclaimed space
  returned: I(system) is C(true)
  type: list
  elements: str
  sample: []
"""


from ansible.module_utils.basic import AnsibleModule


def podmanExec(module, target, filters, executable):
    changed = False
    command = [executable, target, 'prune', '--force']
    if filters != "" and target != "system":
        command.append("--filter=")
        command.append(filters)
    if filters != "" and target == "system":
        split_filters = filters.strip().split(" ")
        for filter in split_filters:
            if filter:
                command.append(filter)
    rc, out, err = module.run_command(command)
    if out:
        changed = True
    if rc != 0:
        module.fail_json(
            msg="Error executing prune on {0}: {1}".format(target, err))
    return changed, out, err


def run_module():
    module_args = dict(
        container=dict(type='bool', default=False),
        container_filters=dict(type='dict'),
        image=dict(type='bool', default=False),
        image_filters=dict(type='dict'),
        network=dict(type='bool', default=False),
        network_filters=dict(type='dict'),
        volume=dict(type='bool', default=False),
        volume_filters=dict(type='dict'),
        system=dict(type='bool', default=False),
        system_all=dict(type='bool', default=False),
        system_volumes=dict(type='bool', default=False),
        executable=dict(type='str', default='podman')
    )

    module = AnsibleModule(
        argument_spec=module_args
    )

    executable = module.get_bin_path(
        module.params['executable'], required=True)

    if module.params["container"]:
        target = "container"
        if not module.params["container_filters"]:
            filters = ""
        else:
            filters = module.params["container_filters"]
        changed, out, err = podmanExec(module, target, filters, executable)
        if not out:
            containers = []
        else:
            containers = out.rstrip().split("\n")
        results = dict(
            changed=changed,
            containers=containers,
            stderr=err
        )

    if module.params["network"]:
        target = "network"
        if not module.params["network_filters"]:
            filters = ""
        else:
            filters = module.params["network_filters"]
        changed, out, err = podmanExec(module, target, filters, executable)
        if not out:
            networks = []
        else:
            networks = out.rstrip().split("\n")
        results = dict(
            changed=changed,
            networks=networks,
            stderr=err
        )

    if module.params["image"]:
        target = "image"
        if not module.params["image_filters"]:
            filters = ""
        else:
            filters = module.params["image_filters"]
        changed, out, err = podmanExec(module, target, filters, executable)
        results = dict(
            changed=changed,
            stdout=out,
            stderr=err
        )

    if module.params["volume"]:
        target = "volume"
        if not module.params["volume_filters"]:
            filters = ""
        else:
            filters = module.params["volume_filters"]
        changed, out, err = podmanExec(module, target, filters, executable)
        if not out:
            volumes = []
        else:
            volumes = out.rstrip().split("\n")
        results = dict(
            changed=changed,
            volumes=volumes,
            stderr=err
        )

    if module.params["system"]:
        target = "system"
        filters = str()

        if module.params["system_all"]:
            filters = " ".join([filters, "--all"])

        if module.params["system_volumes"]:
            filters = " ".join([filters, "--volumes"])

        changed, out, err = podmanExec(module, target, filters, executable)

        results = dict(
            changed=changed,
            stdout=out,
            stderr=err
        )

    module.exit_json(**results)


def main():
    run_module()


if __name__ == '__main__':
    main()
