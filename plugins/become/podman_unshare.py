# -*- coding: utf-8 -*-
# Copyright (c) 2022 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# Written by Janos Gerzson (grzs@backendo.com)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    name: podman_unshare
    short_description: Run tasks using podman unshare
    description:
        - This become plugins allows your remote/login user
          to execute commands in its container user namespace.
          Official documentation: https://docs.podman.io/en/latest/markdown/podman-unshare.1.html
    author:
    - Janos Gerzson (@grzs)
    version_added: 1.9.0
"""

EXAMPLES = """
- name: checking uid of file 'foo'
  ansible.builtin.stat:
    path: "{{ test_dir }}/foo"
  register: foo
- ansible.builtin.debug:
    var: foo.stat.uid
# The output shows that it's owned by the login user
# ok: [test_host] => {
#     "foo.stat.uid": "1003"
# }

- name: mounting the file to an unprivileged container and modifying its owner
  containers.podman.podman_container:
    name: chmod_foo
    image: alpine
    rm: yes
    volume:
    - "{{ test_dir }}:/opt/test:z"
    command: chown 1000 /opt/test/foo

# Now the file 'foo' is owned by the container uid 1000,
# which is mapped to something completaly different on the host.
# It creates a situation when the file is unaccessible to the host user (uid 1003)
# Running stat again, debug output will be like this:
# ok: [test_host] => {
#     "foo.stat.uid": "328679"
# }

- name: running stat in modified user namespace
  become_method: containers.podman.podman_unshare
  become: yes
  ansible.builtin.stat:
    path: "{{ test_dir }}/foo"
  register: foo
# By gathering file stats with podman_ushare
# we can see the uid set in the container:
# ok: [test_host] => {
#     "foo.stat.uid": "1000"
# }

- name: resetting file ownership with podman unshare
  become_method: containers.podman.podman_unshare
  become: yes
  ansible.builtin.file:
    state: file
    path: "{{ test_dir }}/foo"
    owner: 0  # in a modified user namespace host uid is mapped to 0
# If we run stat and debug with 'become: no',
# we can see that the file is ours again:
# ok: [test_host] => {
#     "foo.stat.uid": "1003"
# }
"""


from ansible.plugins.become import BecomeBase


class BecomeModule(BecomeBase):

    name = 'containers.podman.podman_unshare'

    def build_become_command(self, cmd, shell):
        super(BecomeModule, self).build_become_command(cmd, shell)

        if not cmd:
            return cmd

        becomecmd = 'podman unshare'

        return ' '.join([becomecmd, self._build_success_command(cmd, shell)])
