# Based on modern Ansible connection plugin patterns
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
# Connection plugin for building container images using buildah tool
#   https://github.com/containers/buildah
#
# Rewritten with modern patterns and enhanced functionality

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
    author: Tomas Tomecek (@TomasTomecek)
    name: buildah
    short_description: Interact with an existing buildah container
    description:
        - Run commands or put/fetch files to an existing container using buildah tool.
        - Supports container building workflows with enhanced error handling and performance.
    options:
      remote_addr:
        description:
          - The ID or name of the buildah working container you want to access.
        default: inventory_hostname
        vars:
          - name: ansible_host
          - name: inventory_hostname
          - name: ansible_buildah_host
        env:
          - name: ANSIBLE_BUILDAH_HOST
        ini:
          - section: defaults
            key: remote_addr
      remote_user:
        description:
          - User specified via name or UID which is used to execute commands inside the container.
          - For buildah, this affects both run commands and copy operations.
        ini:
          - section: defaults
            key: remote_user
        env:
          - name: ANSIBLE_REMOTE_USER
        vars:
          - name: ansible_user
      buildah_executable:
        description:
          - Executable for buildah command.
        default: buildah
        type: str
        vars:
          - name: ansible_buildah_executable
        env:
          - name: ANSIBLE_BUILDAH_EXECUTABLE
        ini:
          - section: defaults
            key: buildah_executable
      buildah_extra_args:
        description:
          - Extra arguments to pass to the buildah command line.
        default: ''
        type: str
        ini:
          - section: defaults
            key: buildah_extra_args
        vars:
          - name: ansible_buildah_extra_args
        env:
          - name: ANSIBLE_BUILDAH_EXTRA_ARGS
      container_timeout:
        description:
          - Timeout in seconds for container operations.
        default: 30
        type: int
        vars:
          - name: ansible_buildah_timeout
        env:
          - name: ANSIBLE_BUILDAH_TIMEOUT
        ini:
          - section: defaults
            key: buildah_timeout
      connection_retries:
        description:
          - Number of retries for failed container operations.
        default: 3
        type: int
        vars:
          - name: ansible_buildah_retries
        env:
          - name: ANSIBLE_BUILDAH_RETRIES
      mount_detection:
        description:
          - Enable automatic detection and use of container mount points for file operations.
        default: true
        type: bool
        vars:
          - name: ansible_buildah_mount_detection
        env:
          - name: ANSIBLE_BUILDAH_MOUNT_DETECTION
      ignore_mount_errors:
        description:
          - Continue with copy operations even if container mounting fails.
        default: true
        type: bool
        vars:
          - name: ansible_buildah_ignore_mount_errors
      extra_env_vars:
        description:
          - Additional environment variables to set in the container.
        default: {}
        type: dict
        vars:
          - name: ansible_buildah_extra_env
      working_directory:
        description:
          - Set working directory for commands executed in the container.
        type: str
        vars:
          - name: ansible_buildah_working_directory
        env:
          - name: ANSIBLE_BUILDAH_WORKING_DIRECTORY
      auto_commit:
        description:
          - Automatically commit changes after successful operations.
        default: false
        type: bool
        vars:
          - name: ansible_buildah_auto_commit
"""

import json
import os
import shlex
import shutil
import subprocess
import time

from ansible.errors import AnsibleConnectionFailure
from ansible.module_utils.common.process import get_bin_path
from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.plugins.connection import ConnectionBase, ensure_connect
from ansible.utils.display import Display

display = Display()


class BuildahConnectionError(AnsibleConnectionFailure):
    """Specific exception for buildah connection issues"""

    pass


class ContainerNotFoundError(BuildahConnectionError):
    """Exception for when container cannot be found"""

    pass


class Connection(ConnectionBase):
    """
    Modern connection plugin for buildah with enhanced error handling and performance optimizations
    """

    transport = "containers.podman.buildah"
    has_pipelining = True

    def __init__(self, play_context, new_stdin, *args, **kwargs):
        super(Connection, self).__init__(play_context, new_stdin, *args, **kwargs)

        self._container_id = self._play_context.remote_addr
        self._connected = False
        self._container_info = None
        self._mount_point = None
        self._executable_path = None
        self._task_uuid = to_text(kwargs.get("task_uuid", ""))

        # Initialize caches
        self._command_cache = {}
        self._container_validation_cache = {}

        display.vvvv("Using buildah connection from collection", host=self._container_id)

    def _get_buildah_executable(self):
        """Get and cache buildah executable path with validation"""
        if self._executable_path is None:
            executable = self.get_option("buildah_executable")
            try:
                self._executable_path = get_bin_path(executable)
                display.vvvv(f"Found buildah executable: {self._executable_path}", host=self._container_id)
            except ValueError as e:
                raise BuildahConnectionError(f"Could not find {executable} in PATH: {e}")
        return self._executable_path

    def _build_buildah_command(self, cmd_args, include_container=True):
        """Build complete buildah command with all options"""
        cmd = [self._get_buildah_executable()]

        # Add global options
        if self.get_option("buildah_extra_args"):
            extra_args = shlex.split(to_native(self.get_option("buildah_extra_args"), errors="surrogate_or_strict"))
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

    def _run_buildah_command(
        self, cmd_args, input_data=None, check_rc=True, include_container=True, retries=None, output_file=None
    ):
        """Execute buildah command with comprehensive error handling and retries"""
        if retries is None:
            retries = self.get_option("connection_retries")

        cmd = self._build_buildah_command(cmd_args, include_container)
        cmd_bytes = [to_bytes(arg, errors="surrogate_or_strict") for arg in cmd]

        display.vvv(f"BUILDAH EXEC: {' '.join(cmd)}", host=self._container_id)

        last_exception = None
        for attempt in range(retries + 1):
            try:
                # Handle output redirection
                stdout_fd = subprocess.PIPE
                if output_file:
                    stdout_fd = open(output_file, "wb")

                process = subprocess.Popen(
                    cmd_bytes, stdin=subprocess.PIPE, stdout=stdout_fd, stderr=subprocess.PIPE, shell=False
                )

                stdout, stderr = process.communicate(input=input_data, timeout=self.get_option("container_timeout"))

                if output_file:
                    stdout_fd.close()
                    stdout = b""  # No stdout when redirected to file

                display.vvvvv(f"STDOUT: {stdout}", host=self._container_id)
                display.vvvvv(f"STDERR: {stderr}", host=self._container_id)
                display.vvvvv(f"RC: {process.returncode}", host=self._container_id)

                stdout = to_bytes(stdout, errors="surrogate_or_strict")
                stderr = to_bytes(stderr, errors="surrogate_or_strict")

                if check_rc and process.returncode != 0:
                    error_msg = to_text(stderr, errors="surrogate_or_strict").strip()
                    if "no such container" in error_msg.lower() or "container not known" in error_msg.lower():
                        raise ContainerNotFoundError(f"Container '{self._container_id}' not found")
                    raise BuildahConnectionError(f"Command failed (rc={process.returncode}): {error_msg}")

                return process.returncode, stdout, stderr

            except subprocess.TimeoutExpired:
                if output_file and "stdout_fd" in locals():
                    stdout_fd.close()
                process.kill()
                timeout = self.get_option("container_timeout")
                last_exception = BuildahConnectionError(f"Command timeout after {timeout}s")
                if attempt < retries:
                    display.vvv(f"Command timeout, retrying ({attempt + 1}/{retries + 1})", host=self._container_id)
                    time.sleep(1)
                    continue

            except Exception as e:
                if output_file and "stdout_fd" in locals():
                    stdout_fd.close()
                last_exception = BuildahConnectionError(f"Command execution failed: {e}")
                if attempt < retries:
                    display.vvv(f"Command failed, retrying ({attempt + 1}/{retries + 1})", host=self._container_id)
                    time.sleep(1)
                    continue

        raise last_exception

    def _validate_container(self):
        """Validate that the container exists and is accessible"""
        if self._container_id in self._container_validation_cache:
            return self._container_validation_cache[self._container_id]

        try:
            # Check if container exists by inspecting it
            unused, stdout, unused1 = self._run_buildah_command(
                ["inspect", self._container_id], include_container=False, retries=1
            )

            self._container_info = json.loads(to_text(stdout, errors="surrogate_or_strict"))

            # Validate container is in a working state
            if not self._container_info:
                raise BuildahConnectionError("Container inspection returned empty data")

            self._container_validation_cache[self._container_id] = True
            display.vvv("Container validation successful", host=self._container_id)
            return True

        except (json.JSONDecodeError, IndexError, KeyError) as e:
            raise BuildahConnectionError(f"Failed to parse container information: {e}")

    def _setup_mount_point(self):
        """Attempt to mount container filesystem for direct access"""
        if not self.get_option("mount_detection"):
            return

        try:
            unused, stdout, unused1 = self._run_buildah_command(["mount"], retries=1)
            mount_point = to_text(stdout, errors="surrogate_or_strict").strip()

            if mount_point and os.path.isdir(mount_point):
                # Ensure mount point has trailing separator for consistency
                self._mount_point = mount_point.rstrip(os.sep) + os.sep
                display.vvv(f"Container mounted at: {self._mount_point}", host=self._container_id)
            else:
                display.vvv("Container mount point is invalid", host=self._container_id)
        except Exception as e:
            if not self.get_option("ignore_mount_errors"):
                raise BuildahConnectionError(f"Mount setup failed: {e}")
            display.vvv(f"Mount setup failed, continuing without mount: {e}", host=self._container_id)

    def _connect(self):
        """Establish connection to container with validation and setup"""
        super(Connection, self)._connect()

        if self._connected:
            return

        display.vvv(f"Connecting to buildah container: {self._container_id}", host=self._container_id)

        # Validate container exists and is accessible
        self._validate_container()

        # Setup mount point for file operations
        self._setup_mount_point()

        self._connected = True
        display.vvv("Connection established successfully", host=self._container_id)

    @ensure_connect
    def exec_command(self, cmd, in_data=None, sudoable=False):
        """Execute command in container with enhanced error handling"""
        super(Connection, self).exec_command(cmd, in_data=in_data, sudoable=sudoable)

        display.vvv(f"EXEC: {cmd}", host=self._container_id)

        cmd_args_list = shlex.split(to_native(cmd, errors="surrogate_or_strict"))
        run_cmd = ["run"]

        # Handle user specification
        if self.get_option("remote_user") and self.get_option("remote_user") != "root":
            run_cmd.extend(["--user", self.get_option("remote_user")])

        # Add extra environment variables
        extra_env = self.get_option("extra_env_vars")
        if extra_env:
            for key, value in extra_env.items():
                run_cmd.extend(["--env", f"{key}={value}"])

        # Set working directory if specified
        working_dir = self.get_option("working_directory")
        if working_dir:
            run_cmd.extend(["--workingdir", working_dir])

        # Add container name first, then command
        run_cmd.append(self._container_id)

        # Handle privilege escalation for buildah (different from podman)
        if sudoable and self.get_option("remote_user") != "root":
            # For buildah, privilege escalation means running as root user
            # Remove the --user option and don't use sudo inside container
            run_cmd = [arg for arg in run_cmd if not (arg == "--user" or arg == self.get_option("remote_user"))]

        run_cmd.extend(cmd_args_list)

        try:
            # Use include_container=False since we already added container name
            rc, stdout, stderr = self._run_buildah_command(run_cmd, input_data=in_data, include_container=False)

            # Auto-commit if enabled and command succeeded
            if rc == 0 and self.get_option("auto_commit"):
                self._auto_commit_changes()
            return rc, stdout, stderr

        except ContainerNotFoundError:
            # Container might have been removed, invalidate cache and retry once
            if self._container_id in self._container_validation_cache:
                del self._container_validation_cache[self._container_id]
                self._connected = False
                self._connect()
                rc, stdout, stderr = self._run_buildah_command(run_cmd, input_data=in_data, include_container=False)
                return rc, stdout, stderr
            raise

    def _auto_commit_changes(self):
        """Automatically commit changes if enabled"""
        try:
            display.vvv("Auto-committing container changes", host=self._container_id)
            self._run_buildah_command(["commit"], check_rc=False, retries=1)
        except Exception as e:
            display.warning(f"Auto-commit failed: {e}")

    def put_file(self, in_path, out_path):
        """Transfer file to container using optimal method"""
        super(Connection, self).put_file(in_path, out_path)
        display.vvv(f"PUT: {in_path} -> {out_path}", host=self._container_id)

        # Use direct filesystem copy if mount point is available
        if self._mount_point:
            try:
                real_out_path = os.path.join(self._mount_point, out_path.lstrip("/"))
                os.makedirs(os.path.dirname(real_out_path), exist_ok=True)
                shutil.copy2(in_path, real_out_path)
                display.vvvv(f"File copied via mount: {real_out_path}", host=self._container_id)

                # Handle ownership when user is specified
                if self.get_option("remote_user") and self.get_option("remote_user") != "root":
                    try:
                        shutil.chown(real_out_path, user=self.get_option("remote_user"))
                    except (OSError, LookupError) as e:
                        display.vvv(f"Could not change ownership via mount: {e}", host=self._container_id)
                        # Remove the file and fall back to buildah copy
                        try:
                            os.remove(real_out_path)
                        except OSError:
                            pass
                        raise Exception("Ownership change failed, falling back to buildah copy")
                return
            except Exception as e:
                display.vvv(f"Mount copy failed, falling back to buildah copy: {e}", host=self._container_id)

        # Use buildah copy command
        # buildah copy [options] container src dest
        copy_cmd = ["copy"]

        # Add chown flag if user specified
        if self.get_option("remote_user") and self.get_option("remote_user") != "root":
            copy_cmd.extend(["--chown", self.get_option("remote_user")])

        copy_cmd.extend([self._container_id, in_path, out_path])

        self._run_buildah_command(copy_cmd, include_container=False)

    def fetch_file(self, in_path, out_path):
        """Retrieve file from container using optimal method"""
        super(Connection, self).fetch_file(in_path, out_path)
        display.vvv(f"FETCH: {in_path} -> {out_path}", host=self._container_id)

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
                display.vvv(f"Mount fetch failed, falling back to buildah run: {e}", host=self._container_id)

        # Use buildah run with cat command and output redirection
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        cat_cmd = ["run", self._container_id, "cat", in_path]
        self._run_buildah_command(cat_cmd, output_file=out_path, include_container=False)

    def close(self):
        """Close connection and cleanup resources"""
        super(Connection, self).close()

        if self._mount_point:
            try:
                # Attempt to unmount the container
                self._run_buildah_command(["umount"], retries=1, check_rc=False)
                display.vvvv("Container unmounted successfully", host=self._container_id)
            except Exception as e:
                display.vvvv(f"Unmount failed: {e}", host=self._container_id)

        # Auto-commit on close if enabled
        if self.get_option("auto_commit"):
            self._auto_commit_changes()

        # Clear caches
        self._command_cache.clear()

        self._connected = False
        display.vvv("Connection closed", host=self._container_id)
