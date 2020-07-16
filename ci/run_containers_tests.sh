#!/bin/bash
set -o pipefail
set -ex

[[ -z "$TEST2RUN" || ! -f "ci/playbooks/containers/${TEST2RUN}.yml" ]] && {
    echo "Please specify test to run, for example TEST2RUN=podman_container";
    exit 1;
}
ANSIBLECMD=${ANSIBLECMD:-$(command -v ansible-playbook)}
echo "Testing ${TEST2RUN} module"

CURWD="$(readlink -f $(dirname ${BASH_SOURCE[0]}))"

exit_code=0
CMD="ANSIBLE_ROLES_PATH=${CURWD}/../tests/integration/targets \
    ${ANSIBLECMD:-ansible-playbook} \
    -i localhost, -c local --diff \
    ci/playbooks/containers/${TEST2RUN}.yml \
    -e ansible_python_interpreter=$(command -v python)"

bash -c "$CMD -vv" || exit_code=$?
if [[ "$exit_code" != 0 ]]; then
    bash -c "$CMD -vvvvv --diff"
fi
