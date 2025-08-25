#!/usr/bin/bash

DOCS=${1:-$HOME/podman-docs}
COLL_DIR="/tmp/docs_new_path/ansible_collections/containers/podman"
DOCS_TMP="${COLL_DIR}/tmpdocs"
HTML="${DOCS_TMP}/build/html"

# Build current collection
rm -rf /tmp/docs_new_collection
ansible-galaxy collection build --output-path /tmp/docs_new_collection --force
pkg=$(ls -t /tmp/docs_new_collection/* | head -1)
ansible-galaxy collection install -vvv --force $pkg -p /tmp/docs_new_path

pushd /tmp/docs_new_path/ansible_collections/containers/podman

mkdir -p $DOCS_TMP
chmod g-w $DOCS_TMP
ANSIBLE_COLLECTIONS_PATH=../../../ antsibull-docs sphinx-init --use-current --dest-dir $DOCS_TMP containers.podman
pushd $DOCS_TMP
python -m venv .env
source .env/bin/activate
pip install -r requirements.txt
# sed -i "s@--use-current@--squash-hierarchy --use-current@g" build.sh
ANSIBLE_COLLECTIONS_PATH=../../../../ ./build.sh
rm -rf "$HTML/_sources" "$HTML/.buildinfo" "$HTML/.doctrees"

cp -r $HTML/* $DOCS/
popd
popd
