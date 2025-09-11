================================================
Ansible Podman modules and plugins Release Notes
================================================

.. contents:: Topics


v1.18.0
=======

Major Changes
-------------

- Add inventory plugins for buildah and podman
- Add podman system connection modules

Minor Changes
-------------

- Add building Podman from source
- Add podman image scp option
- Add unittests for podman_image
- Improve docs and guides
- Rewrite podman_image and add tests
- Update docs and script

Bugfixes
--------

- Fix podman logout for newer Podman
- Fix podman_image correct delimiter logic for version@digest tags
- Remove quiet mode from pulling image

New Plugins
-----------

Inventory
~~~~~~~~~

- containers.podman.buildah_containers - Inventory plugin that discovers Buildah working containers as hosts
- containers.podman.podman_containers - Inventory plugin that discovers Podman containers as hosts

New Modules
-----------

- containers.podman.podman_system_connection - Manage Podman system connections
- containers.podman.podman_system_connection_info - Get info about Podman system connections

v1.17.0
=======

Release Summary
---------------

Minor changes and system info module

Minor Changes
-------------

- Add another test for volumes
- Added checks for volume opts

New Modules
-----------

- containers.podman.podman_system_info - Get podman system information from host machine

v1.16.4
=======

Release Summary
---------------

Bugfixes

Bugfixes
--------

- Document that sdnotify can be set to healthy
- Fix CI for podman_image_info
- Fix None values in LogOpt in Quadlet
- Fix conditions in CI jobs
- Fix idempotency for any podman secret driver
- Fix idempotency for systemd keyword
- Fix setuptools
- Handle image arguments in podman_container
- Remove docker protocol when inspecting image
- Set custom tmpfs idempotency
- Use usedforsecurity for hashlib.sha256 only in python version >=3.9
- correctly quote labels and environment variables for quadlets
- doc - podman_secret - fix indentation error in example
- fix(podman_image) - correct intendation on 'loop' keyword

v1.16.3
=======

Release Summary
---------------

Bugfixes

Bugfixes
--------

- Don't pull image when state is absent or pull=never (#889)
- Fix idempotency for containers with env vars containing MAX_SIZE (#893)
- Fix list tags failure in podman_search (#875)
- Fix podman_container_copy examples (#882)
- docs(podman_container) - improve comments on network property (#878)

v1.16.2
=======

Release Summary
---------------

Bugfixes and Quadlet improvements

Bugfixes
--------

- Add missing parameters for podman container quadlet
- Add new options for podman_network
- Add option to specify kube file content in module
- Add quadlet file mode option to specify file permission
- Add secret to login module
- Don't check image availability in Quadlet
- Fix max_size idempotency issue
- Fix typo in quadlet generator
- Fix unsupported pull policy in example on podman_container.py
- fix quadlet cmd_args append mistake
- podman_login does not support check_mode

v1.16.1
=======

Release Summary
---------------

Bugfixes

Bugfixes
--------

- Fix podman image permissions issue and runlable test
- don't document quadlet_dir as required when setting state=quadlet

v1.16.0
=======

Release Summary
---------------

New features, podman copy module and bugfixes

Minor Changes
-------------

- Add arch to podman build command explicitly
- Add group_add parameter for podman quadlet
- Add support for check_mode in Quadlet
- Trigger a new image build when we detect that the Containerfile has changed.
- Update inspection info about objects in modules

Bugfixes
--------

- CI - Add images removal for tests
- CI - Fix podman CI test container images
- CI - add ignore list for Ansible sanity for 2.19
- CI - bump artifacts versions for GHactions
- CI - change k8s.gcr.io to registry.k8s.io in tests
- CI - fix Podman search of invalid image
- Disable idempotency for pod_id_file
- Fix command idempotency with quotes
- Fix health-startup-cmd
- Fix logic in Podman images
- Fix quadlet parameters when container uses rootfs
- fix for tls_verify being ignored
- fix(podman_image) - skip empty volume items
- fix(podman_save) - always changed when force
- modify error and docs

New Modules
-----------

- containers.podman.podman_container_copy - Copy file to or from a container

v1.15.4
=======

Release Summary
---------------

Bugfixes

Bugfixes
--------

- Fix missing entries in network quadlet generated file
- Fix quadlet parameters for restart policy
- Idempotency improvements

v1.15.3
=======

Release Summary
---------------

Bugfixes

Minor Changes
-------------

- CI Update python for latest Ansible to 3.11 in CI

Bugfixes
--------

- Fix idempotency for empty values
- params gpus should be exit_policy

v1.15.2
=======

Release Summary
---------------

Inline Containerfile option for podman_image

Minor Changes
-------------

- Add option for inline Containerfile in podman_image

v1.15.1
=======

Release Summary
---------------

Bugfixes for systemd generation

Bugfixes
--------

- Fix idempotency for pods in case of systemd generation
- Fix idempotency for systemd generations

v1.15.0
=======

Release Summary
---------------

Podman search module and bugfixes for Podman image

Major Changes
-------------

- Add podman search

Bugfixes
--------

- Fix issue with pushing podman image to repo name and org

New Modules
-----------

- containers.podman.podman_search - Search for remote images using podman

v1.14.0
=======

Release Summary
---------------

Idempotency redesign and a lot of new options

Major Changes
-------------

- Add mount and unmount for volumes
- Add multiple subnets for networks
- Add new options for podman_container
- Add new options to pod module
- Improve idempotency for networking in podman_container
- Redesign idempotency for Podman Pod module

Minor Changes
-------------

- Add autodiscovery for build context in podman_image
- Add docs, tests and more examples for podman_pod
- Add extra_args for podman_image push and pull
- Add idempotency for mounts and volumes in podman_container
- Add new functionality tests for podman_secret
- Add path and env options for podman_secret
- Add route, dns and ipam_driver to podman_network
- Create podman secret when skip_existing=True and it does not exist

Bugfixes
--------

- Fix idempotency for pod with 0.0.0.0
- Fix transports issues in podman_image
- fix(#747) set correct HealthCmd

v1.13.0
=======

Release Summary
---------------

Quadlet support for Podman

Major Changes
-------------

- Add quadlet support for Podman modules

Bugfixes
--------

- Fix pod info for non-existant pods

v1.12.1
=======

Release Summary
---------------

Support for Podman v5 and bugfixes

Minor Changes
-------------

- CI - Fix rootfs test in CI
- CI - add custom podman path to tasks
- CI - add parametrized executables to tests
- podman_container - Add pasta as default network mode after v5
- podman_container_exec - Return data for podman exec module
- podman_generate_systemd - Fix broken example for podman_generate_systemd (#708)
- podman_login - Update podman_login.py
- podman_play - Add support for kube yaml files with multi-documents (#724)
- podman_play - Update the logic for deleting pods/containers in podman_play
- podman_pod_info - handle return being list in Podman 5 (#713)

Bugfixes
--------

- podman_container - Add check and fixed for v5 network diff
- podman_container - Fix pasta networking idempotency for v5 (#728)
- podman_container_exec - Remove unnecessary quotes in podman_container_exec module
- podman_image_info - Fix wrong return data type in podman_image_info
- podman_play - Fix kube play annotations
- podman_pod - Fix broken info of pods in Podman v5
- podman_pod - Fix pod for Podman v5
- podman_pod - Fix podman pod v5 broken info issue

v1.12.0
=======

Release Summary
---------------

New podman_secret_info module, improvements and bugfixes

Minor Changes
-------------

- Add log_opt and annotaion options to podman_play module
- Add option to parse CreateCommand easily for diff calc
- Add support for setting underlying interface in podman_network
- Alias generate systemd options stop_timeout and time
- Fix CI rootfs for podman_container
- Fix broken conmon version in CI install
- Improve security_opt comparison between existing container
- podman_container - Add new arguments to podman status commands
- podman_container - Update env_file to accept a list of files instead of a single file
- podman_secret_info - Add secrets info module

Bugfixes
--------

- Add idempotency for podman_secret module
- Catch exceptions when no JSON output in podman_image
- Fail if systemd generation failed and it's explicitly set
- Fix example name
- Fix idempotency for podman_network
- Fix idempotency when using 0.0.0.0 in ports
- Fix multi-image support for podman_save
- Fix volume inspection by name in podman_volume
- Recreate stopped containers if recreate flag is enabled

New Modules
-----------

- containers.podman.podman_secret_info - Secrets info module

v1.11.0
=======

Minor Changes
-------------

- Update docs

v1.10.4
=======

Release Summary
---------------

Bugfixes and new modules

Minor Changes
-------------

- podman_container - Add support for health-on-failure action
- podman_image -Add target support for podman build image
- podman_play - Add build and context_dir option to podman_play
- podman_pod - Add options for resource limits to podman_pod

Bugfixes
--------

- Fix common file for Python 2.7
- podman_network - Do not force network removal by default
- podman_network - Fix network DNS enable idempotency issue
- podman_pod - Fix idempotency when running inside Podman container

New Modules
-----------

- containers.podman.podman_container_exec - Executes a command in a running container
- containers.podman.podman_runlabel - Run given label from given image

v1.10.3
=======

Release Summary
---------------

Bugfixes and new options for modules

Bugfixes
--------

- podman_container - Add diff and change detection to systemd generation
- podman_container - Add example with quotes in command to docs
- podman_container - Fix healthcheck issue where defined in image
- podman_container - Fix idempoency issue with PID of container
- podman_container - Fix idempotency for RestartPolicy when MaximumRetryCount
- podman_container - Fix idempotency for devices
- podman_container - Fixed idempotency with cpus parameter
- podman_container - Improve docs about container env_file on remote machine
- podman_container - added cpu_quota parameter to podman_container
- podman_export,podman_import - Adding volume import and export option
- podman_generate_systemd - Add a force field to podman_generate_systemd
- podman_image - Add restart-sec and other options to systemd generation
- podman_image - Fix pulling short image name

v1.10.2
=======

Release Summary
---------------

Bugfixes and docs changes

Bugfixes
--------

- Add hooks-dir parameter for containers
- Add idempotency for restart-policy for containers
- Add missing options to podman network
- Add more explanation about cmd_args command usage
- Add stdout to podman build and push actions
- Added support for "userns" parameter to "play" module
- CI - fix pip installation of the collection
- CI - fix podman play job for 4.4.x versions
- Change yes/no to true/false in the modules
- Convert str to json format before evaluating length.
- Fix CI for newest Ansible branch 2.16
- Fix idempotency for pods with uidmap and gidmap
- Fix idempotency lowercase for devices
- Fix network tests for Podman v4
- Fix podman logout tests for v4
- Fix pylint issues for CI ansible-test
- Fix undesirable splitting of IPv6 host addresses
- Improved documentation of `podman_generate_systemd` module
- Prepare CI for Podman v3 backward compatibility
- Support SHA256 tag for podman images
- Update podman_image to specify CPU arch when pulling image
- added podman_prune module
- become plugin podman_unshare become_user default
- fix for buildah improper remote target
- for pod kube recreate
- pod - Support passing multiple networks with params
- podman-login - fix FIPS md5 issue and registry requirement
- podman-pod - Fix idempotency for pods in 4.4.x versions
- podman_systemd - Ignore header when comparing systemd files content

v1.10.1
=======

Release Summary
---------------

Bugfixes and minor docs changes

Minor Changes
-------------

- Add missed docs for modules

Bugfixes
--------

- podman_systemd_generate - allow empty string for prefixes
- podman_unshare - Fix docs for podman_unshare become plugin

v1.10.0
=======

Release Summary
---------------

New modules, become plugin and bugfixes.

Major Changes
-------------

- New become plugin - podman_unshare
- Podman generate systemd module

Minor Changes
-------------

- Add --sdnotify option for container
- Add example unittest for container lib
- Add protection for systemd files deletion
- Add unittests for Ansible Podman modules
- Check for gha updates weekly using dependabot
- Fix PEP8 issue in podman_image
- Fix building image with buildah and become
- Fix docs issues in podman_image
- Warning about improperly configured remote target
- add required argument to example
- docs - added simple extra_args example
- generate_systemd - implement --wants, --after and --requires
- podman_image - add file parameter for Containerfile location

Bugfixes
--------

- Delete systemd files when container/pod is deleted
- Fix example in systemd generate module
- Fix expanduser in path for systemd generation
- Fix idempotency for labels in pods
- Fix podman load module for Podman 4
- Fix rerunning playbooks with generate_systemd --new
- Improve idempotency for devices mount of rootless podman
- Improve networks idempotency for v4
- Support passing multiple networks with params
- fix pod running status for older podman versions
- podman_container should ensure image by using os path if rootfs is used

v1.9.4
======

Release Summary
---------------

Bugfixes and minor changes

Minor Changes
-------------

- Remove distutils as deprecated
- Run CI on Ubuntu 22.04
- Use 2.13 Ansible version in CI jobs instead of 2.11

Bugfixes
--------

- connection_podman - Add missing docstring for method that executes the podman commands
- podman_container - Change IpcMode default to shareable
- podman_container - Disable memory idempotency
- podman_container - Fix typo in the documentation
- podman_image - Update `podman_image` to remove image with image id
- podman_load - Loop over image names when multiple images present in archive
- podman_login - Fix idempotency for podman_login
- podman_network - Allow specify podman_network options MTU and VLAN separately
- podman_network - Fix internal networks idempotency
- podman_play - Fix play_kube not working when yaml not installed on target
- podman_play - Pass errors as a string instead of list
- podman_pod - Change network attribute from str to list in pods
- podman_pod - Fix pod network idempotency
- podman_pod - Fix pod tests in CI
- podman_pod - Fix pods list retrieve

v1.9.3
======

Release Summary
---------------

Bugfixes and minor changes

Minor Changes
-------------

- Fix sanity issues with a new Ansible version

Bugfixes
--------

- Remove idempotency for log level

v1.9.2
======

Release Summary
---------------

Bugfixes and new requires option for podman_container

Minor Changes
-------------

- Add requires option to podman_container module

Bugfixes
--------

- Add slirp4netns idempotency for pods
- Fix MAC address detection in created container
- Fix check for read-only change of root image in podman_container module
- Fix error with exitcommand for Podman v4
- Fix issue when missing plugins entry in podman_network module
- Fix new requirements for plugins documentation
- Fix podman collection for Podman version 4
- Fix tests for podman_container module
- Strip slashes from volumes

v1.9.1
======

Release Summary
---------------

Bugfixes and new options for Pods

Minor Changes
-------------

- Add new options for pod module
- Use yaml syntax highlighting where appropriate

Bugfixes
--------

- Fix podman_pod_lib behavior for ports published to multiple IPs
- Handle tlsverify correctly in podman_login
- Update secrets description and add test with secret opts

v1.9.0
======

Release Summary
---------------

New podman_tag module and fixes

Major Changes
-------------

- Add podman_tag module
- Add secrets driver and driver opts support

Minor Changes
-------------

- Add a second example to podman_pod_module.html

Bugfixes
--------

- Don't include shared 'net' if network is host in pods

New Modules
-----------

- containers.podman.podman_tag - Add an additional name to a local image

v1.8.3
======

Release Summary
---------------

Bugfixes

Bugfixes
--------

- Add documentations for generate_systemd
- Hardcode RT signal numbers
- Remove default value of log-driver
- Support --new in generate_systemd

v1.8.2
======

Release Summary
---------------

Fixes for various modules

Bugfixes
--------

- Add option for ansible-core in RPM spec file
- Add skip option for podman secret
- Add support for network-alias flag
- Allow to actually pass a list of string for "mounts"
- Don't add newlines to secrets
- Fix issue with podman and exposed ports
- Fix signal diff for truncated and RT signal names
- Support empty strings in prefixes
- Update error message when pull set to false

v1.8.1
======

Release Summary
---------------

Fixes for systemd units generation

Bugfixes
--------

- Add .service extension to systemd files
- Add aliases for image load/save
- Change python version for ansible-core to 3.9
- Fix suboption key in podman_container/podman_pod for generate_systemd documentation

v1.8.0
======

Release Summary
---------------

New modules for images and containers

Major Changes
-------------

- Add systemd generation for pods
- Generate systemd service files for containers

New Modules
-----------

- containers.podman.podman_export - Export a podman container to tar file
- containers.podman.podman_import - Import Podman container from a tar file
- containers.podman.podman_load - Load image from a tar file
- containers.podman.podman_save - Saves podman image to tar file

v1.7.1
======

Release Summary
---------------

Bugfixes and new features

Bugfixes
--------

- Add support for podman pod create --infra-name
- Fix idempotency when containers have a common network
- Remove idempotency leftovers of volumes GID,UID

v1.7.0
======

Release Summary
---------------

New module - Podman secret

Minor Changes
-------------

- Podman secret module

New Modules
-----------

- containers.podman.podman_secret - Manage podman secrets

v1.6.2
======

Release Summary
---------------

Bugfixes for idempotency and pipelining

Bugfixes
--------

- Add meta/runtime.yml which is required for Galaxy now
- Avoid exposing pipelining support for podman connections
- Change present state to be as created state
- Disable no-hosts idempotency
- Fix idempotency with systemd podman files
- Remove idempotency for volume UID/GID

v1.6.1
======

Release Summary
---------------

Bugfix for podman_container_info

Bugfixes
--------

- Fix failure when listing containers

v1.6.0
======

Release Summary
---------------

New module podman_play for playing Kubernetes YAML and bugfixes

Minor Changes
-------------

- Add Ansible 2.11 to all tests and use Ubuntu 20.04
- Add Ansible 2.11 to testing
- Add RPM building scripts
- Add support for timezones in containers

Bugfixes
--------

- Fix ansible-test issues for CI
- Fix idempotency for environment
- Fix ipv6=false issue
- Fix multi-containers options
- Fix overlayfs issue in CI for buildah connection

New Modules
-----------

- containers.podman.podman_play - Play Kubernetes YAML files with Podman

v1.5.0
======

Release Summary
---------------

New module - Podman login

Minor Changes
-------------

- Podman login module

New Modules
-----------

- containers.podman.podman_login - Login to a container registry using podman

v1.4.5
======

Release Summary
---------------

Additional fixes for newest version 3 of Podman

Bugfixes
--------

- Add IPv6 support for publishing ports
- Add sigrtmin+3 signal (required for systemd containers)
- Add support for Podman Pod restart
- Convert IPv6 to shorten form
- Fix error with images info where no images
- Fix idempotency for rootless networks from v3
- Fix no_log for newer ansible-test
- Fix uppercase labels idempotency issue
- Stop pods without recreating them

v1.4.4
======

Release Summary
---------------

Fixes for newest version 3 of Podman

Bugfixes
--------

- Attempt graceful stop when recreating container
- Don't calculate image digest in check mode
- Fix internal networks and DNS plugin for v3
- Fix podman_pod* modules for Podman v3
- Fixes for podman_container for Podman v3

v1.4.3
======

Release Summary
---------------

Documentation fixes and updates

Bugfixes
--------

- Add docs generation
- Update documentation

v1.4.2
======

Release Summary
---------------

Bugfixes for podman container

Bugfixes
--------

- documentation - Add docs to Github
- podman_container - Add 'created' state for podman_container
- podman_container - Change default log level for 3+ versions
- podman_container - Convert systemd option to a string
- podman_container - Don't recreate container if env_file is specified
- podman_container - Fix 'cap_add' and 'cap_drop' idempotency
- podman_container - Fix idempotency for multiple ports
- podman_container - Fix slirp4netns options idempotency
- podman_container - Fix uid/gid checks for podman 1.6.4 volumes
- podman_container - Handle slash removals for root volumes mount
- podman_container - Restart container in a simple manner
- podman_container - podman_container_lib - fix command idempotency
- podman_image - Add debug log and podman_actions to podman_image
- podman_image - Don't set default for validate-certs in podman_image

v1.4.1
======

Release Summary
---------------

Bugfixes for podman container

Bugfixes
--------

- podman_container - Convert gidmap to list for podman_container
- podman_container - Convert log-opts to dictionary and idempotent

v1.4.0
======

Release Summary
---------------

New modules and bugfixes, new network options

Minor Changes
-------------

- podman_container - Add log level for Podman in module
- podman_container - Add mac_address field to podman_container module
- podman_container - Add strict image compare with hashes
- podman_container - Improve compatibility with docker_container by adding aliases
- podman_container - Move containers logic to module utils
- podman_image - reuse existing results in present()
- podman_network - Add IPv6 to network
- podman_network - Add support of network options like MTU, VLAN
- podman_pod - Move pod logic to separate library

Bugfixes
--------

- podman_container - Fix force restart option for containers
- podman_container - Fix idempotency for volume GID and UID
- podman_container - Fix no_hosts idempotency for newer version
- podman_container - Remove 'detach' when creating container
- podman_image - Fix doc defaults for podman_image
- podman_logout - Handle podman logout not logging out when logged in via different tool
- podman_network - Correct IP range example for podman_network

New Modules
-----------

- containers.podman.podman_containers - Manage multiple Podman containers at once
- containers.podman.podman_login_info - Get info about Podman logged in registries
- containers.podman.podman_logout - Log out with Podman from registries

v1.3.2
======

Release Summary
---------------

bugfixes

Bugfixes
--------

- podman_container - Fix signals case for podman_container

v1.3.1
======

Release Summary
---------------

bugfixes

Bugfixes
--------

- multiple modules - fix diff calculation for lower/upper cases
- podman_container - Add note about containerPort setting
- podman_container - Fix init option it's boolean not string
- podman_container - Remove pyyaml from requirements
- podman_network - Check if dnsname plugin installed for CNI
- podman_volume - Set options for a volume as list and fix idempotency

v1.3.0
======

Release Summary
---------------

New podman_network module and bugfixes

Minor Changes
-------------

- Create podman_network module for podman networks management

Bugfixes
--------

- podman_volume - Fix return data from podman_volume module

New Modules
-----------

- containers.podman.podman_network - Manage Podman networks

v1.2.0
======

Release Summary
---------------

Add changelog file.

Minor Changes
-------------

- Add changelog file to collection.

v1.1.4
======

Release Summary
---------------

Pip install and minor fixes.

Minor Changes
-------------

- Add pip installation for podman collection.

v1.1.3
======

Release Summary
---------------

Idempotency fixes for podman containers.

Bugfixes
--------

- podman_container - Fix idempotency for case with = in env
- podman_container - Fix issue with idempotency uts, ipc with pod

v1.1.2
======

Release Summary
---------------

Urgent fix for podman connection plugin.

Bugfixes
--------

- podman_connection - Chown file for users when copy them to container

v1.1.1
======

Release Summary
---------------

New modules for volumes management.

Minor Changes
-------------

- Create podman_volume module for volumes management

Bugfixes
--------

- podman_volume_info - Improve podman volume info tests with new module

New Modules
-----------

- containers.podman.podman_volume - Manage Podman volumes

v1.1.0
======

Release Summary
---------------

New modules for pods management.

Minor Changes
-------------

- Add podman pod and pod info modules

Bugfixes
--------

- podman_container - Fix idempotency for networks and add tests

New Modules
-----------

- containers.podman.podman_pod - Manage Podman pods
- containers.podman.podman_pod_info - Retrieve information about Podman pods

v1.0.5
======

Release Summary
---------------

Idempotency and another bugfixes for podman connection plugin.

Bugfixes
--------

- podman_connection - Add check for empty dir for podman connection mount
- podman_connection - Increase verbosity for mount failure messages
- podman_container - Improve idempotency for volumes with slashesAdd idempotency for ulimits and tests
- podman_container - Improve ports idempotency and support UDP

v1.0.4
======

Release Summary
---------------

Idempotency and Podman v2 fixes

Bugfixes
--------

- podman_container - Add idempotency for ulimits and tests
- podman_container - Fix idempotency for podman > 2 versions

v1.0.3
======

Release Summary
---------------

Relicense under GPLv3 and clean up modules

Minor Changes
-------------

- Relicense under GPLv3 and clean up modules

v1.0.2
======

Release Summary
---------------

Idempotency fixes

Bugfixes
--------

- podman_container - Add idempotency for existing local volumes

v1.0.1
======

Release Summary
---------------

Idempotency and images improvements

Bugfixes
--------

- podman_container - Add inspect of image and user idempotency
- podman_image - Add option for tls_verify=false for images

v1.0.0
======

Release Summary
---------------

Initial release of collection with new modules

Minor Changes
-------------

- buildah_connection - add support of specific user
- buildah_connection - added Buildah connection rootless
- podman_connection - add user flags before container id in podman exec

Bugfixes
--------

- buildah_connection - Fix buildah debug output for py2
- podman_connection - Run pause=false w/o message condition
- podman_container - Add idempotency for user and stop signal
- podman_container - Fix idempotency issues with workdir and volumes
- podman_container - Fix image, healthcheck and other idempotency
- podman_container - Improve idempotency of podman_container in uts, ipc, networks, cpu_shares
- podman_image - only set changed=true if there is a new image
- podman_image - use correct option for remove_signatures flag

New Modules
-----------

- containers.podman.podman_container - Manage Podman containers
- containers.podman.podman_network_info module - Retrieve information about Podman networks
