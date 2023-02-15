# Copyright (c) 2020 Red Hat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import json
import os
import shutil

from ansible.module_utils.six import raise_from
try:
    from ansible.module_utils.compat.version import LooseVersion  # noqa: F401
except ImportError:
    try:
        from distutils.version import LooseVersion  # noqa: F401
    except ImportError as exc:
        raise_from(ImportError('To use this plugin or module with ansible-core'
                               ' < 2.11, you need to use Python < 3.12 with '
                               'distutils.version present'), exc)


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


def run_generate_systemd_command(module, module_params, name, version):
    """Generate systemd unit file."""
    command = [module_params['executable'], 'generate', 'systemd',
               name, '--format', 'json']
    sysconf = module_params['generate_systemd']
    gt4ver = LooseVersion(version) >= LooseVersion('4.0.0')
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
    if sysconf.get("new"):
        command.extend(["--new"])
    if sysconf.get('container_prefix') is not None:
        command.extend(['--container-prefix=%s' % sysconf['container_prefix']])
    if sysconf.get('pod_prefix') is not None:
        command.extend(['--pod-prefix=%s' % sysconf['pod_prefix']])
    if sysconf.get('separator') is not None:
        command.extend(['--separator=%s' % sysconf['separator']])
    if sysconf.get('after') is not None:

        sys_after = sysconf['after']
        if isinstance(sys_after, str):
            sys_after = [sys_after]
        for after in sys_after:
            command.extend(['--after=%s' % after])
    if sysconf.get('wants') is not None:
        sys_wants = sysconf['wants']
        if isinstance(sys_wants, str):
            sys_wants = [sys_wants]
        for want in sys_wants:
            command.extend(['--wants=%s' % want])
    if sysconf.get('requires') is not None:
        sys_req = sysconf['requires']
        if isinstance(sys_req, str):
            sys_req = [sys_req]
        for require in sys_req:
            command.extend(['--requires=%s' % require])
    for param in ['after', 'wants', 'requires']:
        if sysconf.get(param) is not None and not gt4ver:
            module.fail_json(msg="Systemd parameter '%s' is supported from "
                             "podman version 4 only! Current version is %s" % (
                                 param, version))

    if module.params['debug'] or module_params['debug']:
        module.log("PODMAN-CONTAINER-DEBUG: systemd command: %s" %
                   " ".join(command))
    rc, systemd, err = module.run_command(command)
    return rc, systemd, err


def generate_systemd(module, module_params, name, version):
    empty = {}
    sysconf = module_params['generate_systemd']
    rc, systemd, err = run_generate_systemd_command(module, module_params, name, version)
    if rc != 0:
        module.log(
            "PODMAN-CONTAINER-DEBUG: Error generating systemd: %s" % err)
        return empty
    else:
        try:
            data = json.loads(systemd)
            if sysconf.get('path'):
                full_path = os.path.expanduser(sysconf['path'])
                if not os.path.exists(full_path):
                    os.makedirs(full_path)
                if not os.path.isdir(full_path):
                    module.fail_json("Path %s is not a directory! "
                                     "Can not save systemd unit files there!"
                                     % full_path)
                for file_name, file_content in data.items():
                    file_name += ".service"
                    with open(os.path.join(full_path, file_name), 'w') as f:
                        f.write(file_content)
            return data
        except Exception as e:
            module.log(
                "PODMAN-CONTAINER-DEBUG: Error writing systemd: %s" % e)
            return empty


def delete_systemd(module, module_params, name, version):
    sysconf = module_params['generate_systemd']
    if not sysconf.get('path'):
        # We don't know where systemd files are located, nothing to delete
        module.log(
            "PODMAN-CONTAINER-DEBUG: Not deleting systemd file - no path!")
        return
    rc, systemd, err = run_generate_systemd_command(module, module_params, name, version)
    if rc != 0:
        module.log(
            "PODMAN-CONTAINER-DEBUG: Error generating systemd: %s" % err)
        return
    else:
        try:
            data = json.loads(systemd)
            for file_name in data.keys():
                file_name += ".service"
                full_dir_path = os.path.expanduser(sysconf['path'])
                file_path = os.path.join(full_dir_path, file_name)
                if os.path.exists(file_path):
                    os.unlink(file_path)
            return
        except Exception as e:
            module.log(
                "PODMAN-CONTAINER-DEBUG: Error deleting systemd: %s" % e)
            return


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


# Generated from https://github.com/containers/podman/blob/main/pkg/signal/signal_linux.go
# and https://github.com/containers/podman/blob/main/pkg/signal/signal_linux_mipsx.go
_signal_map = {
    "ABRT": 6,
    "ALRM": 14,
    "BUS": 7,
    "CHLD": 17,
    "CLD": 17,
    "CONT": 18,
    "EMT": 7,
    "FPE": 8,
    "HUP": 1,
    "ILL": 4,
    "INT": 2,
    "IO": 29,
    "IOT": 6,
    "KILL": 9,
    "PIPE": 13,
    "POLL": 29,
    "PROF": 27,
    "PWR": 30,
    "QUIT": 3,
    "RTMAX": 64,
    "RTMIN": 34,
    "SEGV": 11,
    "STKFLT": 16,
    "STOP": 19,
    "SYS": 31,
    "TERM": 15,
    "TRAP": 5,
    "TSTP": 20,
    "TTIN": 21,
    "TTOU": 22,
    "URG": 23,
    "USR1": 10,
    "USR2": 12,
    "VTALRM": 26,
    "WINCH": 28,
    "XCPU": 24,
    "XFSZ": 25
}

for i in range(1, _signal_map['RTMAX'] - _signal_map['RTMIN'] + 1):
    _signal_map['RTMIN+{0}'.format(i)] = _signal_map['RTMIN'] + i
    _signal_map['RTMAX-{0}'.format(i)] = _signal_map['RTMAX'] - i


def normalize_signal(signal_name_or_number):
    signal_name_or_number = str(signal_name_or_number)
    if signal_name_or_number.isdigit():
        return signal_name_or_number
    else:
        signal_name = signal_name_or_number.upper()
        if signal_name.startswith('SIG'):
            signal_name = signal_name[3:]
        if signal_name not in _signal_map:
            raise RuntimeError("Unknown signal '{0}'".format(signal_name_or_number))
        return str(_signal_map[signal_name])
