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
  - "Idempotency for local sources uses Podman's .app/.asset manifest files and direct content comparison."
  - "For remote URLs, the module always reinstalls to ensure the host matches the configured source (reports changed=true)."
  - Supports C(.quadlets) files containing multiple quadlet sections separated by C(---) delimiter (requires Podman 6.0+).
  - Each section in a C(.quadlets) file must include a C(# FileName=<name>) comment to specify the output filename.
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
      - If the name does not include the type suffix (e.g. C(.container)), the module will attempt to find a matching quadlet file.
    type: list
    elements: str
  src:
    description:
      - Path to a quadlet file, a directory containing a quadlet application, or a URL to install when I(state=present).
      - For local files and directories, full idempotency is provided (content comparison).
      - For remote URLs, the module always installs fresh and reports C(changed=true) since content cannot be verified.
      - Directory installs support only top-level files; nested subdirectories will cause an error.
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
      description: The .app or .asset marker filename used by Podman
      type: str
    desired_files:
      description: List of filenames that should be installed
      type: list
    removal_target:
      description: What will be passed to 'podman quadlet rm' for updates
      type: str
_debug_installed_files:
  description: List of currently installed files detected from Podman manifests
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


import os
import json

from ansible.module_utils.basic import AnsibleModule  # noqa: F402

try:
    from ansible.module_utils.common.text.converters import to_native  # noqa: F402
except ImportError:
    from ansible.module_utils.common.text import to_native  # noqa: F402
from ..module_utils.podman.quadlet import (
    resolve_quadlet_dir,
    QUADLET_SUFFIXES,
)
from ..module_utils.podman.common import get_podman_version

# Install modes
MODE_DIR_APP = "dir_app"
MODE_QUADLETS_APP = "quadlets_app"
MODE_SINGLE_FILE = "single_file"
MODE_REMOTE = "remote"


def _is_remote_ref(path):
    """Check if the path is a remote URL or OCI artifact reference."""
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


def _get_asset_marker_for_quadlet(quadlet_name):
    """Get the .asset marker filename for a single quadlet file."""
    return ".%s.asset" % quadlet_name


def _add_extra_files(module, extra_files, desired_files):
    """Add extra files to desired_files dict, validating they exist."""
    for f in extra_files:
        if not os.path.isfile(f):
            module.fail_json(msg="Extra file %s is not a file" % f)
        content = _read_file_bytes(f)
        if content is not None:
            desired_files[os.path.basename(f)] = content


def _parse_quadlets_file(path):
    """Parse a .quadlets file and return a dict of {filename: content}.

    Each section is separated by '---' and must have a '# FileName=<name>' comment.
    The extension is detected from the section content (e.g. [Container] -> .container).
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
    for section in sections:
        section = section.strip()
        if not section:
            continue

        # Extract FileName from comments
        filename = None
        extension = None
        for line in section.split("\n"):
            line_stripped = line.strip()
            if line_stripped.startswith("#"):
                comment_content = line_stripped[1:].strip()
                if comment_content.startswith("FileName="):
                    filename = comment_content[9:].strip()
            elif line_stripped.startswith("[") and line_stripped.endswith("]"):
                section_name = line_stripped[1:-1].lower()
                extension = ".%s" % section_name

        if filename and extension:
            full_filename = filename + extension
            result[full_filename] = section.encode("utf-8")

    return result


def _build_desired_spec(module, src, extra_files):
    """Build a specification of what should be installed.

    Returns a dict with:
    - mode: one of MODE_DIR_APP, MODE_QUADLETS_APP, MODE_SINGLE_FILE, MODE_REMOTE
    - marker_name: the .app or .asset marker filename (None for remote)
    - desired_files: dict of {installed_filename: bytes} for local sources
    - removal_target: what to pass to 'podman quadlet rm' for updates
    """
    extra_files = extra_files or []

    # Check if src is a remote reference
    if _is_remote_ref(src):
        return {
            "mode": MODE_REMOTE,
            "marker_name": None,
            "desired_files": {},
            "removal_target": None,
        }

    # Check if any extra file is remote
    for f in extra_files:
        if _is_remote_ref(f):
            return {
                "mode": MODE_REMOTE,
                "marker_name": None,
                "desired_files": {},
                "removal_target": None,
            }

    # Local source - check existence
    if not os.path.exists(src):
        module.fail_json(msg="Source file or directory %s does not exist" % src)

    desired_files = {}

    if os.path.isdir(src):
        # Directory install - creates .app marker
        basename = os.path.basename(src.rstrip("/"))
        marker_name = ".%s.app" % basename

        # Validate: no subdirectories allowed (Podman doesn't support them)
        for entry in os.listdir(src):
            full_path = os.path.join(src, entry)
            if os.path.isdir(full_path):
                module.fail_json(
                    msg="Directory %s contains subdirectory '%s'. "
                    "Podman quadlet install does not support nested directories; "
                    "only top-level files are supported." % (src, entry)
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
            "removal_target": marker_name,
        }

    elif os.path.isfile(src):
        basename = os.path.basename(src)

        # Check if it's a .quadlets file
        if src.endswith(".quadlets"):
            # .quadlets file requires Podman 6.0+
            version_str = get_podman_version(module, fail=False)
            if version_str:
                try:
                    major_version = int(version_str.split(".")[0])
                    if major_version < 6:
                        module.fail_json(
                            msg=".quadlets files require Podman 6.0 or later (current: %s)" % version_str
                        )
                except (ValueError, IndexError):
                    pass  # If we can't parse version, let Podman handle it

            # .quadlets file - creates .app marker with extracted quadlets
            marker_name = ".%s.app" % os.path.splitext(basename)[0]
            parsed = _parse_quadlets_file(src)
            if parsed is None:
                module.fail_json(msg="Failed to parse .quadlets file %s" % src)
            desired_files = parsed

            _add_extra_files(module, extra_files, desired_files)

            return {
                "mode": MODE_QUADLETS_APP,
                "marker_name": marker_name,
                "desired_files": desired_files,
                "removal_target": marker_name,
            }
        else:
            # Single quadlet file - creates .asset marker for extra files only
            content = _read_file_bytes(src)
            if content is not None:
                desired_files[basename] = content

            _add_extra_files(module, extra_files, desired_files)

            return {
                "mode": MODE_SINGLE_FILE,
                "marker_name": _get_asset_marker_for_quadlet(basename) if extra_files else None,
                "desired_files": desired_files,
                "removal_target": basename,
            }
    else:
        module.fail_json(msg="Source %s is not a file or directory" % src)


def _get_installed_files_for_spec(spec, quadlet_dir):
    """Get the set of installed filenames based on the spec mode.

    For .app modes: read the .app marker file
    For single_file mode: the quadlet file + contents of .asset marker
    """
    if spec["mode"] == MODE_REMOTE:
        return set()

    if spec["mode"] in (MODE_DIR_APP, MODE_QUADLETS_APP):
        # Read .app marker
        marker_path = os.path.join(quadlet_dir, spec["marker_name"])
        return _read_lines_if_exists(marker_path)

    elif spec["mode"] == MODE_SINGLE_FILE:
        # The primary quadlet file + any assets
        installed = set()
        primary_quadlet_name = None

        # Get the primary file name from desired_files
        for name in spec["desired_files"]:
            # Check if it's the primary quadlet (has a quadlet suffix)
            for suffix in QUADLET_SUFFIXES:
                if name.endswith(suffix):
                    primary_quadlet_name = name
                    # Only add to installed set if file actually exists
                    if os.path.exists(os.path.join(quadlet_dir, name)):
                        installed.add(name)
                    break

        # ALWAYS check for .asset marker based on primary quadlet name
        # This is needed to detect when assets are removed from the install
        if primary_quadlet_name:
            asset_marker_path = os.path.join(quadlet_dir, _get_asset_marker_for_quadlet(primary_quadlet_name))
            installed.update(_read_lines_if_exists(asset_marker_path))

        return installed

    return set()


def _needs_change(spec, quadlet_dir):
    """Determine if installation/update is needed.

    For remote mode: always returns True (best-effort, let Podman decide)
    For local modes: compare desired vs installed file sets and contents
    """
    if spec["mode"] == MODE_REMOTE:
        # For remote, we'll try to install and let Podman tell us if it exists
        return True

    desired_set = set(spec["desired_files"].keys())
    installed_set = _get_installed_files_for_spec(spec, quadlet_dir)

    # If sets differ, definitely need change
    if desired_set != installed_set:
        return True

    # Compare content of each file
    for filename, desired_content in spec["desired_files"].items():
        installed_path = os.path.join(quadlet_dir, filename)
        installed_content = _read_file_bytes(installed_path)
        if installed_content is None or installed_content != desired_content:
            return True

    return False


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

    def _build_base_cmd(self):
        """Build base command with executable and global args."""
        cmd = [self.executable]
        if self.module.params.get("cmd_args"):
            cmd.extend(self.module.params["cmd_args"])
        return cmd

    def _build_install_cmd(self):
        """Build quadlet install command."""
        cmd = self._build_base_cmd()
        cmd.extend(["quadlet", "install"])
        if self.module.params["reload_systemd"]:
            cmd.append("--reload-systemd")
        else:
            cmd.append("--reload-systemd=false")
        cmd.append(self.module.params["src"])
        if self.module.params.get("files"):
            cmd.extend(self.module.params["files"])
        return cmd

    def _build_rm_cmd(self, names=None):
        """Build quadlet rm command."""
        cmd = self._build_base_cmd()
        cmd.extend(["quadlet", "rm"])
        if self.module.params["reload_systemd"]:
            cmd.append("--reload-systemd")
        else:
            cmd.append("--reload-systemd=false")
        if self.module.params.get("force"):
            cmd.append("--force")
        if self.module.params.get("all"):
            cmd.append("--all")
        if names:
            cmd.extend(names)
        return cmd

    def _build_list_cmd(self):
        """Build quadlet list command."""
        cmd = self._build_base_cmd()
        cmd.extend(["quadlet", "list", "--format", "json"])
        return cmd

    def _run(self, cmd, record=True):
        """Run a command and optionally record it."""
        self.module.log("PODMAN-QUADLET-DEBUG: %s" % " ".join([to_native(i) for i in cmd]))
        if record:
            self.results["podman_actions"].append(" ".join([to_native(i) for i in cmd]))
        if self.module.check_mode:
            return 0, "", ""
        return self.module.run_command(cmd)

    def _get_installed_quadlets(self):
        """Get set of installed quadlet names.

        This is a read-only operation that runs even in check_mode.
        """
        cmd = self._build_list_cmd()
        self.module.log("PODMAN-QUADLET-DEBUG: %s" % " ".join([to_native(i) for i in cmd]))
        # Always run list command, even in check_mode (it's read-only)
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

    def _install(self):
        src = self.module.params["src"]
        extra_files = self.module.params.get("files") or []

        # Build the desired spec using Podman's manifest-based approach
        spec = _build_desired_spec(self.module, src, extra_files)

        # Add debug info if requested
        if self.module.params["debug"]:
            self.results["_debug_spec"] = {
                "mode": spec["mode"],
                "marker_name": spec["marker_name"],
                "desired_files": list(spec["desired_files"].keys()),
                "removal_target": spec["removal_target"],
            }
            if spec["mode"] != MODE_REMOTE:
                installed_set = _get_installed_files_for_spec(spec, self.quadlet_dir)
                self.results["_debug_installed_files"] = list(installed_set)

        # Check if change is needed
        needs_change = _needs_change(spec, self.quadlet_dir)

        if not needs_change:
            # Already up to date
            return

        # For remote sources, we cannot verify content matches the URL.
        # To ensure Ansible's contract (what's configured = what's on host),
        # we always install fresh. Try install first, if "already exists",
        # remove and reinstall.
        if spec["mode"] == MODE_REMOTE:
            cmd = self._build_install_cmd()
            rc, out, err = self._run(cmd)
            if rc != 0:
                err_lower = err.lower()
                if "already exists" in err_lower or "refusing to overwrite" in err_lower:
                    # Need to remove existing and reinstall to ensure fresh content
                    # Extract the quadlet name from the error or URL
                    quadlet_name = os.path.basename(src)
                    rm_cmd = self._build_rm_cmd([quadlet_name])
                    rm_rc, rm_out, rm_err = self._run(rm_cmd)
                    # Ignore rm errors (might not exist with exact name)
                    if rm_rc != 0:
                        rm_err_lower = rm_err.lower()
                        if "does not exist" not in rm_err_lower and "no such" not in rm_err_lower:
                            # Try to proceed anyway - maybe Podman can handle it
                            pass
                    self.results["actions"].append("removed existing quadlet for reinstall from remote")

                    # Retry install
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

            # Remote installs always report changed=true since we can't verify content
            self.results["changed"] = True
            self.results["actions"].append("installed quadlets from %s" % src)
            self.results["quadlets"].append({"source": src, "path": self.quadlet_dir})
            if self.module.params["debug"]:
                self.results.update({"stdout": out, "stderr": err})
            return

        # For local sources with changes needed, remove existing then install
        removal_target = spec["removal_target"]
        if removal_target:
            # Check if the removal target exists
            marker_path = os.path.join(self.quadlet_dir, removal_target)
            target_exists = False

            if spec["mode"] in (MODE_DIR_APP, MODE_QUADLETS_APP):
                # For app modes, check if .app marker exists
                target_exists = os.path.exists(marker_path)
            else:
                # For single file mode, check if the quadlet file exists
                quadlet_path = os.path.join(self.quadlet_dir, removal_target)
                target_exists = os.path.exists(quadlet_path)

            if target_exists:
                rm_cmd = self._build_rm_cmd([removal_target])
                rc, out, err = self._run(rm_cmd)
                if rc != 0:
                    err_lower = err.lower()
                    if "does not exist" not in err_lower and "no such" not in err_lower:
                        self.module.fail_json(
                            msg="Failed to remove existing quadlet for update: %s" % err,
                            stdout=out,
                            stderr=err,
                            **self.results,
                        )
                self.results["actions"].append("removed existing quadlet %s for update" % removal_target)

        # Install
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

    def _absent(self):
        names = self.module.params.get("name") or []
        resolved_names = []

        # If not removing all, resolve names first for idempotency
        if not self.module.params.get("all") and names:
            installed = self._get_installed_quadlets()
            for name in names:
                if name in installed:
                    resolved_names.append(name)
                else:
                    # Try with suffixes
                    for suffix in QUADLET_SUFFIXES:
                        if name + suffix in installed:
                            resolved_names.append(name + suffix)
                            break
                    # If not found, already absent - idempotent

            if not resolved_names:
                # All quadlets already absent
                return

        # Build and run rm command
        if self.module.params.get("all"):
            cmd = self._build_rm_cmd()
        else:
            cmd = self._build_rm_cmd(resolved_names)

        rc, out, err = self._run(cmd)
        if rc != 0:
            # Treat "not found" errors as idempotent (race condition safe)
            if "does not exist" in err.lower() or "no such" in err.lower():
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

    # Custom validation for state=absent
    if module.params["state"] == "absent":
        if not module.params["name"] and not module.params["all"]:
            module.fail_json(msg="For state='absent', either 'name' or 'all' must be specified.")

    PodmanQuadletManager(module).execute()


if __name__ == "__main__":
    main()
