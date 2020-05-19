[![GitHub Actions CI/CD build status — Collection test suite](https://github.com/containers/ansible-podman-collections/workflows/Collection%20build%20and%20tests/badge.svg?branch=master)](https://github.com/containers/ansible-podman-collections/actions?query=workflow%3A%22Collection%20build%20and%20tests)

Ansible Collection: containers.podman
=================================================
Basic Ansible modules for podman containers.

```yaml
- name: Run container
  podman_container:
    - name: web
      state: present
      image: ubuntu:14.04
      command: "sleep 1d"
```

Install collection from galaxy:

```bash
ansible-galaxy collection install containers.podman
```

or clone by your own:

```bash
mkdir -p ~/.ansible/collections/ansible_collections/containers/podman/
git clone https://github.com/containers/ansible-podman-collections.git ~/.ansible/collections/ansible_collections/containers/podman/
```
