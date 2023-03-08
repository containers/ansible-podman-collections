[![GitHub Actions CI/CD build status — Collection test suite](https://github.com/containers/ansible-podman-collections/workflows/Collection%20build%20and%20tests/badge.svg?branch=master)](https://github.com/containers/ansible-podman-collections/actions?query=workflow%3A%22Collection%20build%20and%20tests)

# Ansible Collection: containers.podman

This repo hosts the `containers.podman` Ansible Collection.

The collection includes the Podman container plugins to help the build and management of Podman containers.

## Documentation

For collection versions that are parts of Ansible releases, the documentation can be found on
Ansible docs site: https://docs.ansible.com/ansible/latest/collections/containers/podman

The latest documentation for current collection version in the repository is hosted on github.io docs
site: https://containers.github.io/ansible-podman-collections.

## Installation and Usage

### Installing the Collection from Ansible Galaxy

Before using the Podman collection, you need to install the collection with the `ansible-galaxy` CLI:

`ansible-galaxy collection install containers.podman`

You can also include it in a `requirements.yml` file and install it via
`ansible-galaxy collection install -r requirements.yml` using the format:

```yaml
collections:
- name: containers.podman
```

or clone by your own:

```bash
mkdir -p ~/.ansible/collections/ansible_collections/containers
git clone https://github.com/containers/ansible-podman-collections.git ~/.ansible/collections/ansible_collections/containers/podman
```

### Playbooks

To use a module from Podman collection, please reference the full namespace, collection name,
and modules name that you want to use:

```yaml
---
- name: Using Podman collection
  hosts: localhost
  tasks:
    - name: Run redis container
      containers.podman.podman_container:
        name: myredis
        image: redis
        command: redis-server --appendonly yes
        state: present
        recreate: true
        expose:
          - 6379
        volumes_from:
          - mydata
```

Or you can add full namespace and collection name in the `collections` element:

```yaml
---
- name: Using Podman collection
  hosts: localhost
  collections:
    - containers.podman
  tasks:
    - name: Build and push an image using existing credentials
      podman_image:
        name: nginx
        path: /path/to/build/dir
        push: true
        push_args:
          dest: quay.io/acme
```

## Contributing

We are accepting Github pull requests and issues.
There are many ways in which you can participate in the project, for example:

- Submit bugs and feature requests, and help us verify them
- Submit and review source code changes in Github pull requests
- Add new modules for Podman containers and images

## Testing and Development

If you want to develop new content for this collection or improve what is already
here, the easiest way to work on the collection is to clone it into one of the configured
[`COLLECTIONS_PATHS`](https://docs.ansible.com/ansible/latest/reference_appendices/config.html#collections-paths),
and work on it there.

### Testing with `ansible-test`

We use `ansible-test` for sanity.

## More Information

TBD

## Communication

Please submit Github issues for communication any issues.
You can ask Podman related questions on `#podman` channel of Ansible Podman questions
on `#ansible-podman` channel on Freenode IRC.

## License

GPL-3.0-or-later
