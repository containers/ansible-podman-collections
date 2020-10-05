#!/usr/bin/python
# Copyright (c) 2020 Red Hat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


def run_podman_command(module, executable='podman', args=None, expected_rc=0, ignore_errors=False):
    if not isinstance(executable, list):
        command = [executable]
    if args is not None:
        command.extend(args)
    rc, out, err = module.run_command(command)
    if not ignore_errors and rc != expected_rc:
        module.fail_json(
            msg='Failed to run {command} {args}: {err}'.format(
                command=command, args=args, err=err))
    return rc, out, err


def lower_keys(x):
    if isinstance(x, list):
        return [lower_keys(v) for v in x]
    elif isinstance(x, dict):
        return dict((k.lower(), lower_keys(v)) for k, v in x.items())
    else:
        return x
