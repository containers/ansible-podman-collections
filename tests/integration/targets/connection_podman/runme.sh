#!/usr/bin/env bash

set -o pipefail
set -eux

function run_ansible {
    ${SUDO:-} ${ANSIBLECMD:-ansible-playbook} ../connection/test_connection.yml -i "test_connection.inventory" \
        -e target_hosts="podman" \
        -e action_prefix= \
        -e local_tmp=/tmp/ansible-local \
        -e remote_tmp=/tmp/ansible-remote \
        "$@"

}

run_ansible "$@"
LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 run_ansible "$@"
ANSIBLE_VERBOSITY=4 ANSIBLE_REMOTE_TMP="/tmp" ANSIBLE_REMOTE_USER="1000" run_ansible "$@" | tee check_log
${SUDO:-} grep -q "Using podman connection from collection" check_log
${SUDO:-} rm -f check_log
set +o pipefail
ANSIBLE_PODMAN_EXECUTABLE=fakepodman run_ansible "$@" 2>&1 | grep "fakepodman command not found in PATH"
set -o pipefail
ANSIBLE_PODMAN_EXECUTABLE=fakepodman run_ansible "$@" && {
    echo "Playbook with fakepodman should fail!"
    exit 1
}
ANSIBLE_VERBOSITY=4 ANSIBLE_PODMAN_EXTRA_ARGS=" --log-level debug " run_ansible "$@" | grep "level=debug msg="
