================================================
Ansible Podman modules and plugins Release Notes
================================================

.. contents:: Topics


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
