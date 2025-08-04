<!-- omit in toc -->
# Ansible Collection: containers.podman

[![CI/CD Status](https://img.shields.io/github/actions/workflow/status/containers/ansible-podman-collections/.github/workflows/collection-continuous-integration.yml?branch=main&style=for-the-badge&label=CI%2FCD)](https://github.com/containers/ansible-podman-collections/actions/workflows/collection-continuous-integration.yml)
[![Ansible Galaxy](https://img.shields.io/ansible/collection/d/containers/podman?style=for-the-badge&label=Ansible%20Galaxy)](https://galaxy.ansible.com/containers/podman)
[![License](https://img.shields.io/github/license/containers/ansible-podman-collections?style=for-the-badge)](COPYING)

**Manage the full lifecycle of Podman containers, images, pods, networks, and volumes with Ansible.**

This collection provides a suite of powerful and flexible Ansible modules to automate the management of your [Podman](https://podman.io/) environment. Whether you are running a single container or orchestrating complex, multi-container applications, these modules give you the tools to do it idempotently and efficiently.

---

### **Table of Contents**

- [Key Features](#key-features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Getting Started: A Simple Example](#getting-started-a-simple-example)
- [Available Content](#available-content)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)

---

## Key Features

- **Comprehensive Management:** Control every aspect of Podman, including containers, images, pods, networks, volumes, and secrets.
- **Idempotent Operations:** All modules are designed to be idempotent, ensuring predictable and consistent state for your resources.
- **Flexible and Powerful:** Exposes a wide range of Podman options, from simple container creation to advanced features like systemd integration and Quadlet file generation.
- **Connection Plugin:** Includes a `podman` connection plugin to execute Ansible tasks directly inside containers.

## Requirements

- **Ansible:** `ansible-core >= 2.12`
- **Python:** `python >= 3.9`
- **Podman:** A working installation of Podman on the target machine.

## Installation

Install the collection from Ansible Galaxy using the `ansible-galaxy` CLI:

```bash
ansible-galaxy collection install containers.podman
```

You can also include it in a `requirements.yml` file, which is useful for managing project dependencies:

```yaml
# requirements.yml
collections:
  - name: containers.podman
```

Then, install it with:

```bash
ansible-galaxy collection install -r requirements.yml
```

## Getting Started: A Simple Example

Here is a quick example of how to ensure a Redis container is running using the `podman_container` module.

```yaml
---
- name: Deploy a Redis container with Podman
  hosts: localhost
  connection: local

  tasks:
    - name: Ensure the Redis container is running
      containers.podman.podman_container:
        name: my-redis-cache
        image: docker.io/redis:alpine
        state: started
        ports:
          - "6379:6379"
        restart_policy: "always"
```

## Available Content

This collection includes:

- **Modules:**
  - `podman_container`: Manage Podman containers.
  - `podman_image`: Build, pull, and manage Podman images.
  - `podman_pod`: Create and manage Podman pods.
  - `podman_network`: Manage Podman networks.
  - `podman_volume`: Manage Podman volumes.
  - `podman_secret`: Manage Podman secrets.
  - `podman_login`/`podman_logout`: Authenticate with container registries.
  - ...and many more!

- **Connection Plugins:**
  - `podman`: Execute Ansible tasks directly within a container.
  - `buildah`: Execute Ansible tasks directly within a buildah container.

- **Become Plugins:**
  - `podman_unshare`: Execute tasks within a `podman unshare` environment.

## Documentation

- **Official Ansible Docs:** For stable, released versions of the collection, see the documentation on the [official Ansible documentation site](https://docs.ansible.com/ansible/latest/collections/containers/podman/index.html).
- **Latest Development Version:** For the most up-to-date documentation based on the `main` branch of this repository, visit our [GitHub Pages site](https://containers.github.io/ansible-podman-collections/).

## Contributing

We welcome contributions from the community! Whether you want to fix a bug, add a new feature, or improve our documentation, your help is valuable.

Please read our **[Contributing Guide](CONTRIBUTING.md)** to learn how to get started with development, testing, and submitting pull requests.

## License

This collection is licensed under the [GNU General Public License v3.0 or later](COPYING).
