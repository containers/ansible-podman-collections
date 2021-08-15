#!/bin/bash
mkdir -p /tmp/ansible-lint-installs
mkdir -p /tmp/ansible-lint-collection
rm -rf /tmp/ansible-lint-collection/*
ansible-galaxy collection build --output-path /tmp/ansible-lint-collection --force
pushd /tmp/ansible-lint-collection/
ansible-galaxy collection install -vvv --force $(ls /tmp/ansible-lint-collection/) -p /tmp/ansible-lint-installs
pushd /tmp/ansible-lint-installs/ansible_collections/containers/podman
ansible-test sanity --docker --color --truncate 0 --no-redact --no-pip-check --python 3.9 -v plugins/ tests/
popd
popd
