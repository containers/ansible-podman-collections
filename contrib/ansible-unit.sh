#!/bin/bash
set -euo pipefail


function setup_venv() {
    # Create and use a Python venv compatible with ansible-test (3.10/3.11/3.12)
    for pybin in python3.12 python3.11 python3.10 python3; do
    if command -v "$pybin" >/dev/null 2>&1; then
        PYBIN="$pybin"; break
    fi
    done

    if [[ -z "${PYBIN:-}" ]]; then
    echo "No suitable python found (need 3.10/3.11/3.12)" >&2
    exit 1
    fi

    VENV_DIR="${HOME}/.cache/ap-unit-venv-${PYBIN##python}"
    if [[ ! -d "$VENV_DIR" ]]; then
    "$PYBIN" -m venv "$VENV_DIR"
    fi
    source "$VENV_DIR/bin/activate"
    python -m pip install --upgrade pip >/dev/null
    # Install ansible-core which provides ansible-galaxy and ansible-test
    python -m pip install -U 'ansible-core>=2.16,<2.19' 'pytest>=7' 'pytest-xdist>=3' >/dev/null

    export PATH="${VENV_DIR}/bin:${HOME}/.local/bin:${PATH}"
}

# detect that we are in virtual environment
if [[ -z "${VIRTUAL_ENV:-}" ]]; then
  echo "Setting up virtual environment"
  setup_venv
else
  echo "Already in virtual environment, skipping setup"
fi

mkdir -p /tmp/ansible-lint-installs
mkdir -p /tmp/ansible-lint-collection
rm -rf /tmp/ansible-lint-collection/*

ansible-galaxy collection build --output-path /tmp/ansible-lint-collection --force
pushd /tmp/ansible-lint-collection/ >/dev/null
ansible-galaxy collection install -vvv --force $(ls /tmp/ansible-lint-collection/) -p /tmp/ansible-lint-installs
pushd /tmp/ansible-lint-installs/ansible_collections/containers/podman >/dev/null
ansible-test units --python $(python -V | sed "s/Python //g" | awk -F"." {'print $1"."$2'}) -vvv
popd >/dev/null
popd >/dev/null
