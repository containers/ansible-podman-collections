#!/bin/bash

set -eux

if [[ -z "$1" ]]; then
    echo "Please provide a tag!"
    exit 1
fi
ANSIBLE_GALAXY_BIN=${GALAXY_PATH:-'ansible-galaxy'}

echo "Start building collection"
echo "Generating galaxy.yml for version $1"
${PYTHON_PATH:-python} ./contrib/build.py "$1"

rm -rf build_artifact
mkdir -p build_artifact

${ANSIBLE_GALAXY_BIN} collection build --force --output-path build_artifact/
COLLECTION_P=$(ls build_artifact/*tar.gz)

echo "Publishing collection $COLLECTION_P"

# output=$(${PYTHON_PATH:-python} -m galaxy_importer.main $COLLECTION_P)
# if echo $output | grep ERROR: ; then
#     echo "Failed check of galaxy importer!"
#     exit 1
# fi

echo "Running: ${ANSIBLE_GALAXY_BIN} collection publish --api-key HIDDEN $COLLECTION_P"
if [[ "${DRYRUN:-0}" == "1" ]]; then
    ${ANSIBLE_GALAXY_BIN} collection publish --api-key testkey $COLLECTION_P || true
else
    ${ANSIBLE_GALAXY_BIN} collection publish --api-key $API_GALAXY_TOKEN $COLLECTION_P
fi
