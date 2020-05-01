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

run_ansible "$@"

ANSIBLE_VERBOSITY=4 ANSIBLE_REMOTE_USER="1000" run_ansible "$@" | tee check_log
${SUDO:-} grep -q "Using buildah connection from collection" check_log
${SUDO:-} rm -f check_log
