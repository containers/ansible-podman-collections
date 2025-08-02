#!/bin/bash
mkdir -p /tmp/ansible-lint-installs
mkdir -p /tmp/ansible-lint-collection
rm -rf /tmp/ansible-lint-collection/*
ansible-galaxy collection build --output-path /tmp/ansible-lint-collection --force
pushd /tmp/ansible-lint-collection/
ansible-galaxy collection install -vvv --force $(ls /tmp/ansible-lint-collection/) -p /tmp/ansible-lint-installs
pushd /tmp/ansible-lint-installs/ansible_collections/containers/podman
ansible-test units --python 3.12 -vvv
popd
popd
