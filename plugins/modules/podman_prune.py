#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# Copyright (c) 2023, Roberto Alfieri <ralfieri@redhat.com>

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
module: podman_prune
author:
    - 'Roberto Alfieri (@rebtoor)'
version_added: '1.10.0'
short_description: Allows to prune various podman objects
notes: []
description:
    - Allows to run C(podman container prune), C(podman image prune), C(podman network prune),
      C(podman volume prune) and C(podman system prune)
requirements:
    - 'Podman installed on host'
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
            - 'For example, C(until: 24h).'
            - See L(the podman documentation,
              https://docs.podman.io/en/latest/markdown/podman-container-prune.1.html#filter-filters)
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
            - 'You can also use C(dangling_only: false) to delete dangling and non-dangling images or C(external: true)
              to delete images even when they are used by external containers.'
            - See L(the podman documentation,
              https://docs.podman.io/en/latest/markdown/podman-image-prune.1.html#filter-filters)
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
            - See L(the podman documentation,
              https://docs.podman.io/en/latest/markdown/podman-network-prune.1.html#filter)
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
            - See L(the podman documentation,
              https://docs.podman.io/en/latest/markdown/podman-volume-prune.1.html#filter)
              for more information on possible filters.
        type: dict
'''

EXAMPLES = r'''
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
'''

RETURN = r'''
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
'''


from ansible.module_utils.basic import AnsibleModule


def filtersPrepare(target, filters):
    filter_out = []
    if target == 'system':
        for system_filter in filters:
            filter_out.append(filters[system_filter])
    else:
        for common_filter in filters:
            if isinstance(filters[common_filter], dict):
                dict_filters = filters[common_filter]
                for single_filter in dict_filters:
                    filter_out.append('--filter={label}={key}={value}'.format(label=common_filter, key=single_filter,
                                                                              value=dict_filters[single_filter]))
            else:
                if target == 'image' and (common_filter in ('dangling_only', 'external')):
                    if common_filter == 'dangling_only' and not filters['dangling_only']:
                        filter_out.append('-a')
                    if common_filter == 'external' and filters['external']:
                        filter_out.append('--external')
                else:
                    filter_out.append('--filter={label}={value}'.format(label=common_filter,
                                                                        value=filters[common_filter]))

    return filter_out


def podmanExec(module, target, filters, executable):
    command = [executable, target, 'prune', '--force']
    if filters is not None:
        command.extend(filtersPrepare(target, filters))
    rc, out, err = module.run_command(command)
    changed = bool(out)

    if rc != 0:
        module.fail_json(
            msg='Error executing prune on {target}: {err}'.format(target=target, err=err))

    return {
        "changed": changed,
        target: list(filter(None, out.split('\n'))),
        "errors": err
    }


def main():
    results = dict()
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

    for target, filters in (
            ('container', 'container_filters'), ('image', 'image_filters'), ('network', 'network_filters'),
            ('volume', 'volume_filters')):
        if module.params[target]:
            results[target] = podmanExec(module, target, module.params[filters], executable)

    if module.params['system']:
        target = 'system'
        system_filters = {}
        if module.params['system_all']:
            system_filters['system_all'] = '--all'
        if module.params['system_volumes']:
            system_filters['system_volumes'] = '--volumes'
        results[target] = podmanExec(module, target, system_filters, executable)

    module.exit_json(**results)


if __name__ == '__main__':
    main()
