# Based on the docker connection plugin
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
# Connection plugin for building container images using buildah tool
#   https://github.com/projectatomic/buildah
#
# Written by: Tomas Tomecek (https://github.com/TomasTomecek)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = '''
    short_description: Interact with an existing buildah container
    description:
        - Run commands or put/fetch files to an existing container using buildah tool.
    author: Tomas Tomecek (@TomasTomecek)
    name: buildah
    options:
      remote_addr:
        description:
            - The ID of the container you want to access.
        default: inventory_hostname
        vars:
            - name: ansible_host
#        keyword:
#            - name: hosts
      remote_user:
        description:
            - User specified via name or ID which is used to execute commands inside the container.
        ini:
          - section: defaults
            key: remote_user
        env:
          - name: ANSIBLE_REMOTE_USER
        vars:
          - name: ansible_user
#        keyword:
#            - name: remote_user
'''

import os
import shlex
import shutil
import subprocess

from ansible.errors import AnsibleError
from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.plugins.connection import ConnectionBase, ensure_connect
from ansible.utils.display import Display

display = Display()


# this _has to be_ named Connection
class Connection(ConnectionBase):
    """
    This is a connection plugin for buildah: it uses buildah binary to interact with the containers
    """

    # String used to identify this Connection class from other classes
    transport = 'containers.podman.buildah'
    has_pipelining = True

    def __init__(self, play_context, new_stdin, *args, **kwargs):
        super(Connection, self).__init__(play_context, new_stdin, *args, **kwargs)

        self._container_id = self._play_context.remote_addr
        self._connected = False
        # container filesystem will be mounted here on host
        self._mount_point = None
        # `buildah inspect` doesn't contain info about what the default user is -- if it's not
        # set, it's empty
        self.user = self._play_context.remote_user
        display.vvvv("Using buildah connection from collection")

    def _set_user(self):
        self._buildah(b"config", [b"--user=" + to_bytes(self.user, errors='surrogate_or_strict')])

    def _buildah(self, cmd, cmd_args=None, in_data=None, outfile_stdout=None):
        """
        run buildah executable

        :param cmd: buildah's command to execute (str)
        :param cmd_args: list of arguments to pass to the command (list of str/bytes)
        :param in_data: data passed to buildah's stdin
        :param outfile_stdout: file for writing STDOUT to
        :return: return code, stdout, stderr
        """
        buildah_exec = 'buildah'
        local_cmd = [buildah_exec]

        if isinstance(cmd, str):
            local_cmd.append(cmd)
        else:
            local_cmd.extend(cmd)
        if self.user and self.user != 'root':
            if cmd == 'run':
                local_cmd.extend(("--user", self.user))
            elif cmd == 'copy':
                local_cmd.extend(("--chown", self.user))
        local_cmd.append(self._container_id)

        if cmd_args:
            if isinstance(cmd_args, str):
                local_cmd.append(cmd_args)
            else:
                local_cmd.extend(cmd_args)

        local_cmd = [to_bytes(i, errors='surrogate_or_strict')
                     for i in local_cmd]

        display.vvv("RUN %s" % (local_cmd,), host=self._container_id)
        if outfile_stdout:
            stdout_fd = open(outfile_stdout, "wb")
        else:
            stdout_fd = subprocess.PIPE
        p = subprocess.Popen(local_cmd, shell=False, stdin=subprocess.PIPE,
                             stdout=stdout_fd, stderr=subprocess.PIPE)

        stdout, stderr = p.communicate(input=in_data)
        display.vvvv("STDOUT %s" % to_text(stdout))
        display.vvvv("STDERR %s" % to_text(stderr))
        display.vvvv("RC CODE %s" % p.returncode)
        stdout = to_bytes(stdout, errors='surrogate_or_strict')
        stderr = to_bytes(stderr, errors='surrogate_or_strict')
        return p.returncode, stdout, stderr

    def _connect(self):
        """
        no persistent connection is being maintained, mount container's filesystem
        so we can easily access it
        """
        super(Connection, self)._connect()
        rc, self._mount_point, stderr = self._buildah("mount")
        if rc != 0:
            display.v("Failed to mount container %s: %s" % (self._container_id, stderr.strip()))
        else:
            self._mount_point = self._mount_point.strip() + to_bytes(os.path.sep, errors='surrogate_or_strict')
            display.vvvv("MOUNTPOINT %s RC %s STDERR %r" % (self._mount_point, rc, stderr))
        self._connected = True

    @ensure_connect
    def exec_command(self, cmd, in_data=None, sudoable=False):
        """ run specified command in a running OCI container using buildah """
        super(Connection, self).exec_command(cmd, in_data=in_data, sudoable=sudoable)

        # shlex.split has a bug with text strings on Python-2.6 and can only handle text strings on Python-3
        cmd_args_list = shlex.split(to_native(cmd, errors='surrogate_or_strict'))

        rc, stdout, stderr = self._buildah("run", cmd_args_list, in_data)

        display.vvvv("STDOUT %r\nSTDERR %r" % (stderr, stderr))
        return rc, stdout, stderr

    def put_file(self, in_path, out_path):
        """ Place a local file located in 'in_path' inside container at 'out_path' """
        super(Connection, self).put_file(in_path, out_path)
        display.vvv("PUT %s TO %s" % (in_path, out_path), host=self._container_id)
        if not self._mount_point or self.user:
            rc, stdout, stderr = self._buildah(
                "copy", [in_path, out_path])
            if rc != 0:
                raise AnsibleError(
                    "Failed to copy file from %s to %s in container %s\n%s" % (
                        in_path, out_path, self._container_id, stderr)
                )
        else:
            real_out_path = self._mount_point + to_bytes(out_path, errors='surrogate_or_strict')
            shutil.copyfile(
                to_bytes(in_path, errors='surrogate_or_strict'),
                to_bytes(real_out_path, errors='surrogate_or_strict')
            )

    def fetch_file(self, in_path, out_path):
        """ obtain file specified via 'in_path' from the container and place it at 'out_path' """
        super(Connection, self).fetch_file(in_path, out_path)
        display.vvv("FETCH %s TO %s" %
                    (in_path, out_path), host=self._container_id)
        if not self._mount_point:
            rc, stdout, stderr = self._buildah(
                "run",
                ["cat", to_bytes(in_path, errors='surrogate_or_strict')],
                outfile_stdout=out_path)
            if rc != 0:
                raise AnsibleError("Failed to fetch file from %s to %s from container %s\n%s" % (
                    in_path, out_path, self._container_id, stderr))
        else:
            real_in_path = self._mount_point + \
                to_bytes(in_path, errors='surrogate_or_strict')
            shutil.copyfile(
                to_bytes(real_in_path, errors='surrogate_or_strict'),
                to_bytes(out_path, errors='surrogate_or_strict')
            )

    def close(self):
        """ unmount container's filesystem """
        super(Connection, self).close()
        rc, stdout, stderr = self._buildah("umount")
        display.vvvv("RC %s STDOUT %r STDERR %r" % (rc, stdout, stderr))
        self._connected = False
