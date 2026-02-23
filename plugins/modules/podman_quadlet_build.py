# Copyright (c) 2018 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
  module: podman_quadlet_build
  author:
      - Benjamin Vouillaume (@BenjaminVouillaume)
  short_description: Build images for use by Podman Quadlets
  notes: []
  description:
      - Build images using Quadlet.
  options:
    annotation:
      description:
        - Dictionary of key=value pairs to add to the image. Only works with OCI images.
          Ignored for Docker containers.
      type: dict
    arch:
      description:
        - CPU architecture for the container image
      type: str
    auth_file:
      description:
        - Path to file containing authorization credentials to the remote registry.
      aliases:
        - authfile
      type: path
    build_args:
      description:
        - Dictionary of key=value pairs to add as build argument.
      aliases:
        - buildargs
      type: dict
    ca_cert_dir:
      description:
        - Path to directory containing TLS certificates and keys to use.
      type: 'path'
    cache:
      description:
        - Whether or not to use cached layers when building an image
      type: bool
    cmd_args:
      description:
        - Extra global arguments to pass to the C(podman) command (e.g., C(--log-level=debug)).
        - These are placed after the executable and before the subcommand.
      type: list
      elements: str
    dns:
      description:
      - Set custom DNS servers in the /etc/resolv.conf file that will be shared between
        all containers in the pod. A special option, "none" is allowed which disables
        creation of /etc/resolv.conf for the pod.
      type: list
      elements: str
      required: false
    dns_opt:
      description:
      - Set custom DNS options in the /etc/resolv.conf file that will be shared between
        all containers in the pod.
      type: list
      elements: str
      aliases:
        - dns_option
      required: false
    dns_search:
      description:
      - Set custom DNS search domains in the /etc/resolv.conf file that will be shared
        between all containers in the pod.
      type: list
      elements: str
      required: false
    env:
      description:
        - Dictionary of key=value pairs to add as environment variable.
      type: dict
    file:
      description: Path to the Containerfile if it is not in the build context directory.
      required: True
      type: path
    force_rm:
      description:
        - Always remove intermediate containers after a build, even if the build is unsuccessful.
      type: bool
    group_add:
      description:
        - Add additional groups to run as
      type: list
      elements: str
      aliases:
        - groups
    ignore_file:
      description: Path to an alternate .containerignore file to use when building the image.
      type: path
      aliases:
        - ignorefile
    name:
      description:
        - Name of the image to build. It may contain a tag using the format C(image:tag).
      required: True
      type: str
    labels:
      description:
        - Labels to set on the image.
      type: dict
    network:
      description:
        - List of the names of CNI networks the build should join during the RUN instructions.
      type: list
      elements: str
      aliases:
        - net
        - network_mode
    password:
      description:
        - Password to use when authenticating to remote registries.
      type: str
    pull:
      description:
        - Pull image policy. The default is 'missing'.
      type: str
      choices:
        - 'missing'
        - 'always'
        - 'never'
        - 'newer'
    retry:
      description:
        - Number of times to retry pulling or pushing images between the registry and local storage in case of failure.
          Default is 3.
      type: int
    retry_delay:
      description:
        - Duration of delay between retry attempts when pulling or pushing images between the registry and local storage in case of failure.
      type: str
      aliases:
        - retrydelay
    set_working_directory:
      description:
        - Provide context (a working directory) to podman build.
      type: str
      aliases:
        - setworkingdirectory
    target:
      description:
        - Specify the target build stage to build.
      type: str
    username:
      description:
        - username to use when authenticating to remote registries.
      type: str
    validate_certs:
      description:
        - Require HTTPS and validate certificates when pulling or pushing.
          Also used during build if a pull or push is necessary.
      type: bool
      aliases:
        - tlsverify
        - tls_verify
    variant:
      description:
        - Override the default architecture variant of the container image to be built.
      type: str
    volume:
      description:
        - Specify multiple volume / mount options to mount one or more mounts to a container.
      type: list
      elements: str
    executable:
      description:
        - Path to C(podman) executable if it is not in the C($PATH) on the machine running C(podman).
      default: 'podman'
      type: str
    state:
      description:
        - Whether an image should be present, absent, or built.
      default: "quadlet"
      type: str
      choices:
        - quadlet
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
- name: Build an image
  containers.podman.podman_quadlet_build:
    name: myimage
    file: /tmp/Containerfile

- name: Build an image
  containers.podman.podman_quadlet_build:
    name: myimage
    set_working_directory: /tmp/context

"""

RETURN = r"""
changed:
  description: Whether any change was made
  returned: always
  type: bool

"""

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.podman.quadlet import (
    create_quadlet_state,
)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            annotation=dict(type="dict"),
            arch=dict(type="str"),
            auth_file=dict(type="path", aliases=["authfile"]),
            build_args=dict(type="dict", aliases=["buildargs"]),
            ca_cert_dir=dict(type="path"),
            cache=dict(type="bool"),
            cmd_args=dict(type="list", elements="str"),
            dns=dict(type="list", elements="str", required=False),
            dns_opt=dict(type="list", elements="str", aliases=["dns_option"], required=False),
            dns_search=dict(type="list", elements="str", required=False),
            env=dict(type="dict"),
            file=dict(type="path", required=True),
            force_rm=dict(type="bool"),
            group_add=dict(type="list", elements="str", aliases=["groups"]),
            ignore_file=dict(type="path", aliases=["ignorefile"]),
            name=dict(type="str", required=True),
            labels=dict(type="dict"),
            network=dict(type="list", elements="str", aliases=["net", "network_mode"]),
            password=dict(type="str", no_log=True),
            pull=dict(type="str", choices=["always", "missing", "never", "newer"]),
            retry=dict(type="int"),
            retry_delay=dict(type="str", aliases=["retrydelay"]),
            set_working_directory=dict(type="str", aliases=["setworkingdirectory"]),
            target=dict(type="str"),
            username=dict(type="str"),
            validate_certs=dict(type="bool", aliases=["tlsverify", "tls_verify"]),
            variant=dict(type="str"),
            volume=dict(type="list", elements="str"),
            executable=dict(type="str", default="podman"),
            state=dict(
                type="str",
                default="quadlet",
                choices=["quadlet"],
            ),
            quadlet_dir=dict(type="path", required=False),
            quadlet_filename=dict(type="str"),
            quadlet_file_mode=dict(type="raw", required=False),
            quadlet_options=dict(type="list", elements="str", required=False),
        ),
        supports_check_mode=False,
        required_together=(["username", "password"],),
        mutually_exclusive=(
            ["auth_file", "username"],
            ["auth_file", "password"],
        ),
    )

    # Handle quadlet state separately
    if module.params["state"] == "quadlet":  # type: ignore
        results = create_quadlet_state(module, "build")
        module.exit_json(**results)


if __name__ == "__main__":
    main()
