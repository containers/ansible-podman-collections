#!/usr/bin/env bash
set -o pipefail
set -eux

function run_ansible {
    ${SUDO:-} ${ANSIBLECMD:-ansible-playbook} ../connection/test_connection.yml -i "test_connection.inventory" \
        -e target_hosts="buildah" \
        -e action_prefix= \
        -e local_tmp=/tmp/ansible-local \
        -e remote_tmp=/tmp/ansible-remote \
        "$@"

}

# Issue in buildah: https://github.com/containers/buildah/issues/3126
# Hack is from: https://github.com/containers/buildah/issues/3120#issuecomment-815889314
# PR is merged here: https://github.com/containers/storage/pull/871
export STORAGE_OPTS="overlay.mount_program=/usr/bin/fuse-overlayfs"
# First run as root
run_ansible "$@"

# Create a non-root user
${SUDO:-} ${ANSIBLECMD:-ansible-playbook} -i "test_connection.inventory" ../connection/create-nonroot-user.yml \
    -e target_hosts="buildah"

# Second run as normal user
ANSIBLE_VERBOSITY=4 ANSIBLE_REMOTE_USER="testuser" run_ansible "$@" | tee check_log
${SUDO:-} grep -q "Using buildah connection from collection" check_log
${SUDO:-} rm -f check_log
