# Copyright (c) 2020 Red Hat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json
import os
import shutil

try:
    from ansible.module_utils.compat.version import LooseVersion  # noqa: F401
except ImportError:
    try:
        from distutils.version import LooseVersion  # noqa: F401
    except ImportError as exc:
        raise ImportError(
            "To use this plugin or module with ansible-core"
            " < 2.11, you need to use Python < 3.12 with "
            "distutils.version present"
        ) from exc

ARGUMENTS_OPTS_DICT = {
    "--attach": ["--attach", "-a"],
    "--cpu-shares": ["--cpu-shares", "-c"],
    "--detach": ["--detach", "-d"],
    "--env": ["--env", "-e"],
    "--hostname": ["--hostname", "-h"],
    "--interactive": ["--interactive", "-i"],
    "--label": ["--label", "-l"],
    "--memory": ["--memory", "-m"],
    "--network": ["--network", "--net"],
    "--publish": ["--publish", "-p"],
    "--publish-all": ["--publish-all", "-P"],
    "--quiet": ["--quiet", "-q"],
    "--tty": ["--tty", "-t"],
    "--user": ["--user", "-u"],
    "--volume": ["--volume", "-v"],
    "--workdir": ["--workdir", "-w"],
}


def run_podman_command(module, executable="podman", args=None, expected_rc=0, ignore_errors=False):
    if not isinstance(executable, list):
        command = [executable]
    if args is not None:
        command.extend(args)
    rc, out, err = module.run_command(command)
    if not ignore_errors and rc != expected_rc:
        module.fail_json(msg="Failed to run {command} {args}: {err}".format(command=command, args=args, err=err))
    return rc, out, err


def run_generate_systemd_command(module, module_params, name, version):
    """Generate systemd unit file."""
    command = [
        module_params["executable"],
        "generate",
        "systemd",
        name,
        "--format",
        "json",
    ]
    sysconf = module_params["generate_systemd"]
    gt4ver = LooseVersion(version) >= LooseVersion("4.0.0")
    if sysconf.get("restart_policy"):
        if sysconf.get("restart_policy") not in [
            "no",
            "on-success",
            "on-failure",
            "on-abnormal",
            "on-watchdog",
            "on-abort",
            "always",
        ]:
            module.fail_json(
                'Restart policy for systemd unit file is "%s" and must be one of: '
                '"no", "on-success", "on-failure", "on-abnormal", "on-watchdog", "on-abort", or "always"'
                % sysconf.get("restart_policy")
            )
        command.extend(["--restart-policy", sysconf["restart_policy"]])
    if sysconf.get("restart_sec") is not None:
        command.extend(["--restart-sec=%s" % sysconf["restart_sec"]])
    if (sysconf.get("stop_timeout") is not None) or (sysconf.get("time") is not None):
        # Select correct parameter name based on version
        arg_name = "stop-timeout" if gt4ver else "time"
        arg_value = sysconf.get("stop_timeout") if sysconf.get("stop_timeout") is not None else sysconf.get("time")
        command.extend(["--%s=%s" % (arg_name, arg_value)])
    if sysconf.get("start_timeout") is not None:
        command.extend(["--start-timeout=%s" % sysconf["start_timeout"]])
    if sysconf.get("no_header"):
        command.extend(["--no-header"])
    if sysconf.get("names", True):
        command.extend(["--name"])
    if sysconf.get("new"):
        command.extend(["--new"])
    if sysconf.get("container_prefix") is not None:
        command.extend(["--container-prefix=%s" % sysconf["container_prefix"]])
    if sysconf.get("pod_prefix") is not None:
        command.extend(["--pod-prefix=%s" % sysconf["pod_prefix"]])
    if sysconf.get("separator") is not None:
        command.extend(["--separator=%s" % sysconf["separator"]])
    if sysconf.get("after") is not None:

        sys_after = sysconf["after"]
        if isinstance(sys_after, str):
            sys_after = [sys_after]
        for after in sys_after:
            command.extend(["--after=%s" % after])
    if sysconf.get("wants") is not None:
        sys_wants = sysconf["wants"]
        if isinstance(sys_wants, str):
            sys_wants = [sys_wants]
        for want in sys_wants:
            command.extend(["--wants=%s" % want])
    if sysconf.get("requires") is not None:
        sys_req = sysconf["requires"]
        if isinstance(sys_req, str):
            sys_req = [sys_req]
        for require in sys_req:
            command.extend(["--requires=%s" % require])
    for param in ["after", "wants", "requires"]:
        if sysconf.get(param) is not None and not gt4ver:
            module.fail_json(
                msg="Systemd parameter '%s' is supported from "
                "podman version 4 only! Current version is %s" % (param, version)
            )

    if module.params["debug"] or module_params["debug"]:
        module.log("PODMAN-CONTAINER-DEBUG: systemd command: %s" % " ".join(command))
    rc, systemd, err = module.run_command(command)
    return rc, systemd, err


def compare_systemd_file_content(file_path, file_content):
    if not os.path.exists(file_path):
        # File does not exist, so all lines in file_content are different
        return "", file_content
    # Read the file
    with open(file_path, "r") as unit_file:
        current_unit_file_content = unit_file.read()

    # Function to remove comments from file content
    def remove_comments(content):
        return "\n".join([line for line in content.splitlines() if not line.startswith("#")])

    # Remove comments from both file contents before comparison
    current_unit_file_content_nocmnt = remove_comments(current_unit_file_content)
    unit_content_nocmnt = remove_comments(file_content)
    if current_unit_file_content_nocmnt == unit_content_nocmnt:
        return None

    # Get the different lines between the two contents
    diff_in_file = [
        line for line in unit_content_nocmnt.splitlines() if line not in current_unit_file_content_nocmnt.splitlines()
    ]
    diff_in_string = [
        line for line in current_unit_file_content_nocmnt.splitlines() if line not in unit_content_nocmnt.splitlines()
    ]

    return diff_in_string, diff_in_file


def generate_systemd(module, module_params, name, version):
    result = {
        "changed": False,
        "systemd": {},
        "diff": {},
    }
    sysconf = module_params["generate_systemd"]
    rc, systemd, err = run_generate_systemd_command(module, module_params, name, version)
    if rc != 0:
        module.log("PODMAN-CONTAINER-DEBUG: Error generating systemd: %s" % err)
        if sysconf:
            module.fail_json(msg="Error generating systemd: %s" % err)
        return result
    else:
        try:
            data = json.loads(systemd)
            result["systemd"] = data
            if sysconf.get("path"):
                full_path = os.path.expanduser(sysconf["path"])
                if not os.path.exists(full_path):
                    os.makedirs(full_path)
                    result["changed"] = True
                if not os.path.isdir(full_path):
                    module.fail_json(
                        "Path %s is not a directory! " "Can not save systemd unit files there!" % full_path
                    )
                for file_name, file_content in data.items():
                    file_name += ".service"
                    if not os.path.exists(os.path.join(full_path, file_name)):
                        result["changed"] = True
                        if result["diff"].get("before") is None:
                            result["diff"] = {"before": {}, "after": {}}
                        result["diff"]["before"].update({"systemd_{file_name}.service".format(file_name=file_name): ""})
                        result["diff"]["after"].update(
                            {"systemd_{file_name}.service".format(file_name=file_name): file_content}
                        )

                    else:
                        diff_ = compare_systemd_file_content(os.path.join(full_path, file_name), file_content)
                        if diff_:
                            result["changed"] = True
                            if result["diff"].get("before") is None:
                                result["diff"] = {"before": {}, "after": {}}
                            result["diff"]["before"].update(
                                {"systemd_{file_name}.service".format(file_name=file_name): "\n".join(diff_[0])}
                            )
                            result["diff"]["after"].update(
                                {"systemd_{file_name}.service".format(file_name=file_name): "\n".join(diff_[1])}
                            )
                    with open(os.path.join(full_path, file_name), "w") as f:
                        f.write(file_content)
                diff_before = "\n".join(
                    [
                        "{j} - {k}".format(j=j, k=k)
                        for j, k in result["diff"].get("before", {}).items()
                        if "PIDFile" not in k
                    ]
                ).strip()
                diff_after = "\n".join(
                    [
                        "{j} - {k}".format(j=j, k=k)
                        for j, k in result["diff"].get("after", {}).items()
                        if "PIDFile" not in k
                    ]
                ).strip()
                if diff_before or diff_after:
                    result["diff"]["before"] = diff_before + "\n"
                    result["diff"]["after"] = diff_after + "\n"
                else:
                    result["diff"] = {}
            return result
        except Exception as e:
            module.log("PODMAN-CONTAINER-DEBUG: Error writing systemd: %s" % e)
            if sysconf:
                module.fail_json(msg="Error writing systemd: %s" % e)
            return result


def delete_systemd(module, module_params, name, version):
    sysconf = module_params["generate_systemd"]
    if not sysconf.get("path"):
        # We don't know where systemd files are located, nothing to delete
        module.log("PODMAN-CONTAINER-DEBUG: Not deleting systemd file - no path!")
        return
    rc, systemd, err = run_generate_systemd_command(module, module_params, name, version)
    if rc != 0:
        module.log("PODMAN-CONTAINER-DEBUG: Error generating systemd: %s" % err)
        return
    else:
        try:
            data = json.loads(systemd)
            for file_name in data.keys():
                file_name += ".service"
                full_dir_path = os.path.expanduser(sysconf["path"])
                file_path = os.path.join(full_dir_path, file_name)
                if os.path.exists(file_path):
                    os.unlink(file_path)
            return
        except Exception as e:
            module.log("PODMAN-CONTAINER-DEBUG: Error deleting systemd: %s" % e)
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
    "XFSZ": 25,
}

for i in range(1, _signal_map["RTMAX"] - _signal_map["RTMIN"] + 1):
    _signal_map["RTMIN+{0}".format(i)] = _signal_map["RTMIN"] + i
    _signal_map["RTMAX-{0}".format(i)] = _signal_map["RTMAX"] - i


def normalize_signal(signal_name_or_number):
    signal_name_or_number = str(signal_name_or_number)
    if signal_name_or_number.isdigit():
        return signal_name_or_number
    else:
        signal_name = signal_name_or_number.upper()
        if signal_name.startswith("SIG"):
            signal_name = signal_name[3:]
        if signal_name not in _signal_map:
            raise RuntimeError("Unknown signal '{0}'".format(signal_name_or_number))
        return str(_signal_map[signal_name])


def get_podman_version(module, fail=True):
    executable = module.params["executable"] if module.params["executable"] else "podman"
    rc, out, err = module.run_command([executable, b"--version"])
    if rc != 0 or not out or "version" not in out:
        if fail:
            module.fail_json(msg="'%s --version' run failed! Error: %s" % (executable, err))
        return None
    return out.split("version")[1].strip()


def createcommand(argument, info_config, boolean_type=False):
    """Returns list of values for given argument from CreateCommand
    from Podman container inspect output.

    Args:
        argument (str): argument name
        info_config (dict): dictionary with container info
        boolean_type (bool): if True, then argument is boolean type

    Returns:

        all_values: list of values for given argument from createcommand
    """
    if "createcommand" not in info_config:
        return []
    cr_com = info_config["createcommand"]
    argument_values = ARGUMENTS_OPTS_DICT.get(argument, [argument])
    all_values = []
    # Remove command args from the list
    container_cmd = info_config.get("cmd")
    if container_cmd and container_cmd == cr_com[-len(container_cmd):]:
        cr_com = cr_com[:-len(container_cmd)]
    for arg in argument_values:
        for ind, cr_opt in enumerate(cr_com):
            if arg == cr_opt:
                if boolean_type:
                    # This is a boolean argument and doesn't have value
                    return [True]
                if not cr_com[ind + 1].startswith("-"):
                    # This is a key=value argument
                    all_values.append(cr_com[ind + 1])
                else:
                    # This is also a false/true switching argument
                    return [True]
            if cr_opt.startswith("%s=" % arg):
                all_values.append(cr_opt.split("=", 1)[1])
    return all_values


def diff_generic(params, info_config, module_arg, cmd_arg, boolean_type=False):
    """
    Generic diff function for module arguments from CreateCommand
    in Podman inspection output.

    Args:
        params (dict): module parameters
        info_config (dict): dictionary with container info
        module_arg (str): module argument name
        cmd_arg (str): command line argument name
        boolean_type (bool): if True, then argument is boolean type

    Returns:
        bool: True if there is a difference, False otherwise

    """
    before = createcommand(cmd_arg, info_config, boolean_type=boolean_type)
    if before == []:
        before = None
    after = params[module_arg]
    if boolean_type and (before, after) in [(None, False), (False, None)]:
        before, after = False, False
        return before, after
    if before is None and after is None:
        return before, after
    if after is not None:
        if isinstance(after, list):
            after = ",".join(sorted([str(i).lower() for i in after]))
            if before:
                before = ",".join(sorted([str(i).lower() for i in before]))
            else:
                before = ""
        elif isinstance(after, dict):
            if module_arg == "log_opt" and "max_size" in after:
                after["max-size"] = after.pop("max_size")
            after = ",".join(sorted([str(k).lower() + "=" + str(v).lower() for k, v in after.items() if v is not None]))
            if before:
                before = ",".join(sorted([j.lower() for j in before]))
            else:
                before = ""
        elif isinstance(after, bool):
            after = str(after).capitalize()
            if before is not None:
                before = str(before[0]).capitalize()
        elif isinstance(after, int):
            after = str(after)
            if before is not None:
                before = str(before[0])
        else:
            before = before[0] if before else None
    else:
        before = ",".join(sorted(before)) if len(before) > 1 else before[0]
    return before, after
