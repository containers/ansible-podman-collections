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
        - This become plugins allows your remote/login user to execute commands in its container user namespace
    author:
    - Janos Gerzson (@grzs)
    version_added: 1.9.4
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
