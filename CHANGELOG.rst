================================================
Ansible Podman modules and plugins Release Notes
================================================

.. contents:: Topics


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
