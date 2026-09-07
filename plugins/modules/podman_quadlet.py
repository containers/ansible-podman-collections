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
  - Updates are handled by removing the existing quadlet and installing the new one.
  - Idempotency for ordinary local files and directories uses content comparison.
  - "For remote URLs, the module always reinstalls to ensure the host matches the configured source
    (reports changed=true)."
  - C(.quadlets) files are passed directly to Podman 6.0+ and always report C(changed=true).
    Generated units removed from a later version of the file must be removed explicitly with I(state=absent).
  - Directory installs on Podman 6.0+ support nested subdirectories.
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
      - If the name does not include the type suffix (e.g. C(.container)), the module will
        attempt to find a matching quadlet file.  When exactly one match is found it is used;
        when multiple suffixes match, all are removed.
    type: list
    elements: str
  src:
    description:
      - Path to a quadlet file, a directory containing a quadlet application, or a URL to install when I(state=present).
      - Except for C(.quadlets), local files and directories provide idempotency through content comparison.
      - For remote URLs, the module always installs fresh and reports C(changed=true) since content cannot be verified.
      - Directory installs on Podman 6.0+ support nested subdirectories.
      - Directory installs on Podman < 6.0 require a flat directory (no subdirectories).
    type: str
  files:
    description:
      - Additional non-quadlet files or URLs to install along with the primary I(src) (quadlet application use-case).
      - Passed positionally to C(podman quadlet install) after I(src) when supported.
      - On Podman 6.0 or later, local non-quadlet files require a directory I(src). The module fails with
        an explanatory message when they are supplied with a file or URL I(src).
      - Content changes to local files are detected. Previously installed files that are later omitted from
        this option must be removed explicitly with I(state=absent).
      - If any file is a URL, the entire install always reports C(changed=true) since remote content cannot be verified.
    type: list
    elements: str
  quadlet_dir:
    description:
      - Override the target quadlet directory used for idempotency checks.
      - By default it follows Podman defaults.
      - C(/etc/containers/systemd/) for root, C(~/.config/containers/systemd/) for non-root.
      - Note this is used for content comparison only and is not passed to Podman.
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
      - Extra global arguments to pass to the C(podman) command (e.g., C(--log-level=debug)).
      - These are placed after the executable and before the subcommand.
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
_debug_spec:
  description: Internal specification used for idempotency detection
  returned: when debug=true and state=present
  type: dict
  contains:
    mode:
      description: Install mode (dir_app, quadlets_file, single_file, or remote)
      type: str
    marker_name:
      description: Podman tracking filename, when applicable
      type: str
    desired_files:
      description: List of filenames that should be installed
      type: list
    removal_target:
      description: What will be passed to 'podman quadlet rm' for updates
      type: str
_debug_installed_files:
  description: List of currently installed files detected for content comparison
  returned: when debug=true and state=present and the source supports content comparison
  type: list
"""


EXAMPLES = r"""
- name: Install a simple quadlet file
  containers.podman.podman_quadlet:
    state: present
    src: /tmp/myapp.container

- name: Install a directory application with additional config files
  containers.podman.podman_quadlet:
    state: present
    src: /tmp/myapp_dir/
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

- name: Install quadlet from a URL (always reports changed=true)
  containers.podman.podman_quadlet:
    state: present
    src: https://example.com/myapp.container

- name: Install multi-quadlet application from .quadlets file (Podman 6.0+)
  containers.podman.podman_quadlet:
    state: present
    src: /tmp/webapp.quadlets
"""


import os  # noqa: E402
import json  # noqa: E402

from ansible.module_utils.basic import AnsibleModule  # noqa: E402

try:
    from ansible.module_utils.common.text.converters import to_native  # noqa: E402
except ImportError:
    from ansible.module_utils.common.text import to_native  # noqa: E402
from ..module_utils.podman.quadlet import (
    resolve_quadlet_dir,
    QUADLET_SUFFIXES,
)
from ..module_utils.podman.common import LooseVersion, get_podman_version

# Install modes
MODE_DIR_APP = "dir_app"
MODE_QUADLETS_FILE = "quadlets_file"
MODE_SINGLE_FILE = "single_file"
MODE_REMOTE = "remote"


# ---------------------------------------------------------------------------
# Pure helper functions (no version dependency)
# ---------------------------------------------------------------------------


def _is_remote_ref(path):
    """Check if the path is a remote URL."""
    if path is None:
        return False
    path_lower = path.lower()
    return path_lower.startswith("http://") or path_lower.startswith("https://")


def _read_lines_if_exists(path):
    """Read lines from a file if it exists, returning a set of non-empty lines."""
    if not os.path.exists(path):
        return set()
    try:
        with open(path, "r", encoding="utf-8") as f:
            return {line.strip() for line in f if line.strip()}
    except (IOError, OSError):
        return set()


def _read_file_bytes(path):
    """Read file contents as bytes, return None if cannot read."""
    try:
        with open(path, "rb") as f:
            return f.read()
    except (IOError, OSError):
        return None


def _read_required_file_bytes(module, path, description):
    """Read a required input file or fail with an actionable message."""
    try:
        with open(path, "rb") as f:
            return f.read()
    except (IOError, OSError) as exc:
        module.fail_json(msg="Failed to read %s %s: %s" % (description, path, to_native(exc)))


def _asset_marker_name(quadlet_name):
    """Get the .asset marker filename for a single quadlet file."""
    return ".%s.asset" % quadlet_name


def _add_extra_files(module, extra_files, desired_files):
    """Add extra files to desired_files dict, validating they exist."""
    for f in extra_files:
        if not os.path.isfile(f):
            module.fail_json(msg="Extra file %s is not a file" % f)
        basename = os.path.basename(f)
        if basename in desired_files:
            module.fail_json(msg="Duplicate basename '%s' in files list" % basename)
        desired_files[basename] = _read_required_file_bytes(module, f, "extra file")


# ---------------------------------------------------------------------------
# Spec builder — describes what should be installed
# ---------------------------------------------------------------------------


def _build_desired_spec(module, src, extra_files, podman_v6=False):
    """Build a specification of what should be installed.

    Returns a dict with:
    - mode: one of MODE_DIR_APP, MODE_QUADLETS_FILE, MODE_SINGLE_FILE, MODE_REMOTE
    - marker_name: Podman tracking filename when applicable
    - desired_files: dict of {installed_filename: bytes} for local sources
    - removal_target: what to pass to 'podman quadlet rm' for updates
    """
    extra_files = extra_files or []

    # Remote reference?
    if _is_remote_ref(src):
        return {"mode": MODE_REMOTE, "marker_name": None, "desired_files": {}, "removal_target": None}
    for f in extra_files:
        if _is_remote_ref(f):
            return {"mode": MODE_REMOTE, "marker_name": None, "desired_files": {}, "removal_target": None}

    if not os.path.exists(src):
        module.fail_json(msg="Source file or directory %s does not exist" % src)

    desired_files = {}

    # --- Directory source (app install) ---
    if os.path.isdir(src):
        basename = os.path.basename(src.rstrip("/"))
        marker_name = ".%s.app" % basename

        if podman_v6:
            # v6 supports nested directories via findNestedQuadlets
            def fail_walk(exc):
                module.fail_json(msg="Failed to read source directory %s: %s" % (src, to_native(exc)))

            for dirpath, _dirnames, filenames in os.walk(src, onerror=fail_walk):
                for fname in filenames:
                    full_path = os.path.join(dirpath, fname)
                    rel_path = os.path.relpath(full_path, src)
                    desired_files[rel_path] = _read_required_file_bytes(module, full_path, "source file")
        else:
            # v5: flat directory only — reject subdirectories
            try:
                entries = os.listdir(src)
            except (IOError, OSError) as exc:
                module.fail_json(msg="Failed to read source directory %s: %s" % (src, to_native(exc)))
            for entry in entries:
                full_path = os.path.join(src, entry)
                if os.path.isdir(full_path):
                    module.fail_json(
                        msg="Directory %s contains subdirectory '%s'. "
                        "Podman < 6.0 does not support nested directories in "
                        "quadlet application installs." % (src, entry)
                    )
                if os.path.isfile(full_path):
                    desired_files[entry] = _read_required_file_bytes(module, full_path, "source file")

        _add_extra_files(module, extra_files, desired_files)
        return {
            "mode": MODE_DIR_APP,
            "marker_name": marker_name,
            "desired_files": desired_files,
            "removal_target": basename,
        }

    # --- File source ---
    elif os.path.isfile(src):
        basename = os.path.basename(src)

        # .quadlets multi-section file (Podman 6.0+ only)
        if src.endswith(".quadlets"):
            if not podman_v6:
                module.fail_json(msg=".quadlets files require Podman 6.0 or later")
            _read_required_file_bytes(module, src, "source file")
            return {
                "mode": MODE_QUADLETS_FILE,
                "marker_name": None,
                "desired_files": {},
                "removal_target": None,
            }

        # Single quadlet file
        else:
            desired_files[basename] = _read_required_file_bytes(module, src, "source file")
            _add_extra_files(module, extra_files, desired_files)

            marker = _asset_marker_name(basename) if extra_files and not podman_v6 else None
            return {
                "mode": MODE_SINGLE_FILE,
                "marker_name": marker,
                "desired_files": desired_files,
                "removal_target": basename,
            }
    else:
        module.fail_json(msg="Source %s is not a file or directory" % src)


# ---------------------------------------------------------------------------
# PodmanQuadletManager — orchestrates install / absent
# ---------------------------------------------------------------------------


class PodmanQuadletManager:
    def __init__(self, module):
        self.module = module
        self.version = get_podman_version(module, fail=False)
        self.podman_v6 = self.version is not None and LooseVersion(self.version) >= LooseVersion("6.0.0")
        self.results = {
            "changed": False,
            "actions": [],
            "podman_actions": [],
            "quadlets": [],
        }
        self.executable = module.get_bin_path(module.params["executable"], required=True)
        self.quadlet_dir = resolve_quadlet_dir(module)

    # -------------------------------------------------------------------
    # Command builders
    # -------------------------------------------------------------------

    def _build_base_cmd(self):
        cmd = [self.executable]
        if self.module.params.get("cmd_args"):
            cmd.extend(self.module.params["cmd_args"])
        return cmd

    def _build_install_cmd(self):
        cmd = self._build_base_cmd()
        cmd.extend(["quadlet", "install"])
        if self.module.params["reload_systemd"]:
            cmd.append("--reload-systemd")
        else:
            cmd.append("--reload-systemd=false")
        src = self.module.params["src"]
        if os.path.isdir(src) and self.podman_v6:
            app_name = os.path.basename(src.rstrip("/"))
            cmd.extend(["--application", app_name])
        elif self.podman_v6 and src.endswith(".quadlets"):
            cmd.append("--replace")
        cmd.append(src)
        if self.module.params.get("files"):
            cmd.extend(self.module.params["files"])
        return cmd

    def _validate_install_layout(self, src, files):
        """Reject file layouts unsupported by the selected Podman version."""
        if not self.podman_v6 or os.path.isdir(src):
            return
        unsupported = [
            path
            for path in files
            if not _is_remote_ref(path) and not any(path.endswith(suffix) for suffix in QUADLET_SUFFIXES)
        ]
        if unsupported:
            self.module.fail_json(
                msg=(
                    "Podman 6 does not support local non-Quadlet files with a file or URL src: %s. "
                    "Use a directory as src so Podman can install the files as an application." % ", ".join(unsupported)
                )
            )

    def _build_rm_cmd(self, names=None, recursive=False):
        cmd = self._build_base_cmd()
        cmd.extend(["quadlet", "rm"])
        if self.module.params["reload_systemd"]:
            cmd.append("--reload-systemd")
        else:
            cmd.append("--reload-systemd=false")
        if self.module.params.get("force"):
            cmd.append("--force")
        if recursive:
            cmd.append("--recursive")
        if self.module.params.get("all"):
            cmd.append("--all")
        if names:
            cmd.extend(names)
        return cmd

    def _build_list_cmd(self):
        cmd = self._build_base_cmd()
        cmd.extend(["quadlet", "list", "--format", "json"])
        return cmd

    # -------------------------------------------------------------------
    # Command runners
    # -------------------------------------------------------------------

    def _run(self, cmd, record=True):
        """Run a command and optionally record it."""
        self.module.log("PODMAN-QUADLET-DEBUG: %s" % " ".join([to_native(i) for i in cmd]))
        if record:
            self.results["podman_actions"].append(" ".join([to_native(i) for i in cmd]))
        if self.module.check_mode:
            return 0, "", ""
        return self.module.run_command(cmd)

    def _run_rm_safe(self, cmd, context_msg):
        """Run a rm command, tolerating 'does not exist' errors.

        Returns (rc, out, err).  On non-zero rc, if the error is NOT a
        'does not exist' message, the module is failed with context_msg.
        """
        rc, out, err = self._run(cmd)
        if rc != 0:
            err_lower = err.lower()
            if "does not exist" not in err_lower and "no such" not in err_lower:
                self.module.fail_json(
                    msg="%s: %s" % (context_msg, err),
                    stdout=out,
                    stderr=err,
                    **self.results,
                )
        return rc, out, err

    # -------------------------------------------------------------------
    # Installed-file detection — v5 / v6 dispatch
    # -------------------------------------------------------------------

    def _get_installed_files(self, spec):
        """Return the set of filenames currently installed for this spec."""
        mode = spec["mode"]
        if mode == MODE_REMOTE:
            return set()
        if mode == MODE_DIR_APP:
            return (
                self._get_installed_files_dir_app_v6(spec) if self.podman_v6 else self._get_installed_files_marker(spec)
            )
        if mode == MODE_QUADLETS_FILE:
            return set()
        if mode == MODE_SINGLE_FILE:
            return self._get_installed_files_single(spec)
        return set()

    def _get_installed_files_marker(self, spec):
        """v5: read the .app marker file written by podman."""
        marker_path = os.path.join(self.quadlet_dir, spec["marker_name"])
        return _read_lines_if_exists(marker_path)

    def _get_installed_files_dir_app_v6(self, spec):
        """v6 DIR_APP: list files in the application subdirectory."""
        app_dir = os.path.join(self.quadlet_dir, spec["removal_target"])
        if not os.path.isdir(app_dir):
            return set()
        installed = set()
        for dirpath, _dirnames, filenames in os.walk(app_dir):
            for fname in filenames:
                full = os.path.join(dirpath, fname)
                installed.add(os.path.relpath(full, app_dir))
        return installed

    def _get_installed_files_single(self, spec):
        """Return installed files for a single-file invocation."""
        if self.podman_v6:
            return {name for name in spec["desired_files"] if os.path.exists(os.path.join(self.quadlet_dir, name))}

        installed = set()
        primary_name = spec["removal_target"]
        if os.path.exists(os.path.join(self.quadlet_dir, primary_name)):
            installed.add(primary_name)
        marker_path = os.path.join(self.quadlet_dir, _asset_marker_name(primary_name))
        installed.update(_read_lines_if_exists(marker_path))
        return installed

    # -------------------------------------------------------------------
    # Content directory — where installed files live
    # -------------------------------------------------------------------

    def _content_dir(self, spec):
        """Return the directory where installed content files are located."""
        if self.podman_v6 and spec["mode"] == MODE_DIR_APP:
            return os.path.join(self.quadlet_dir, spec["removal_target"])
        return self.quadlet_dir

    # -------------------------------------------------------------------
    # Change detection
    # -------------------------------------------------------------------

    def _needs_change(self, spec):
        """Determine if installation/update is needed."""
        if spec["mode"] in (MODE_REMOTE, MODE_QUADLETS_FILE):
            return True

        desired_set = set(spec["desired_files"].keys())
        installed_set = self._get_installed_files(spec)
        if desired_set != installed_set:
            return True

        content_dir = self._content_dir(spec)
        for filename, desired_content in spec["desired_files"].items():
            installed_path = os.path.join(content_dir, filename)
            installed_content = _read_file_bytes(installed_path)
            if installed_content is None or installed_content != desired_content:
                return True
        return False

    # -------------------------------------------------------------------
    # Pre-install removal
    # -------------------------------------------------------------------

    def _remove_for_update(self, spec):
        """Remove existing quadlet(s) before reinstalling with new content."""
        removal_target = spec["removal_target"]
        if not removal_target:
            return

        mode = spec["mode"]

        # --- DIR_APP ---
        if mode == MODE_DIR_APP:
            if self.podman_v6:
                app_dir = os.path.join(self.quadlet_dir, removal_target)
                if not os.path.isdir(app_dir):
                    return
                self._run_rm_safe(
                    self._build_rm_cmd([removal_target], recursive=True),
                    "Failed to remove existing app for update",
                )
            else:
                marker = os.path.join(self.quadlet_dir, spec["marker_name"])
                app_dir = os.path.join(self.quadlet_dir, removal_target)
                if not os.path.exists(marker) and not os.path.isdir(app_dir):
                    return
                # v5 requires the .app marker name for removal
                self._run_rm_safe(
                    self._build_rm_cmd([spec["marker_name"]]),
                    "Failed to remove existing app for update",
                )
            self.results["actions"].append("removed existing quadlet %s for update" % removal_target)
            return

        # --- SINGLE_FILE ---
        if mode == MODE_SINGLE_FILE:
            installed = self._get_installed_files(spec)
            if not installed:
                return
            removal_names = (
                sorted(name for name in installed if any(name.endswith(suffix) for suffix in QUADLET_SUFFIXES))
                if self.podman_v6
                else [removal_target]
            )
            self._run_rm_safe(
                self._build_rm_cmd(removal_names),
                "Failed to remove existing quadlet for update",
            )
            self.results["actions"].append("removed existing quadlet %s for update" % removal_target)

    # -------------------------------------------------------------------
    # Installed quadlet listing (for absent state)
    # -------------------------------------------------------------------

    def _get_installed_quadlets(self):
        """Get set of installed quadlet names (read-only, runs in check_mode)."""
        cmd = self._build_list_cmd()
        self.module.log("PODMAN-QUADLET-DEBUG: %s" % " ".join([to_native(i) for i in cmd]))
        rc, out, err = self.module.run_command(cmd)
        if rc != 0:
            self.module.fail_json(
                msg="Failed to list quadlets: %s" % err,
                stdout=out,
                stderr=err,
                **self.results,
            )
        try:
            quadlets = json.loads(out) if out.strip() else []
        except json.JSONDecodeError as e:
            self.module.fail_json(
                msg="Failed to parse quadlet list output: %s" % str(e),
                stdout=out,
                stderr=err,
                **self.results,
            )
        return {name for name in (q.get("Name") for q in quadlets) if name}

    # -------------------------------------------------------------------
    # state=present
    # -------------------------------------------------------------------

    def _install(self):
        src = self.module.params["src"]
        extra_files = self.module.params.get("files") or []

        self._validate_install_layout(src, extra_files)
        spec = _build_desired_spec(self.module, src, extra_files, self.podman_v6)

        if self.module.params["debug"]:
            self.results["_debug_spec"] = {
                "mode": spec["mode"],
                "marker_name": spec["marker_name"],
                "desired_files": list(spec["desired_files"].keys()),
                "removal_target": spec["removal_target"],
            }
            if spec["mode"] not in (MODE_REMOTE, MODE_QUADLETS_FILE):
                self.results["_debug_installed_files"] = list(self._get_installed_files(spec))

        if not self._needs_change(spec):
            return

        # --- Remote source ---
        if spec["mode"] == MODE_REMOTE:
            cmd = self._build_install_cmd()
            rc, out, err = self._run(cmd)
            if rc != 0:
                err_lower = err.lower()
                if "already exists" in err_lower or "refusing to overwrite" in err_lower:
                    quadlet_name = os.path.basename(src)
                    self._run_rm_safe(
                        self._build_rm_cmd([quadlet_name]),
                        "Failed to remove existing quadlet for remote reinstall",
                    )
                    self.results["actions"].append("removed existing quadlet for reinstall from remote")
                    cmd = self._build_install_cmd()
                    rc, out, err = self._run(cmd)
                    if rc != 0:
                        self.module.fail_json(
                            msg="Failed to install quadlet(s) from remote: %s" % err,
                            stdout=out,
                            stderr=err,
                            **self.results,
                        )
                else:
                    self.module.fail_json(
                        msg="Failed to install quadlet(s): %s" % err,
                        stdout=out,
                        stderr=err,
                        **self.results,
                    )
            self.results["changed"] = True
            self.results["actions"].append("installed quadlets from %s" % src)
            self.results["quadlets"].append({"source": src, "path": self.quadlet_dir})
            if self.module.params["debug"]:
                self.results.update({"stdout": out, "stderr": err})
            return

        # --- Local source with changes ---
        self._remove_for_update(spec)

        cmd = self._build_install_cmd()
        rc, out, err = self._run(cmd)
        if rc != 0:
            self.module.fail_json(
                msg="Failed to install quadlet(s): %s" % err,
                stdout=out,
                stderr=err,
                **self.results,
            )

        self.results["changed"] = True
        self.results["actions"].append("installed quadlets from %s" % src)
        self.results["quadlets"].append({"source": src, "path": self.quadlet_dir})
        if self.module.params["debug"]:
            self.results.update({"stdout": out, "stderr": err})

    # -------------------------------------------------------------------
    # state=absent
    # -------------------------------------------------------------------

    def _absent(self):
        names = self.module.params.get("name") or []
        resolved_names = []

        if not self.module.params.get("all") and names:
            installed = self._get_installed_quadlets()
            app_names = []
            for name in names:
                if name in installed and name not in resolved_names:
                    resolved_names.append(name)
                    continue
                found_suffix = False
                for suffix in QUADLET_SUFFIXES:
                    resolved = name + suffix
                    if resolved in installed and resolved not in resolved_names:
                        resolved_names.append(resolved)
                        found_suffix = True
                if found_suffix:
                    continue
                # On v6, check if it's an application directory name
                if self.podman_v6:
                    app_dir = os.path.join(self.quadlet_dir, name)
                    if os.path.isdir(app_dir):
                        app_names.append(name)

            if not resolved_names and not app_names:
                return

            # Remove app directories first via --recursive
            if app_names:
                app_cmd = self._build_rm_cmd(app_names, recursive=True)
                self._run_rm_safe(
                    app_cmd,
                    "Failed to remove application(s) %s" % ", ".join(app_names),
                )
                self.results["changed"] = True
                for aname in app_names:
                    self.results["actions"].append("removed application %s" % aname)
                    self.results["quadlets"].append({"name": aname, "path": self.quadlet_dir})

            if not resolved_names:
                if self.module.params["debug"]:
                    self.results.update({"stdout": "", "stderr": ""})
                return

        if self.module.params.get("all"):
            cmd = self._build_rm_cmd(recursive=self.podman_v6)
        elif self.podman_v6:
            cmd = self._build_rm_cmd(resolved_names, recursive=True)
        else:
            cmd = self._build_rm_cmd(resolved_names)

        rc, out, err = self._run(cmd)
        if rc != 0:
            err_lower = err.lower()
            if "does not exist" in err_lower or "no such" in err_lower:
                return
            if self.module.params.get("all"):
                msg = "Failed to remove all quadlets: %s" % err
            else:
                msg = "Failed to remove quadlet(s) %s: %s" % (", ".join(resolved_names), err)
            self.module.fail_json(msg=msg, stdout=out, stderr=err, **self.results)

        self.results["changed"] = True

        if self.module.params.get("all"):
            self.results["actions"].append("removed all quadlets")
            self.results["quadlets"].append({"name": "all", "path": self.quadlet_dir})
        else:
            self.results["actions"].append("removed %s" % ", ".join(resolved_names))
            for name in resolved_names:
                self.results["quadlets"].append({"name": name, "path": self.quadlet_dir})

        if self.module.params["debug"]:
            self.results.update({"stdout": out, "stderr": err})

    # -------------------------------------------------------------------
    # Entry point
    # -------------------------------------------------------------------

    def execute(self):
        state = self.module.params["state"]
        if state == "present":
            self._install()
        elif state == "absent":
            self._absent()
        self.module.exit_json(**self.results)


def _validate_state_params(module):
    """Reject parameters that do not apply to the requested state."""
    state = module.params["state"]
    if state == "present":
        invalid = []
        if module.params.get("name") is not None:
            invalid.append("name")
        if module.params.get("all"):
            invalid.append("all")
        if invalid:
            module.fail_json(msg="The following options are not valid with state='present': %s" % ", ".join(invalid))
        return

    invalid = [name for name in ("src", "files") if module.params.get(name) is not None]
    if invalid:
        module.fail_json(msg="The following options are not valid with state='absent': %s" % ", ".join(invalid))
    if not module.params["name"] and not module.params["all"]:
        module.fail_json(msg="For state='absent', either 'name' or 'all' must be specified.")


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(type="str", default="present", choices=["present", "absent"]),
            name=dict(type="list", elements="str", required=False),
            src=dict(type="str", required=False),
            files=dict(type="list", elements="str", required=False),
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

    _validate_state_params(module)
    PodmanQuadletManager(module).execute()


if __name__ == "__main__":
    main()
