# Copyright (c) 2018 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
  module: podman_image
  author:
      - Sagi Shnaidman (@sshnaidm)
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
        ssh:
          description:
            - SSH options to use when pushing images with SCP transport.
          type: str
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
            - docker-archive
            - docker-daemon
            - oci-archive
            - ostree
            - docker
            - scp
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
        - The O(quadlet_file_mode) can be specied as octal numbers or as a symbolic mode
          (for example, V(u+rwx) or V(u=rw,g=r,o=r)).
          For octal numbers format, you must either add a leading zero so that Ansible's YAML parser knows it is an
          octal number (like V(0644) or V(01777)) or quote it (like V('644') or V('1777')) so Ansible receives a string
          and can do its own conversion from string into number. Giving Ansible a number without following one of these
          rules will end up with a decimal number which will have unexpected results.
        - If O(quadlet_file_mode) is not specified and the quadlet file B(does not) exist, the default V('0640') mask
          will be used
          when setting the mode for the newly created file.
        - If O(quadlet_file_mode) is not specified and the quadlet file B(does) exist, the mode of the existing file
          will be used.
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

- name: Push image to a remote host via scp transport
  containers.podman.podman_image:
    name: testimage
    pull: false
    push: true
    push_args:
      dest: user@server
      transport: scp

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

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.podman.quadlet import (
    create_quadlet_state,
)
from ..module_utils.podman.podman_image_lib import (
    PodmanImageManager,
)


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
                    ssh=dict(type="str"),
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
                            "scp",
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

    # Handle quadlet state separately
    if module.params["state"] == "quadlet":  # type: ignore
        results = create_quadlet_state(module, "image")
        module.exit_json(**results)

    try:
        manager = PodmanImageManager(module)
        results = manager.execute()
        module.exit_json(**results)
    except Exception as e:
        module.fail_json(msg=f"Failed to manage image: {str(e)}", exception=str(e))


if __name__ == "__main__":
    main()
