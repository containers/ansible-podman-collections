# Based on modern Ansible connection plugin patterns
# Copyright (c) 2018 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
# Connection plugin to interact with existing podman containers.
#   https://github.com/containers/podman
#
# Rewritten with modern patterns and enhanced functionality

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
    author: Tomas Tomecek (@TomasTomecek)
    name: podman
    short_description: Interact with an existing podman container
    description:
        - Run commands or put/fetch files to an existing container using podman tool.
        - Supports both direct execution and filesystem mounting for optimal performance.
    options:
      remote_addr:
        description:
          - The ID or name of the container you want to access.
        default: inventory_hostname
        vars:
          - name: inventory_hostname
          - name: ansible_host
          - name: ansible_podman_host
        env:
          - name: ANSIBLE_PODMAN_HOST
        ini:
          - section: defaults
            key: remote_addr
      remote_user:
        description:
          - User specified via name or UID which is used to execute commands inside the container.
          - If you specify the user via UID, you must set C(ANSIBLE_REMOTE_TMP) to a path that exists
            inside the container and is writable by Ansible.
        ini:
          - section: defaults
            key: remote_user
        env:
          - name: ANSIBLE_REMOTE_USER
        vars:
          - name: ansible_user
      podman_extra_args:
        description:
          - Extra arguments to pass to the podman command line.
        default: ''
        type: str
        ini:
          - section: defaults
            key: podman_extra_args
        vars:
          - name: ansible_podman_extra_args
        env:
          - name: ANSIBLE_PODMAN_EXTRA_ARGS
      podman_executable:
        description:
          - Executable for podman command.
        default: podman
        type: str
        vars:
          - name: ansible_podman_executable
        env:
          - name: ANSIBLE_PODMAN_EXECUTABLE
        ini:
          - section: defaults
            key: podman_executable
      container_timeout:
        description:
          - Timeout in seconds for container operations. 0 means no timeout.
        default: 0
        type: int
        vars:
          - name: ansible_podman_timeout
        env:
          - name: ANSIBLE_PODMAN_TIMEOUT
        ini:
          - section: defaults
            key: podman_timeout
      mount_detection:
        description:
          - Enable automatic detection and use of container mount points for file operations.
        default: true
        type: bool
        vars:
          - name: ansible_podman_mount_detection
        env:
          - name: ANSIBLE_PODMAN_MOUNT_DETECTION
      ignore_mount_errors:
        description:
          - Continue with copy operations even if container mounting fails.
        default: true
        type: bool
        vars:
          - name: ansible_podman_ignore_mount_errors
      extra_env_vars:
        description:
          - Additional environment variables to set in the container.
        default: {}
        type: dict
        vars:
          - name: ansible_podman_extra_env
      privilege_escalation_method:
        description:
          - Method to use for privilege escalation inside container.
        default: 'auto'
        choices: ['auto', 'sudo', 'su', 'none']
        type: str
        vars:
          - name: ansible_podman_privilege_escalation
      working_directory:
        description:
          - Working directory for commands executed in the container.
        type: str
        vars:
          - name: ansible_podman_working_directory
"""

import os
import shlex
import shutil
import subprocess

from ansible.errors import AnsibleConnectionFailure
from ansible.module_utils.common.process import get_bin_path
try:
    from ansible.module_utils.common.text.converters import to_native, to_bytes, to_text  # noqa: F402
except ImportError:
    from ansible.module_utils.common.text import to_native, to_bytes, to_text  # noqa: F402
from ansible.plugins.connection import ConnectionBase, ensure_connect
from ansible.utils.display import Display

display = Display()


class PodmanConnectionError(AnsibleConnectionFailure):
    """Specific exception for podman connection issues"""


class ContainerNotFoundError(PodmanConnectionError):
    """Exception for when container cannot be found"""


class Connection(ConnectionBase):
    """
    Modern connection plugin for podman with enhanced error handling and performance optimizations
    """

    transport = "containers.podman.podman"
    has_pipelining = True

    def __init__(self, play_context, new_stdin, *args, **kwargs):
        super(Connection, self).__init__(play_context, new_stdin, *args, **kwargs)

        self._container_id = self._play_context.remote_addr
        self._connected = False
        self._container_info = None
        self._mount_point = None
        self._executable_path = None
        self._task_uuid = to_text(kwargs.get("task_uuid", ""))

        # No pre-validation caches to preserve performance

        display.vvvv("Using podman connection from collection", host=self._container_id)

    def _get_podman_executable(self):
        """Get and cache podman executable path with validation"""
        if self._executable_path is None:
            executable = self.get_option("podman_executable")
            try:
                self._executable_path = get_bin_path(executable)
                display.vvvv(f"Found podman executable: {self._executable_path}", host=self._container_id)
            except ValueError as e:
                raise PodmanConnectionError(f"Could not find {executable} in PATH: {e}")
        return self._executable_path

    def _build_podman_command(self, cmd_args, include_container=True):
        """Build complete podman command with all options"""
        cmd = [self._get_podman_executable()]

        # Add global options
        if self.get_option("podman_extra_args"):
            extra_args = shlex.split(to_native(self.get_option("podman_extra_args"), errors="surrogate_or_strict"))
            cmd.extend(extra_args)

        # Add subcommand and arguments
        if isinstance(cmd_args, str):
            cmd.append(cmd_args)
        else:
            cmd.extend(cmd_args)

        # Add container ID if needed
        if include_container:
            cmd.append(self._container_id)

        return cmd

    def _run_podman_command(self, cmd_args, input_data=None, check_rc=False, include_container=True):
        """Execute podman command once with error handling"""
        cmd = self._build_podman_command(cmd_args, include_container)
        cmd_bytes = [to_bytes(arg, errors="surrogate_or_strict") for arg in cmd]

        display.vvv(f"PODMAN EXEC: {' '.join(cmd)}", host=self._container_id)

        try:
            process = subprocess.Popen(
                cmd_bytes, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False
            )

            # Only pass timeout if explicitly configured
            communicate_kwargs = {}
            container_timeout = self.get_option("container_timeout")
            if isinstance(container_timeout, int) and container_timeout > 0:
                communicate_kwargs["timeout"] = container_timeout

            stdout, stderr = process.communicate(input=input_data, **communicate_kwargs)

            display.vvvvv(f"STDOUT: {stdout}", host=self._container_id)
            display.vvvvv(f"STDERR: {stderr}", host=self._container_id)
            display.vvvvv(f"RC: {process.returncode}", host=self._container_id)

            if process.returncode != 0:
                error_msg = to_text(stderr, errors="surrogate_or_strict").strip()
                lower = error_msg.lower()
                if "no such container" in lower or "does not exist" in lower or "container not known" in lower:
                    self._connected = False
                    raise ContainerNotFoundError(f"Container '{self._container_id}' not found")
                if check_rc:
                    raise PodmanConnectionError(f"Command failed (rc={process.returncode}): {error_msg}")

            return process.returncode, stdout, stderr

        except subprocess.TimeoutExpired:
            process.kill()
            timeout_val = self.get_option("container_timeout")
            self._connected = False
            raise PodmanConnectionError(f"Command timeout after {timeout_val}s")
        except Exception as e:
            raise PodmanConnectionError(f"Command execution failed: {e}")

    # No proactive validation; rely on operation failures for performance

    def _setup_mount_point(self):
        """Attempt to mount container filesystem for direct access (lightweight)"""
        if not self.get_option("mount_detection"):
            return

        try:
            rc, stdout, stderr = self._run_podman_command(["mount"])
            if rc == 0:
                mount_point = to_text(stdout, errors="surrogate_or_strict").strip()
                if mount_point and os.path.isdir(mount_point):
                    self._mount_point = mount_point
                    display.vvv(f"Container mounted at: {self._mount_point}", host=self._container_id)
                else:
                    display.vvv("Container mount point is invalid", host=self._container_id)
            else:
                display.vvv(
                    f"Container mount failed: {to_text(stderr, errors='surrogate_or_strict')}", host=self._container_id
                )
        except Exception as e:
            if not self.get_option("ignore_mount_errors"):
                raise PodmanConnectionError(f"Mount setup failed: {e}")
            display.vvv(f"Mount setup failed, continuing without mount: {e}", host=self._container_id)

    def _connect(self):
        """Establish connection to container with validation and setup"""
        super(Connection, self)._connect()

        if self._connected:
            return

        display.vvv(f"Connecting to container: {self._container_id}", host=self._container_id)

        self._connected = True
        display.vvv("Connection established successfully", host=self._container_id)

    @ensure_connect
    def exec_command(self, cmd, in_data=None, sudoable=False):
        """Execute command in container with enhanced error handling"""
        super(Connection, self).exec_command(cmd, in_data=in_data, sudoable=sudoable)

        display.vvv(f"EXEC: {cmd}", host=self._container_id)

        cmd_args_list = shlex.split(to_native(cmd, errors="surrogate_or_strict"))
        exec_cmd = ["exec"]

        # Add interactive flag only when input is provided
        if in_data is not None:
            exec_cmd.append("-i")

        # Handle user specification
        if self.get_option("remote_user"):
            exec_cmd.extend(["--user", self.get_option("remote_user")])

        # Add extra environment variables
        extra_env = self.get_option("extra_env_vars")
        if extra_env:
            for key, value in extra_env.items():
                exec_cmd.extend(["--env", f"{key}={value}"])

        # Handle privilege escalation only when explicitly requested
        privilege_method = self.get_option("privilege_escalation_method")
        if sudoable and privilege_method != "none" and privilege_method != "auto":
            if privilege_method == "sudo":
                cmd_args_list = ["sudo", "-n"] + cmd_args_list
            elif privilege_method == "su":
                cmd_args_list = ["su", "-c", " ".join(shlex.quote(arg) for arg in cmd_args_list)]

        # Add working directory option
        workdir = self.get_option("working_directory")
        if workdir:
            exec_cmd.extend(["--workdir", workdir])

        # Combine exec command: podman exec [options] container_id command
        full_cmd = exec_cmd + [self._container_id] + cmd_args_list

        rc, stdout, stderr = self._run_podman_command(full_cmd, input_data=in_data, include_container=False)
        return rc, stdout, stderr

    def put_file(self, in_path, out_path):
        """Transfer file to container using optimal method"""
        super(Connection, self).put_file(in_path, out_path)
        display.vvv(f"PUT: {in_path} -> {out_path}", host=self._container_id)

        # Lazily prepare mount point if needed
        if self._mount_point is None and self.get_option("mount_detection"):
            self._setup_mount_point()

        # Use direct filesystem copy if mount point is available and no user specified
        if self._mount_point and not self.get_option("remote_user"):
            try:
                real_out_path = os.path.join(self._mount_point, out_path.lstrip("/"))
                os.makedirs(os.path.dirname(real_out_path), exist_ok=True)
                shutil.copy2(in_path, real_out_path)
                display.vvvv(f"File copied via mount: {real_out_path}", host=self._container_id)
                return
            except Exception as e:
                display.vvv(f"Mount copy failed, falling back to podman cp: {e}", host=self._container_id)

        # Use podman cp command
        copy_cmd = ["cp", "--pause=false", in_path, f"{self._container_id}:{out_path}"]
        self._run_podman_command(copy_cmd, include_container=False, check_rc=True)

        # Change ownership if user specified
        if self.get_option("remote_user"):
            chown_cmd = [
                "exec",
                "--user",
                "root",
                self._container_id,
                "chown",
                self.get_option("remote_user"),
                out_path,
            ]
            try:
                self._run_podman_command(chown_cmd, include_container=False, check_rc=True)
            except PodmanConnectionError as e:
                display.warning(f"Failed to change file ownership: {e}")

    def fetch_file(self, in_path, out_path):
        """Retrieve file from container using optimal method"""
        super(Connection, self).fetch_file(in_path, out_path)
        display.vvv(f"FETCH: {in_path} -> {out_path}", host=self._container_id)

        # Lazily prepare mount point if needed
        if self._mount_point is None and self.get_option("mount_detection"):
            self._setup_mount_point()

        # Use direct filesystem copy if mount point is available
        if self._mount_point:
            try:
                real_in_path = os.path.join(self._mount_point, in_path.lstrip("/"))
                if os.path.exists(real_in_path):
                    os.makedirs(os.path.dirname(out_path), exist_ok=True)
                    shutil.copy2(real_in_path, out_path)
                    display.vvvv(f"File fetched via mount: {real_in_path}", host=self._container_id)
                    return
            except Exception as e:
                display.vvv(f"Mount fetch failed, falling back to podman cp: {e}", host=self._container_id)

        # Use podman cp command
        copy_cmd = ["cp", "--pause=false", f"{self._container_id}:{in_path}", out_path]
        self._run_podman_command(copy_cmd, include_container=False, check_rc=True)

    def close(self):
        """Close connection and cleanup resources"""
        super(Connection, self).close()

        if self._mount_point:
            try:
                # Attempt to unmount (optional, container keeps mount anyway)
                self._run_podman_command(["umount"], check_rc=False)
                display.vvvv("Container unmounted successfully", host=self._container_id)
            except Exception as e:
                display.vvvv(f"Unmount failed (this is usually not critical): {e}", host=self._container_id)

        self._connected = False
        display.vvv("Connection closed", host=self._container_id)
