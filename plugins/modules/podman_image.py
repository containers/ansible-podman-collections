#!/usr/bin/python
# Copyright (c) 2018 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
  module: podman_image
  author:
      - Sam Doran (@samdoran)
  short_description: Pull images for use by podman
  notes: []
  description:
      - Build, pull, or push images using Podman.
  options:
    arch:
      description:
        - CPU architecture for the container image
      type: str
    name:
      description:
        - Name of the image to pull, push, or delete. It may contain a tag using the format C(image:tag).
      required: True
      type: str
    executable:
      description:
        - Path to C(podman) executable if it is not in the C($PATH) on the machine running C(podman).
      default: 'podman'
      type: str
    ca_cert_dir:
      description:
        - Path to directory containing TLS certificates and keys to use.
      type: 'path'
    tag:
      description:
        - Tag of the image to pull, push, or delete.
      default: "latest"
      type: str
    pull:
      description: Whether or not to pull the image.
      default: True
      type: bool
    pull_extra_args:
      description:
        - Extra arguments to pass to the pull command.
      type: str
    push:
      description: Whether or not to push an image.
      default: False
      type: bool
    path:
      description: Path to the build context directory.
      type: str
    force:
      description:
        - Whether or not to force push or pull an image.
        - When building, force the build even if the image already exists.
      type: bool
      default: False
    state:
      description:
        - Whether an image should be present, absent, or built.
      default: "present"
      type: str
      choices:
        - present
        - absent
        - build
        - quadlet
    validate_certs:
      description:
        - Require HTTPS and validate certificates when pulling or pushing.
          Also used during build if a pull or push is necessary.
      type: bool
      aliases:
        - tlsverify
        - tls_verify
    password:
      description:
        - Password to use when authenticating to remote registries.
      type: str
    username:
      description:
        - username to use when authenticating to remote registries.
      type: str
    auth_file:
      description:
        - Path to file containing authorization credentials to the remote registry.
      aliases:
        - authfile
      type: path
    build:
      description: Arguments that control image build.
      type: dict
      default: {}
      aliases:
        - build_args
        - buildargs
      suboptions:
        container_file:
          description:
            - Content of the Containerfile to use for building the image.
              Mutually exclusive with the C(file) option which is path to the existing Containerfile.
          type: str
        file:
          description:
            - Path to the Containerfile if it is not in the build context directory.
              Mutually exclusive with the C(container_file) option.
          type: path
        volume:
          description:
            - Specify multiple volume / mount options to mount one or more mounts to a container.
          type: list
          elements: str
        annotation:
          description:
            - Dictionary of key=value pairs to add to the image. Only works with OCI images.
              Ignored for Docker containers.
          type: dict
        force_rm:
          description:
            - Always remove intermediate containers after a build, even if the build is unsuccessful.
          type: bool
          default: False
        format:
          description:
            - Format of the built image.
          type: str
          choices:
            - docker
            - oci
          default: "oci"
        cache:
          description:
            - Whether or not to use cached layers when building an image
          type: bool
          default: True
        rm:
          description: Remove intermediate containers after a successful build
          type: bool
          default: True
        extra_args:
          description:
            - Extra args to pass to build, if executed. Does not idempotently check for new build args.
          type: str
        target:
          description:
            - Specify the target build stage to build.
          type: str
    push_args:
      description: Arguments that control pushing images.
      type: dict
      default: {}
      suboptions:
        compress:
          description:
            - Compress tarball image layers when pushing to a directory using the 'dir' transport.
          type: bool
        format:
          description:
            - Manifest type to use when pushing an image using the 'dir' transport (default is manifest type of source)
          type: str
          choices:
            - oci
            - v2s1
            - v2s2
        remove_signatures:
          description: Discard any pre-existing signatures in the image
          type: bool
        sign_by:
          description:
            - Path to a key file to use to sign the image.
          type: str
        dest:
          description: Path or URL where image will be pushed.
          type: str
          aliases:
            - destination
        transport:
          description:
            - Transport to use when pushing in image. If no transport is set, will attempt to push to a remote registry
          type: str
          choices:
            - dir
            - docker
            - docker-archive
            - docker-daemon
            - oci-archive
            - ostree
        extra_args:
          description:
            - Extra args to pass to push, if executed. Does not idempotently check for new push args.
          type: str
    quadlet_dir:
      description:
        - Path to the directory to write quadlet file in.
          By default, it will be set as C(/etc/containers/systemd/) for root user,
          C(~/.config/containers/systemd/) for non-root users.
      type: path
      required: false
    quadlet_filename:
      description:
        - Name of quadlet file to write. By default it takes image name without prefixes and tags.
      type: str
    quadlet_file_mode:
      description:
        - The permissions of the quadlet file.
        - The O(quadlet_file_mode) can be specied as octal numbers or as a symbolic mode (for example, V(u+rwx) or V(u=rw,g=r,o=r)).
          For octal numbers format, you must either add a leading zero so that Ansible's YAML parser knows it is an
          octal number (like V(0644) or V(01777)) or quote it (like V('644') or V('1777')) so Ansible receives a string
          and can do its own conversion from string into number. Giving Ansible a number without following one of these
          rules will end up with a decimal number which will have unexpected results.
        - If O(quadlet_file_mode) is not specified and the quadlet file B(does not) exist, the default V('0640') mask will be used
          when setting the mode for the newly created file.
        - If O(quadlet_file_mode) is not specified and the quadlet file B(does) exist, the mode of the existing file will be used.
        - Specifying O(quadlet_file_mode) is the best way to ensure files are created with the correct permissions.
      type: raw
      required: false
    quadlet_options:
      description:
        - Options for the quadlet file. Provide missing in usual network args
          options as a list of lines to add.
      type: list
      elements: str
      required: false
"""

EXAMPLES = r"""
- name: Pull an image
  containers.podman.podman_image:
    name: quay.io/bitnami/wildfly

- name: Remove an image
  containers.podman.podman_image:
    name: quay.io/bitnami/wildfly
    state: absent

- name: Remove an image with image id
  containers.podman.podman_image:
    name: 0e901e68141f
    state: absent

- name: Pull a specific version of an image
  containers.podman.podman_image:
    name: redis
    tag: 4

- name: Build a basic OCI image
  containers.podman.podman_image:
    name: nginx
    path: /path/to/build/dir

- name: Build a basic OCI image with advanced parameters
  containers.podman.podman_image:
    name: nginx
    path: /path/to/build/dir
    build:
      cache: no
      force_rm: true
      format: oci
      annotation:
        app: nginx
        function: proxy
        info: Load balancer for my cool app
      extra_args: "--build-arg KEY=value"

- name: Build a Docker formatted image
  containers.podman.podman_image:
    name: nginx
    path: /path/to/build/dir
    build:
      format: docker

- name: Build and push an image using existing credentials
  containers.podman.podman_image:
    name: nginx
    path: /path/to/build/dir
    push: true
    push_args:
      dest: quay.io/acme

- name: Build and push an image using an auth file
  containers.podman.podman_image:
    name: nginx
    push: true
    auth_file: /etc/containers/auth.json
    push_args:
      dest: quay.io/acme

- name: Build and push an image using username and password
  containers.podman.podman_image:
    name: nginx
    push: true
    username: bugs
    password: "{{ vault_registry_password }}"
    push_args:
      dest: quay.io/acme

- name: Build and push an image to multiple registries
  containers.podman.podman_image:
    name: "{{ item }}"
    path: /path/to/build/dir
    push: true
    auth_file: /etc/containers/auth.json
  loop:
    - quay.io/acme/nginx
    - docker.io/acme/nginx

- name: Build and push an image to multiple registries with separate parameters
  containers.podman.podman_image:
    name: "{{ item.name }}"
    tag: "{{ item.tag }}"
    path: /path/to/build/dir
    push: true
    auth_file: /etc/containers/auth.json
    push_args:
      dest: "{{ item.dest }}"
  loop:
    - name: nginx
      tag: 4
      dest: docker.io/acme

    - name: nginx
      tag: 3
      dest: docker.io/acme

- name: Pull an image for a specific CPU architecture
  containers.podman.podman_image:
    name: nginx
    arch: amd64

- name: Build a container from file inline
  containers.podman.podman_image:
    name: mycustom_image
    state: build
    build:
      container_file: |-
        FROM alpine:latest
        CMD echo "Hello, World!"

- name: Create a quadlet file for an image
  containers.podman.podman_image:
    name: docker.io/library/alpine:latest
    state: quadlet
    quadlet_dir: /etc/containers/systemd
    quadlet_filename: alpine-latest
    quadlet_file_mode: '0640'
    quadlet_options:
      - Variant=arm/v7
      - |
        [Install]
        WantedBy=default.target
"""

RETURN = r"""
  image:
    description:
      - Image inspection results for the image that was pulled, pushed, or built.
    returned: success
    type: dict
    sample: [
                {
                    "Id": "6d1ef012b5674ad8a127ecfa9b5e6f5178d171b90ee462846974177fd9bdd39f",
                    "Digest": "sha256:8421d9a84432575381bfabd248f1eb56f3aa21d9d7cd2511583c68c9b7511d10",
                    "RepoTags": [
                        "docker.io/library/alpine:3.7"
                    ],
                    "RepoDigests": [
                        "docker.io/library/alpine@sha256:8421...",
                        "docker.io/library/alpine@sha256:9225..."
                    ],
                    "Parent": "",
                    "Comment": "",
                    "Created": "2019-03-07T22:19:53.447205048Z",
                    "Config": {
                        "Env": [
                                "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
                        ],
                        "Cmd": [
                                "/bin/sh"
                        ],
                        "ArgsEscaped": true
                    },
                    "Version": "18.06.1-ce",
                    "Author": "",
                    "Architecture": "amd64",
                    "Os": "linux",
                    "Size": 4467084,
                    "VirtualSize": 4467084,
                    "GraphDriver": {
                        "Name": "overlay",
                        "Data": {
                                "UpperDir": "/home/user/.local/share/containers/storage/overlay/3fc6.../diff",
                                "WorkDir": "/home/user/.local/share/containers/storage/overlay/3fc6.../work"
                        }
                    },
                    "RootFS": {
                        "Type": "layers",
                        "Layers": [
                                "sha256:3fc6..."
                        ]
                    },
                    "Labels": null,
                    "Annotations": {},
                    "ManifestType": "application/vnd.docker.distribution.manifest.v2+json",
                    "User": "",
                    "History": [
                        {
                                "created": "2019-03-07T22:19:53.313789681Z",
                                "created_by": "/bin/sh -c #(nop) ADD file:aa17928... in / "
                        },
                        {
                                "created": "2019-03-07T22:19:53.447205048Z",
                                "created_by": "/bin/sh -c #(nop)  CMD [\"/bin/sh\"]",
                                "empty_layer": true
                        }
                    ],
                    "NamesHistory": [
                        "docker.io/library/alpine:3.7"
                    ]
                }
            ]

"""

import json  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402
import shlex  # noqa: E402
import tempfile  # noqa: E402
import time  # noqa: E402
import hashlib  # noqa: E402
import sys  # noqa: E402

from ansible.module_utils._text import to_native
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.containers.podman.plugins.module_utils.podman.common import (
    run_podman_command,
)
from ansible_collections.containers.podman.plugins.module_utils.podman.quadlet import (
    create_quadlet_state,
)


class PodmanImageManager(object):

    def __init__(self, module, results):

        super(PodmanImageManager, self).__init__()

        self.module = module
        self.results = results
        self.name = self.module.params.get("name")
        self.executable = self.module.get_bin_path(module.params.get("executable"), required=True)
        self.tag = self.module.params.get("tag")
        self.pull = self.module.params.get("pull")
        self.pull_extra_args = self.module.params.get("pull_extra_args")
        self.push = self.module.params.get("push")
        self.path = self.module.params.get("path")
        self.force = self.module.params.get("force")
        self.state = self.module.params.get("state")
        self.validate_certs = self.module.params.get("validate_certs")
        self.auth_file = self.module.params.get("auth_file")
        self.username = self.module.params.get("username")
        self.password = self.module.params.get("password")
        self.ca_cert_dir = self.module.params.get("ca_cert_dir")
        self.build = self.module.params.get("build")
        self.push_args = self.module.params.get("push_args")
        self.arch = self.module.params.get("arch")

        repo, repo_tag = parse_repository_tag(self.name)
        if repo_tag:
            self.name = repo
            self.tag = repo_tag

        delimiter = ":" if "sha256" not in self.tag else "@"
        self.image_name = "{name}{d}{tag}".format(name=self.name, d=delimiter, tag=self.tag)

        if self.state in ["present", "build"]:
            self.present()

        if self.state in ["absent"]:
            self.absent()

        if self.state == "quadlet":
            self.make_quadlet()

    def _run(self, args, expected_rc=0, ignore_errors=False):
        cmd = " ".join([self.executable] + [to_native(i) for i in args])
        self.module.log("PODMAN-IMAGE-DEBUG: %s" % cmd)
        self.results["podman_actions"].append(cmd)
        return run_podman_command(
            module=self.module,
            executable=self.executable,
            args=args,
            expected_rc=expected_rc,
            ignore_errors=ignore_errors,
        )

    def _get_id_from_output(self, lines, startswith=None, contains=None, split_on=" ", maxsplit=1):
        layer_ids = []
        for line in lines.splitlines():
            if startswith and line.startswith(startswith) or contains and contains in line:
                splitline = line.rsplit(split_on, maxsplit)
                layer_ids.append(splitline[1])

        # Podman 1.4 changed the output to only include the layer id when run in quiet mode
        if not layer_ids:
            layer_ids = lines.splitlines()

        return layer_ids[-1]

    def _find_containerfile_from_context(self):
        """
        Find a Containerfile/Dockerfile path inside a podman build context.
        Return 'None' if none exist.
        """

        containerfile_path = None
        for filename in [os.path.join(self.path, fname) for fname in ["Containerfile", "Dockerfile"]]:
            if os.path.exists(filename):
                containerfile_path = filename
                break
        return containerfile_path

    def _get_containerfile_contents(self):
        """
        Get the path to the Containerfile for an invocation
        of the module, and return its contents.

        See if either `file` or `container_file` in build args are populated,
        fetch their contents if so. If not, return the contents of the Containerfile
        or Dockerfile from inside the build context, if present.

        If we don't find a Containerfile/Dockerfile in any of the above
        locations, return 'None'.
        """

        build_file_arg = self.build.get("file") if self.build else None
        containerfile_contents = self.build.get("container_file") if self.build else None

        container_filename = None
        if build_file_arg:
            container_filename = build_file_arg
        elif self.path and not build_file_arg:
            container_filename = self._find_containerfile_from_context()

        if not containerfile_contents and os.access(container_filename, os.R_OK):
            with open(container_filename) as f:
                containerfile_contents = f.read()

        return containerfile_contents

    def _hash_containerfile_contents(self, containerfile_contents):
        """
        When given the contents of a Containerfile/Dockerfile,
        return a sha256 hash of these contents.
        """
        if not containerfile_contents:
            return None

        # usedforsecurity keyword arg was introduced in python 3.9
        if sys.version_info < (3, 9):
            return hashlib.sha256(
                containerfile_contents.encode(),
            ).hexdigest()
        else:
            return hashlib.sha256(containerfile_contents.encode(), usedforsecurity=False).hexdigest()

    def _get_args_containerfile_hash(self):
        """
        If we can find a Containerfile in any of the module args
        or inside the build context, hash its contents.

        If we don't have this, return an empty string.
        """

        args_containerfile_hash = None

        context_has_containerfile = self.path and self._find_containerfile_from_context()

        should_hash_args_containerfile = (
            context_has_containerfile
            or self.build.get("file") is not None
            or self.build.get("container_file") is not None
        )

        if should_hash_args_containerfile:
            args_containerfile_hash = self._hash_containerfile_contents(self._get_containerfile_contents())
        return args_containerfile_hash

    def present(self):
        image = self.find_image()

        existing_image_containerfile_hash = ""
        args_containerfile_hash = self._get_args_containerfile_hash()

        if image:
            digest_before = image[0].get("Digest", image[0].get("digest"))
            labels = image[0].get("Labels") or {}
            if "containerfile.hash" in labels:
                existing_image_containerfile_hash = labels["containerfile.hash"]
        else:
            digest_before = None

        both_hashes_exist_and_differ = (
            args_containerfile_hash
            and existing_image_containerfile_hash
            and args_containerfile_hash != existing_image_containerfile_hash
        )

        if not image or self.force or both_hashes_exist_and_differ:
            if self.state == "build" or self.path:
                # Build the image
                build_file = self.build.get("file") if self.build else None
                container_file_txt = self.build.get("container_file") if self.build else None
                if build_file and container_file_txt:
                    self.module.fail_json(msg="Cannot specify both build file and container file content!")
                if not self.path and build_file:
                    self.path = os.path.dirname(build_file)
                elif not self.path and not build_file and not container_file_txt:
                    self.module.fail_json(msg="Path to build context or file is required when building an image")
                self.results["actions"].append(
                    "Built image {image_name} from {path}".format(
                        image_name=self.image_name, path=self.path or "default context"
                    )
                )
                if not self.module.check_mode:
                    self.results["image"], self.results["stdout"] = self.build_image(args_containerfile_hash)
                    image = self.results["image"]
            else:
                # Pull the image
                self.results["actions"].append("Pulled image {image_name}".format(image_name=self.image_name))
                if not self.module.check_mode:
                    image = self.results["image"] = self.pull_image()

            if not image:
                image = self.find_image()
            if not self.module.check_mode:
                digest_after = image[0].get("Digest", image[0].get("digest"))
                self.results["changed"] = digest_before != digest_after
            else:
                self.results["changed"] = True

        if self.push:
            self.results["image"], output = self.push_image()
            self.results["stdout"] += "\n" + output
        if image and not self.results.get("image"):
            self.results["image"] = image

    def absent(self):
        image = self.find_image()
        image_id = self.find_image_id()

        if image:
            self.results["actions"].append("Removed image {name}".format(name=self.name))
            self.results["changed"] = True
            self.results["image"]["state"] = "Deleted"
            if not self.module.check_mode:
                self.remove_image()
        elif image_id:
            self.results["actions"].append("Removed image with id {id}".format(id=self.image_name))
            self.results["changed"] = True
            self.results["image"]["state"] = "Deleted"
            if not self.module.check_mode:
                self.remove_image_id()

    def make_quadlet(self):
        results_update = create_quadlet_state(self.module, "image")
        self.results.update(results_update)
        self.module.exit_json(**self.results)

    def find_image(self, image_name=None):
        if image_name is None:
            image_name = self.image_name
        # Let's find out if image exists
        rc, out, err = self._run(["image", "exists", image_name], ignore_errors=True)
        if rc == 0:
            inspect_json = self.inspect_image(image_name)
        else:
            return None
        args = ["image", "ls", image_name, "--format", "json"]
        rc, images, err = self._run(args, ignore_errors=True)
        try:
            images = json.loads(images)
        except json.decoder.JSONDecodeError:
            self.module.fail_json(msg="Failed to parse JSON output from podman image ls: {out}".format(out=images))
        if len(images) == 0:
            return None
        inspect_json = self.inspect_image(image_name)
        if self._is_target_arch(inspect_json, self.arch) or not self.arch:
            return images or inspect_json
        return None

    def _is_target_arch(self, inspect_json=None, arch=None):
        return arch and inspect_json[0]["Architecture"] == arch

    def find_image_id(self, image_id=None):
        if image_id is None:
            # If image id is set as image_name, remove tag
            image_id = re.sub(":.*$", "", self.image_name)
        args = ["image", "ls", "--quiet", "--no-trunc"]
        rc, candidates, err = self._run(args, ignore_errors=True)
        candidates = [re.sub("^sha256:", "", c) for c in str.splitlines(candidates)]
        for c in candidates:
            if c.startswith(image_id):
                return image_id
        return None

    def inspect_image(self, image_name=None):
        if image_name is None:
            image_name = self.image_name
        args = ["inspect", image_name, "--format", "json"]
        rc, image_data, err = self._run(args)
        try:
            image_data = json.loads(image_data)
        except json.decoder.JSONDecodeError:
            self.module.fail_json(msg="Failed to parse JSON output from podman inspect: {out}".format(out=image_data))
        if len(image_data) > 0:
            return image_data
        else:
            return None

    def pull_image(self, image_name=None):
        if image_name is None:
            image_name = self.image_name

        args = ["pull", image_name, "-q"]

        if self.arch:
            args.extend(["--arch", self.arch])

        if self.auth_file:
            args.extend(["--authfile", self.auth_file])

        if self.username and self.password:
            cred_string = "{user}:{password}".format(user=self.username, password=self.password)
            args.extend(["--creds", cred_string])

        if self.validate_certs is not None:
            if self.validate_certs:
                args.append("--tls-verify")
            else:
                args.append("--tls-verify=false")

        if self.ca_cert_dir:
            args.extend(["--cert-dir", self.ca_cert_dir])

        if self.pull_extra_args:
            args.extend(shlex.split(self.pull_extra_args))

        rc, out, err = self._run(args, ignore_errors=True)
        if rc != 0:
            if not self.pull:
                self.module.fail_json(
                    msg="Failed to find image {image_name} locally, image pull set to {pull_bool}".format(
                        pull_bool=self.pull, image_name=image_name
                    )
                )
            else:
                self.module.fail_json(msg="Failed to pull image {image_name}".format(image_name=image_name))
        return self.inspect_image(out.strip())

    def build_image(self, containerfile_hash):
        args = ["build"]
        args.extend(["-t", self.image_name])

        if self.validate_certs is not None:
            if self.validate_certs:
                args.append("--tls-verify")
            else:
                args.append("--tls-verify=false")

        annotation = self.build.get("annotation")
        if annotation:
            for k, v in annotation.items():
                args.extend(["--annotation", "{k}={v}".format(k=k, v=v)])

        if self.ca_cert_dir:
            args.extend(["--cert-dir", self.ca_cert_dir])

        if self.build.get("force_rm"):
            args.append("--force-rm")

        image_format = self.build.get("format")
        if image_format:
            args.extend(["--format", image_format])

        if self.arch:
            args.extend(["--arch", self.arch])

        if not self.build.get("cache"):
            args.append("--no-cache")

        if self.build.get("rm"):
            args.append("--rm")

        containerfile = self.build.get("file")
        if containerfile:
            args.extend(["--file", containerfile])
        container_file_txt = self.build.get("container_file")
        if container_file_txt:
            # create a temporarly file with the content of the Containerfile
            if self.path:
                container_file_path = os.path.join(self.path, "Containerfile.generated_by_ansible_%s" % time.time())
            else:
                container_file_path = os.path.join(
                    tempfile.gettempdir(),
                    "Containerfile.generated_by_ansible_%s" % time.time(),
                )
            with open(container_file_path, "w") as f:
                f.write(container_file_txt)
            args.extend(["--file", container_file_path])

        if containerfile_hash:
            args.extend(["--label", f"containerfile.hash={containerfile_hash}"])

        volume = self.build.get("volume")
        if volume:
            for v in volume:
                if v:
                    args.extend(["--volume", v])

        if self.auth_file:
            args.extend(["--authfile", self.auth_file])

        if self.username and self.password:
            cred_string = "{user}:{password}".format(user=self.username, password=self.password)
            args.extend(["--creds", cred_string])

        extra_args = self.build.get("extra_args")
        if extra_args:
            args.extend(shlex.split(extra_args))

        target = self.build.get("target")
        if target:
            args.extend(["--target", target])
        if self.path:
            args.append(self.path)

        rc, out, err = self._run(args, ignore_errors=True)
        if rc != 0:
            self.module.fail_json(
                msg="Failed to build image {image}: {out} {err}".format(image=self.image_name, out=out, err=err)
            )
        # remove the temporary file if it was created
        if container_file_txt:
            os.remove(container_file_path)
        last_id = self._get_id_from_output(out, startswith="-->")
        return self.inspect_image(last_id), out + err

    def push_image(self):
        args = ["push"]

        if self.validate_certs is not None:
            if self.validate_certs:
                args.append("--tls-verify")
            else:
                args.append("--tls-verify=false")

        if self.ca_cert_dir:
            args.extend(["--cert-dir", self.ca_cert_dir])

        if self.username and self.password:
            cred_string = "{user}:{password}".format(user=self.username, password=self.password)
            args.extend(["--creds", cred_string])

        if self.auth_file:
            args.extend(["--authfile", self.auth_file])

        if self.push_args.get("compress"):
            args.append("--compress")

        push_format = self.push_args.get("format")
        if push_format:
            args.extend(["--format", push_format])

        if self.push_args.get("remove_signatures"):
            args.append("--remove-signatures")

        sign_by_key = self.push_args.get("sign_by")
        if sign_by_key:
            args.extend(["--sign-by", sign_by_key])

        push_extra_args = self.push_args.get("extra_args")
        if push_extra_args:
            args.extend(shlex.split(push_extra_args))

        args.append(self.image_name)

        # Build the destination argument
        dest = self.push_args.get("dest")
        transport = self.push_args.get("transport")

        if dest is None:
            dest = self.image_name

        if transport:
            if transport == "docker":
                dest_format_string = "{transport}://{dest}"
            elif transport == "ostree":
                dest_format_string = "{transport}:{name}@{dest}"
            else:
                dest_format_string = "{transport}:{dest}"
                if transport == "docker-daemon" and ":" not in dest:
                    dest_format_string = "{transport}:{dest}:latest"
            dest_string = dest_format_string.format(transport=transport, name=self.name, dest=dest)
        else:
            dest_string = dest
            # In case of dest as a repository with org name only, append image name to it
            if ":" not in dest and "@" not in dest and len(dest.rstrip("/").split("/")) == 2:
                dest_string = dest.rstrip("/") + "/" + self.image_name

        if "/" not in dest_string and "@" not in dest_string and "docker-daemon" not in dest_string:
            self.module.fail_json(msg="Destination must be a full URL or path to a directory with image name and tag.")

        args.append(dest_string)
        self.module.log(
            "PODMAN-IMAGE-DEBUG: Pushing image {image_name} to {dest_string}".format(
                image_name=self.image_name, dest_string=dest_string
            )
        )
        self.results["actions"].append(" ".join(args))
        self.results["changed"] = True
        out, err = "", ""
        if not self.module.check_mode:
            rc, out, err = self._run(args, ignore_errors=True)
            if rc != 0:
                self.module.fail_json(
                    msg="Failed to push image {image_name}".format(image_name=self.image_name),
                    stdout=out,
                    stderr=err,
                    actions=self.results["actions"],
                    podman_actions=self.results["podman_actions"],
                )

        return self.inspect_image(self.image_name), out + err

    def remove_image(self, image_name=None):
        if image_name is None:
            image_name = self.image_name

        args = ["rmi", image_name]
        if self.force:
            args.append("--force")
        rc, out, err = self._run(args, ignore_errors=True)
        if rc != 0:
            self.module.fail_json(
                msg="Failed to remove image {image_name}. {err}".format(image_name=image_name, err=err)
            )
        return out

    def remove_image_id(self, image_id=None):
        if image_id is None:
            image_id = re.sub(":.*$", "", self.image_name)

        args = ["rmi", image_id]
        if self.force:
            args.append("--force")
        rc, out, err = self._run(args, ignore_errors=True)
        if rc != 0:
            self.module.fail_json(
                msg="Failed to remove image with id {image_id}. {err}".format(image_id=image_id, err=err)
            )
        return out


def parse_repository_tag(repo_name):
    parts = repo_name.rsplit("@", 1)
    if len(parts) == 2:
        return tuple(parts)
    parts = repo_name.rsplit(":", 1)
    if len(parts) == 2 and "/" not in parts[1]:
        return tuple(parts)
    return repo_name, None


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type="str", required=True),
            arch=dict(type="str"),
            tag=dict(type="str", default="latest"),
            pull=dict(type="bool", default=True),
            pull_extra_args=dict(type="str"),
            push=dict(type="bool", default=False),
            path=dict(type="str"),
            force=dict(type="bool", default=False),
            state=dict(
                type="str",
                default="present",
                choices=["absent", "present", "build", "quadlet"],
            ),
            validate_certs=dict(type="bool", aliases=["tlsverify", "tls_verify"]),
            executable=dict(type="str", default="podman"),
            auth_file=dict(type="path", aliases=["authfile"]),
            username=dict(type="str"),
            password=dict(type="str", no_log=True),
            ca_cert_dir=dict(type="path"),
            quadlet_dir=dict(type="path", required=False),
            quadlet_filename=dict(type="str"),
            quadlet_file_mode=dict(type="raw", required=False),
            quadlet_options=dict(type="list", elements="str", required=False),
            build=dict(
                type="dict",
                aliases=["build_args", "buildargs"],
                default={},
                options=dict(
                    annotation=dict(type="dict"),
                    force_rm=dict(type="bool", default=False),
                    file=dict(type="path"),
                    container_file=dict(type="str"),
                    format=dict(type="str", choices=["oci", "docker"], default="oci"),
                    cache=dict(type="bool", default=True),
                    rm=dict(type="bool", default=True),
                    volume=dict(type="list", elements="str"),
                    extra_args=dict(type="str"),
                    target=dict(type="str"),
                ),
            ),
            push_args=dict(
                type="dict",
                default={},
                options=dict(
                    compress=dict(type="bool"),
                    format=dict(type="str", choices=["oci", "v2s1", "v2s2"]),
                    remove_signatures=dict(type="bool"),
                    sign_by=dict(type="str"),
                    dest=dict(
                        type="str",
                        aliases=["destination"],
                    ),
                    extra_args=dict(type="str"),
                    transport=dict(
                        type="str",
                        choices=[
                            "dir",
                            "docker-archive",
                            "docker-daemon",
                            "oci-archive",
                            "ostree",
                            "docker",
                        ],
                    ),
                ),
            ),
        ),
        supports_check_mode=True,
        required_together=(["username", "password"],),
        mutually_exclusive=(
            ["auth_file", "username"],
            ["auth_file", "password"],
        ),
    )

    results = dict(
        changed=False,
        actions=[],
        podman_actions=[],
        image={},
        stdout="",
    )

    PodmanImageManager(module, results)
    module.exit_json(**results)


if __name__ == "__main__":
    main()
