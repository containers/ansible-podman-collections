#!/usr/bin/python
# Copyright (c) 2025 Red Hat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# flake8: noqa: E501
from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
module: podman_quadlet
author:
  - "Sagi Shnaidman (@sshnaidm)"
short_description: Install or remove Podman Quadlets
description:
  - Install or remove Podman Quadlets using C(podman quadlet install) and C(podman quadlet rm).
  - Creation of quadlet files is handled by resource modules with I(state=quadlet).
requirements:
  - podman
options:
  state:
    description:
      - Desired state of quadlet(s).
    type: str
    default: present
    choices:
      - present
      - absent
  name:
    description:
      - Name (filename without path) of an installed quadlet to remove when I(state=absent).
      - If the name does not include the type suffix (e.g. C(.container)), the module will attempt to find a matching quadlet file in I(quadlet_dir).
    type: list
    elements: str
  src:
    description:
      - Path to a quadlet file or a directory containing a quadlet application to install when I(state=present).
    type: path
  files:
    description:
      - Additional non-quadlet files or URLs to install along with the primary I(src) (quadlet application use-case).
      - Passed positionally to C(podman quadlet install) after I(src).
    type: list
    elements: path
  quadlet_dir:
    description:
      - Override the target quadlet directory. By default it follows Podman defaults.
      - C(/etc/containers/systemd/) for root, C(~/.config/containers/systemd/) for non-root.
    type: path
  reload_systemd:
    description:
      - Control systemd reload behavior in Podman. When true, pass C(--reload-systemd).
      - When false, pass C(--reload-systemd=false).
    type: bool
    default: true
  force:
    description:
      - Force removal when I(state=absent) (maps to C(podman quadlet rm --force)).
    type: bool
    default: true

  all:
    description:
      - Remove all installed quadlets when I(state=absent) (maps to C(podman quadlet rm --all)).
    type: bool
    default: false
  executable:
    description:
      - Path to C(podman) executable if it is not in the C($PATH) on the machine running C(podman)
    default: 'podman'
    type: str
  cmd_args:
    description:
      - Extra arguments to pass to the C(podman) command (e.g., C(--log-level=debug)).
    type: list
    elements: str
  debug:
    description:
      - Return additional information which can be helpful for investigations.
    type: bool
    default: false
"""


RETURN = r"""
changed:
  description: Whether any change was made
  returned: always
  type: bool
actions:
  description: Human-readable actions performed
  returned: always
  type: list
podman_actions:
  description: Executed podman command lines
  returned: always
  type: list
quadlets:
  description: List of affected quadlets with name, path, and scope
  returned: always
  type: list
stdout:
  description: podman stdout
  returned: when debug=true
  type: str
stderr:
  description: podman stderr
  returned: when debug=true
  type: str
"""


EXAMPLES = r"""
- name: Install a simple quadlet file
  containers.podman.podman_quadlet:
    state: present
    src: /tmp/myapp.container

- name: Install a quadlet application with additional config files
  containers.podman.podman_quadlet:
    state: present
    src: /tmp/myapp.container
    files:
      - /tmp/myapp.conf
      - /tmp/secrets.env

- name: Install quadlet application from a directory
  containers.podman.podman_quadlet:
    state: present
    src: /tmp/myapp_dir/

- name: Install with custom quadlet directory (e.g. for system-wide install)
  containers.podman.podman_quadlet:
    state: present
    src: /tmp/myapp.container
    quadlet_dir: /etc/containers/systemd
  become: true

- name: Remove a specific quadlet
  containers.podman.podman_quadlet:
    state: absent
    name:
      - myapp.container

- name: Remove multiple quadlets
  containers.podman.podman_quadlet:
    state: absent
    name:
      - myapp.container
      - database.container
      - cache.container

- name: Remove quadlet without suffix (module resolves to .container, .pod, etc.)
  containers.podman.podman_quadlet:
    state: absent
    name:
      - myapp

- name: Remove all quadlets (use with caution)
  containers.podman.podman_quadlet:
    state: absent
    all: true
"""


import os
import json

from ansible.module_utils.basic import AnsibleModule  # noqa: F402
from ansible.module_utils._text import to_native  # noqa: F402
from ..module_utils.podman.quadlet import (
    resolve_quadlet_dir,
    QUADLET_SUFFIXES,
)


def _build_quadlet_install_cmd(module):
    cmd = [module.params["executable"], "quadlet", "install"]
    if module.params.get("cmd_args"):
        cmd.extend(module.params["cmd_args"])
    if module.params["reload_systemd"]:
        cmd.append("--reload-systemd")
    else:
        cmd.append("--reload-systemd=false")
    cmd.append(module.params["src"])
    if module.params.get("files"):
        cmd.extend(module.params["files"])
    return cmd


def _build_quadlet_rm_cmd(module):
    cmd = [module.params["executable"], "quadlet", "rm"]
    if module.params.get("cmd_args"):
        cmd.extend(module.params["cmd_args"])
    if module.params["reload_systemd"]:
        cmd.append("--reload-systemd")
    else:
        cmd.append("--reload-systemd=false")
    if module.params.get("force"):
        cmd.append("--force")
    if module.params.get("all"):
        cmd.append("--all")
    return cmd


class PodmanQuadletManager:
    def __init__(self, module):
        self.module = module
        self.results = {
            "changed": False,
            "actions": [],
            "podman_actions": [],
            "quadlets": [],
        }
        self.executable = module.get_bin_path(module.params["executable"], required=True)
        self.quadlet_dir = resolve_quadlet_dir(module)

    def _run(self, cmd):
        self.module.log("PODMAN-QUADLET-DEBUG: %s" % " ".join([to_native(i) for i in cmd]))
        self.results["podman_actions"].append(" ".join([to_native(i) for i in cmd]))
        if self.module.check_mode:
            return 0, "", ""
        return self.module.run_command(cmd)

    def _install(self):
        src = self.module.params["src"]
        if not src:
            self.module.fail_json(msg="Parameter 'src' is required for state=present")

        # Improved idempotency check: use stat comparison first, then checksums
        will_change = False
        file_list = []
        if os.path.isdir(src):
            # Limit depth and filter file types for performance
            for root, _dirs, files in os.walk(src):
                # Limit to 3 levels deep to avoid excessive traversal
                if root.count(os.sep) - src.count(os.sep) >= 3:
                    continue
                for f in files:
                    # Only include likely quadlet files and configs
                    if f.endswith(tuple(QUADLET_SUFFIXES + [".conf", ".yaml", ".yml"])):
                        file_list.append(os.path.join(root, f))
        else:
            file_list = [src]

        for path in file_list:
            if os.path.isdir(path):
                continue
            target = os.path.join(self.quadlet_dir, os.path.basename(path))
            try:
                if not os.path.exists(target):
                    will_change = True
                    break

                src_stat = os.stat(path)
                target_stat = os.stat(target)

                # Check size and mtime
                if src_stat.st_size != target_stat.st_size or src_stat.st_mtime > target_stat.st_mtime:
                    will_change = True
                    break

                # If size matches and src is not newer, check content for small files
                if src_stat.st_size < 1024 * 1024:  # 1MB limit
                    with open(path, "rb") as sf:
                        sdata = sf.read()
                    with open(target, "rb") as tf:
                        tdata = tf.read()
                    if sdata != tdata:
                        will_change = True
                        break
            except Exception:
                # If any issue reading, assume change needed
                will_change = True
                break

        if not will_change:
            # Nothing to do
            return

        cmd = _build_quadlet_install_cmd(self.module)
        rc, out, err = self._run(cmd)
        if rc != 0:
            self.module.fail_json(msg="Failed to install quadlet(s): %s" % err, stdout=out, stderr=err, **self.results)

        self.results["changed"] = True
        self.results["actions"].append("installed quadlets from %s" % src)
        self.results["quadlets"].append({"source": src, "path": self.quadlet_dir})
        if self.module.params["debug"]:
            self.results.update({"stdout": out, "stderr": err})

    def _absent(self):
        if not (self.module.params.get("all") or self.module.params.get("name")):
            self.module.fail_json(msg="Provide 'name' or set 'all=true' for state=absent")

        cmd = _build_quadlet_rm_cmd(self.module)
        names = self.module.params.get("name") or []
        resolved_names = []

        # If not removing all, resolve names first to reduce command execution
        if not self.module.params.get("all") and names:
            # Pre-resolve names using quadlet list to avoid multiple rm attempts
            try:
                list_cmd = [self.module.params["executable"], "quadlet", "list", "--format", "json"]
                rc_list, out_list, err_list = self.module.run_command(list_cmd)
                if rc_list != 0:
                    self.module.fail_json(
                        msg="Failed to list quadlets for idempotency check: %s" % err_list,
                        stdout=out_list,
                        stderr=err_list,
                        **self.results
                    )
                installed_quadlets = json.loads(out_list) if out_list else []
                installed_names = {q.get("Name", q.get("name", "")) for q in installed_quadlets}
                for name in names:
                    if name in installed_names:
                        resolved_names.append(name)
                    else:
                        # Try with suffixes
                        for suffix in QUADLET_SUFFIXES:
                            if name + suffix in installed_names:
                                resolved_names.append(name + suffix)
                                break
                        else:
                            # If not found, it's already absent - idempotent
                            pass
            except json.JSONDecodeError as e:
                self.module.fail_json(msg="Failed to parse quadlet list output: %s" % str(e), **self.results)

            if not resolved_names:
                # All quadlets already absent, no change needed
                return

            cmd.extend(resolved_names)

        rc, out, err = self._run(cmd)

        # Handle errors
        if rc != 0:
            if self.module.params.get("all"):
                # For all=True, any failure is a real error
                self.module.fail_json(
                    msg="Failed to remove all quadlets: %s" % err, stdout=out, stderr=err, **self.results
                )
            else:
                # For specific names, check if it's a race condition (file already gone)
                if "no such file or directory" in err.lower() or "does not exist" in err.lower():
                    # Race condition: files were removed between list and rm
                    # Don't set changed=True since no actual change was made
                    return
                else:
                    # Real error
                    self.module.fail_json(
                        msg="Failed to remove quadlet(s): %s" % ", ".join(names), stdout=out, stderr=err, **self.results
                    )

        # Success - set changed and build return value
        self.results["changed"] = True

        if self.module.params.get("all"):
            self.results["actions"].append("removed all quadlets")
            self.results["quadlets"].append({"name": "all", "path": self.quadlet_dir})
        else:
            # Return list of dicts for each removed quadlet
            self.results["actions"].append("removed %s" % ", ".join(resolved_names))
            for name in resolved_names:
                self.results["quadlets"].append({"name": name, "path": self.quadlet_dir})

        if self.module.params["debug"]:
            self.results.update({"stdout": out, "stderr": err})

    def execute(self):
        state = self.module.params["state"]
        if state == "present":
            self._install()
        elif state == "absent":
            self._absent()
        self.module.exit_json(**self.results)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(type="str", default="present", choices=["present", "absent"]),
            name=dict(type="list", elements="str", required=False),
            src=dict(type="path", required=False),
            files=dict(type="list", elements="path", required=False),
            quadlet_dir=dict(type="path", required=False),
            reload_systemd=dict(type="bool", default=True),
            force=dict(type="bool", default=True),
            all=dict(type="bool", default=False),
            executable=dict(type="str", default="podman"),
            cmd_args=dict(type="list", elements="str", required=False),
            debug=dict(type="bool", default=False),
        ),
        required_if=[
            ("state", "present", ["src"]),
        ],
        mutually_exclusive=[
            ["all", "name"],
        ],
        supports_check_mode=True,
    )

    # Custom validation for state=absent
    if module.params["state"] == "absent":
        if not module.params["name"] and not module.params["all"]:
            module.fail_json(msg="For state='absent', either 'name' or 'all' must be specified.")

    PodmanQuadletManager(module).execute()


if __name__ == "__main__":
    main()
