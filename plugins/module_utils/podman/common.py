# Copyright (c) 2020 Red Hat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import json
import os
import shutil


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


def generate_systemd(module, module_params, name):
    """Generate systemd unit file."""
    command = [module_params['executable'], 'generate', 'systemd',
               name, '--format', 'json']
    sysconf = module_params['generate_systemd']
    empty = {}
    if sysconf.get('restart_policy'):
        if sysconf.get('restart_policy') not in [
            "no", "on-success", "on-failure", "on-abnormal", "on-watchdog",
                "on-abort", "always"]:
            module.fail_json(
                'Restart policy for systemd unit file is "%s" and must be one of: '
                '"no", "on-success", "on-failure", "on-abnormal", "on-watchdog", "on-abort", or "always"' %
                sysconf.get('restart_policy'))
        command.extend([
            '--restart-policy',
            sysconf['restart_policy']])
    if sysconf.get('time'):
        command.extend(['--time', str(sysconf['time'])])
    if sysconf.get('no_header'):
        command.extend(['--no-header'])
    if sysconf.get('names', True):
        command.extend(['--name'])
    if sysconf.get('container_prefix'):
        command.extend(['--container-prefix=%s' % sysconf['container_prefix']])
    if sysconf.get('pod_prefix'):
        command.extend(['--pod-prefix=%s' % sysconf['pod_prefix']])
    if sysconf.get('separator'):
        command.extend(['--separator=%s' % sysconf['separator']])
    if module.params['debug'] or module_params['debug']:
        module.log("PODMAN-CONTAINER-DEBUG: systemd command: %s" %
                   " ".join(command))
    rc, systemd, err = module.run_command(command)
    if rc != 0:
        module.log(
            "PODMAN-CONTAINER-DEBUG: Error generating systemd: %s" % err)
        return empty
    else:
        try:
            data = json.loads(systemd)
            if sysconf.get('path'):
                if not os.path.exists(sysconf['path']):
                    os.makedirs(sysconf['path'])
                if not os.path.isdir(sysconf['path']):
                    module.fail_json("Path %s is not a directory! "
                                     "Can not save systemd unit files there!"
                                     % sysconf['path'])
                for file_name, file_content in data.items():
                    file_name += ".service"
                    with open(os.path.join(sysconf['path'], file_name), 'w') as f:
                        f.write(file_content)
            return data
        except Exception as e:
            module.log(
                "PODMAN-CONTAINER-DEBUG: Error writing systemd: %s" % e)
            return empty


def lower_keys(x):
    if isinstance(x, list):
        return [lower_keys(v) for v in x]
    elif isinstance(x, dict):
        return dict((k.lower(), lower_keys(v)) for k, v in x.items())
    else:
        return x


def remove_file_or_dir(path):
    if os.path.isfile(path):
        os.unlink(path)
    elif os.path.isdir(path):
        shutil.rmtree(path)
    else:
        raise ValueError("file %s is not a file or dir." % path)
