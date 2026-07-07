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
  - Idempotency for local sources uses content comparison and module-managed manifest files.
  - "For remote URLs, the module always reinstalls to ensure the host matches the configured source (reports changed=true)."
  - Supports C(.quadlets) files containing multiple quadlet sections separated by C(---) delimiter (requires Podman 6.0+).
  - Each section in a C(.quadlets) file must include a C(# FileName=<name>) comment to specify the output filename.
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
      - For local files and directories, full idempotency is provided (content comparison).
      - For remote URLs, the module always installs fresh and reports C(changed=true) since content cannot be verified.
      - Directory installs on Podman 6.0+ support nested subdirectories.
      - Directory installs on Podman < 6.0 require a flat directory (no subdirectories).
    type: str
  files:
    description:
      - Additional non-quadlet files or URLs to install along with the primary I(src) (quadlet application use-case).
      - Passed positionally to C(podman quadlet install) after I(src).
      - For local files, full idempotency is provided.
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
      description: Install mode (dir_app, quadlets_app, single_file, or remote)
      type: str
    marker_name:
      description: The manifest or marker filename used for tracking
      type: str
    desired_files:
      description: List of filenames that should be installed
      type: list
    removal_target:
      description: What will be passed to 'podman quadlet rm' for updates
      type: str
_debug_installed_files:
  description: List of currently installed files detected from manifests
  returned: when debug=true and state=present and mode is not remote
  type: list
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
MODE_QUADLETS_APP = "quadlets_app"
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
        with open(path, "r") as f:
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


def _asset_marker_name(quadlet_name):
    """Get the .asset marker filename for a single quadlet file."""
    return ".%s.asset" % quadlet_name


def _quadlets_manifest_name(quadlets_basename):
    """Get the .quadlets.manifest filename for a .quadlets install."""
    stem = os.path.splitext(quadlets_basename)[0]
    return ".%s.quadlets.manifest" % stem


def _add_extra_files(module, extra_files, desired_files):
    """Add extra files to desired_files dict, validating they exist."""
    for f in extra_files:
        if not os.path.isfile(f):
            module.fail_json(msg="Extra file %s is not a file" % f)
        basename = os.path.basename(f)
        if basename in desired_files:
            module.fail_json(msg="Duplicate basename '%s' in files list" % basename)
        content = _read_file_bytes(f)
        if content is not None:
            desired_files[basename] = content


def _parse_quadlets_file(path):
    """Parse a .quadlets file and return a dict of {filename: content}.

    Each section is separated by '---' and must have a '# FileName=<name>' comment.
    The extension is detected from the first recognized quadlet type header.
    Mirrors podman's strict parsing: fails on missing FileName, unrecognized
    type, or path separators in FileName.

    Returns dict on success, None on IO error, or a string error message.
    """
    try:
        with open(path, "r") as f:
            content = f.read()
    except (IOError, OSError):
        return None

    sections = []
    current_section = []

    for line in content.split("\n"):
        if line.strip() == "---":
            if current_section:
                sections.append("\n".join(current_section))
                current_section = []
        else:
            current_section.append(line)

    if current_section:
        sections.append("\n".join(current_section))

    result = {}
    for idx, section in enumerate(sections):
        section = section.strip()
        if not section:
            continue

        filename = None
        extension = None
        for line in section.split("\n"):
            line_stripped = line.strip()
            if line_stripped.startswith("#"):
                comment_content = line_stripped[1:].strip()
                if comment_content.startswith("FileName="):
                    filename = comment_content[9:].strip()
            elif line_stripped.startswith("[") and line_stripped.endswith("]") and extension is None:
                candidate = ".%s" % line_stripped[1:-1].lower()
                if candidate in QUADLET_SUFFIXES:
                    extension = candidate

        if not filename:
            return "section %d has no '# FileName=<name>' comment" % (idx + 1)
        if "/" in filename or "\\" in filename or filename in (".", ".."):
            return "section %d FileName '%s' contains path separators" % (idx + 1, filename)
        if not extension:
            return (
                "section %d (FileName=%s) has no recognized quadlet type "
                "(expected [Container], [Volume], etc.)" % (idx + 1, filename)
            )

        # Mirror podman: destName = section.name + section.extension
        full_filename = filename + extension
        result[full_filename] = section.encode("utf-8")

    return result


# ---------------------------------------------------------------------------
# Spec builder — describes what should be installed
# ---------------------------------------------------------------------------


def _build_desired_spec(module, src, extra_files, podman_v6=False):
    """Build a specification of what should be installed.

    Returns a dict with:
    - mode: one of MODE_DIR_APP, MODE_QUADLETS_APP, MODE_SINGLE_FILE, MODE_REMOTE
    - marker_name: the manifest/marker filename (None for remote)
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
            for dirpath, _dirnames, filenames in os.walk(src):
                for fname in filenames:
                    full_path = os.path.join(dirpath, fname)
                    rel_path = os.path.relpath(full_path, src)
                    content = _read_file_bytes(full_path)
                    if content is not None:
                        desired_files[rel_path] = content
        else:
            # v5: flat directory only — reject subdirectories
            for entry in os.listdir(src):
                full_path = os.path.join(src, entry)
                if os.path.isdir(full_path):
                    module.fail_json(
                        msg="Directory %s contains subdirectory '%s'. "
                        "Podman < 6.0 does not support nested directories in "
                        "quadlet application installs." % (src, entry)
                    )
                if os.path.isfile(full_path):
                    content = _read_file_bytes(full_path)
                    if content is not None:
                        desired_files[entry] = content

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
            version_str = get_podman_version(module, fail=False)
            if version_str and LooseVersion(version_str) < LooseVersion("6.0.0"):
                module.fail_json(msg=".quadlets files require Podman 6.0 or later (current: %s)" % version_str)

            parsed = _parse_quadlets_file(src)
            if parsed is None:
                module.fail_json(msg="Failed to read .quadlets file %s" % src)
            if isinstance(parsed, str):
                module.fail_json(msg="Invalid .quadlets file %s: %s" % (src, parsed))
            if not parsed:
                module.fail_json(msg=".quadlets file %s has no sections" % src)
            desired_files = parsed
            _add_extra_files(module, extra_files, desired_files)

            stem = os.path.splitext(basename)[0]
            manifest = _quadlets_manifest_name(basename)
            return {
                "mode": MODE_QUADLETS_APP,
                "marker_name": manifest,
                "desired_files": desired_files,
                "removal_target": stem,
            }

        # Single quadlet file
        else:
            content = _read_file_bytes(src)
            if content is not None:
                desired_files[basename] = content
            _add_extra_files(module, extra_files, desired_files)

            marker = _asset_marker_name(basename) if extra_files else None
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
        cmd.append(src)
        if self.module.params.get("files"):
            cmd.extend(self.module.params["files"])
        return cmd

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
        if mode == MODE_QUADLETS_APP:
            return (
                self._get_installed_files_quadlets_v6(spec)
                if self.podman_v6
                else self._get_installed_files_marker(spec)
            )
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

    def _get_installed_files_quadlets_v6(self, spec):
        """v6 QUADLETS_APP: read the module-managed .quadlets.manifest.

        Falls back to checking desired files on disk when no manifest
        exists (upgrade from older module version or manual install).
        """
        manifest_path = os.path.join(self.quadlet_dir, spec["marker_name"])
        from_manifest = _read_lines_if_exists(manifest_path)
        if from_manifest:
            return from_manifest
        return {name for name in spec["desired_files"] if os.path.exists(os.path.join(self.quadlet_dir, name))}

    def _get_installed_files_single(self, spec):
        """SINGLE_FILE: the primary quadlet file + contents of .asset marker."""
        installed = set()
        primary_name = None
        for name in spec["desired_files"]:
            for suffix in QUADLET_SUFFIXES:
                if name.endswith(suffix):
                    primary_name = name
                    if os.path.exists(os.path.join(self.quadlet_dir, name)):
                        installed.add(name)
                    break
        if primary_name:
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
        if spec["mode"] == MODE_REMOTE:
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

        # --- v6 QUADLETS_APP: flat files, remove individually ---
        if mode == MODE_QUADLETS_APP and self.podman_v6:
            installed = self._get_installed_files(spec)
            if not installed:
                return
            self._run_rm_safe(
                self._build_rm_cmd(sorted(installed)),
                "Failed to remove existing quadlets for update",
            )
            self.results["actions"].append("removed existing quadlets for update")
            return

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

        # --- QUADLETS_APP v5 ---
        if mode == MODE_QUADLETS_APP and not self.podman_v6:
            marker = os.path.join(self.quadlet_dir, spec["marker_name"])
            if not os.path.exists(marker):
                return
            self._run_rm_safe(
                self._build_rm_cmd([removal_target]),
                "Failed to remove existing quadlet for update",
            )
            self.results["actions"].append("removed existing quadlet %s for update" % removal_target)
            return

        # --- SINGLE_FILE ---
        if mode == MODE_SINGLE_FILE:
            quadlet_path = os.path.join(self.quadlet_dir, removal_target)
            if not os.path.exists(quadlet_path):
                return
            self._run_rm_safe(
                self._build_rm_cmd([removal_target]),
                "Failed to remove existing quadlet for update",
            )
            self.results["actions"].append("removed existing quadlet %s for update" % removal_target)
            # podman rm only removes unit files — clean up companions
            if not self.module.check_mode:
                installed = self._get_installed_files(spec)
                for fname in installed:
                    fpath = os.path.join(self.quadlet_dir, fname)
                    if os.path.exists(fpath) and not any(fname.endswith(s) for s in QUADLET_SUFFIXES):
                        os.remove(fpath)

    # -------------------------------------------------------------------
    # Post-install marker writing (check_mode guarded)
    # -------------------------------------------------------------------

    def _write_install_markers(self, spec, src, extra_files):
        """Write module-managed markers/manifests after a successful install."""
        if self.module.check_mode:
            return

        mode = spec["mode"]

        if mode == MODE_SINGLE_FILE and self.podman_v6:
            marker_name = _asset_marker_name(os.path.basename(src))
            marker_path = os.path.join(self.quadlet_dir, marker_name)
            if extra_files:
                all_names = [os.path.basename(src)] + [os.path.basename(f) for f in extra_files]
                with open(marker_path, "w") as f:
                    f.write("\n".join(all_names) + "\n")
            elif os.path.exists(marker_path):
                os.remove(marker_path)

        elif mode == MODE_QUADLETS_APP and self.podman_v6:
            manifest_name = spec["marker_name"]
            manifest_path = os.path.join(self.quadlet_dir, manifest_name)
            filenames = sorted(spec["desired_files"].keys())
            with open(manifest_path, "w") as f:
                f.write("\n".join(filenames) + "\n")

    # -------------------------------------------------------------------
    # Post-absent cleanup (check_mode guarded)
    # -------------------------------------------------------------------

    def _cleanup_after_absent(self, names):
        """Remove companion files and module-managed markers after absent."""
        if self.module.check_mode:
            return
        if not os.path.isdir(self.quadlet_dir):
            return
        for name in names:
            # Remove .asset marker and its listed companions
            asset_path = os.path.join(self.quadlet_dir, _asset_marker_name(name))
            if os.path.exists(asset_path):
                companions = _read_lines_if_exists(asset_path)
                for comp in companions:
                    comp_path = os.path.join(self.quadlet_dir, comp)
                    if os.path.exists(comp_path) and comp != name:
                        os.remove(comp_path)
                os.remove(asset_path)
            # Scan .quadlets.manifest files — if any manifest lists
            # this name, remove all sibling quadlets via podman and
            # clean up the manifest.
            for entry in os.listdir(self.quadlet_dir):
                if not entry.endswith(".quadlets.manifest"):
                    continue
                manifest_path = os.path.join(self.quadlet_dir, entry)
                siblings = _read_lines_if_exists(manifest_path)
                if name not in siblings:
                    continue
                # Remove remaining sibling quadlets through podman
                remaining = [s for s in siblings if s != name and os.path.exists(os.path.join(self.quadlet_dir, s))]
                if remaining:
                    self._run_rm_safe(
                        self._build_rm_cmd(sorted(remaining)),
                        "Failed to remove sibling quadlets from .quadlets group",
                    )
                os.remove(manifest_path)
                break

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

        spec = _build_desired_spec(self.module, src, extra_files, self.podman_v6)

        if self.module.params["debug"]:
            self.results["_debug_spec"] = {
                "mode": spec["mode"],
                "marker_name": spec["marker_name"],
                "desired_files": list(spec["desired_files"].keys()),
                "removal_target": spec["removal_target"],
            }
            if spec["mode"] != MODE_REMOTE:
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

        self._write_install_markers(spec, src, extra_files)

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
                if name in installed:
                    resolved_names.append(name)
                    continue
                found_suffix = False
                for suffix in QUADLET_SUFFIXES:
                    if name + suffix in installed:
                        resolved_names.append(name + suffix)
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
            # Clean up companion files listed in markers, then the markers
            if not self.module.check_mode and os.path.isdir(self.quadlet_dir):
                for entry in os.listdir(self.quadlet_dir):
                    entry_path = os.path.join(self.quadlet_dir, entry)
                    if entry.endswith(".asset"):
                        for comp in _read_lines_if_exists(entry_path):
                            comp_path = os.path.join(self.quadlet_dir, comp)
                            if os.path.exists(comp_path):
                                os.remove(comp_path)
                        os.remove(entry_path)
                    elif entry.endswith(".quadlets.manifest"):
                        os.remove(entry_path)
        else:
            self.results["actions"].append("removed %s" % ", ".join(resolved_names))
            for name in resolved_names:
                self.results["quadlets"].append({"name": name, "path": self.quadlet_dir})
            self._cleanup_after_absent(resolved_names)

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

    if module.params["state"] == "absent":
        if not module.params["name"] and not module.params["all"]:
            module.fail_json(msg="For state='absent', either 'name' or 'all' must be specified.")

    PodmanQuadletManager(module).execute()


if __name__ == "__main__":
    main()
