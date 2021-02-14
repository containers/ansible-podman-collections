#!/usr/bin/bash

DOCS=${1:-$HOME/podman-docs}
HTML=${2:-/tmp/html}
DOCS_TMP=${3:-/tmp/docs}


# Build current collection
rm -rf /tmp/docs_new_collection
ansible-galaxy collection build --output-path /tmp/docs_new_collection --force
pkg=$(ls -t /tmp/docs_new_collection/* | head -1)
ansible-galaxy collection install -vvv --force $pkg -p /tmp/docs_new_path

pushd /tmp/docs_new_path/ansible_collections/containers/podman

mkdir -p $DOCS_TMP
chmod g-w $DOCS_TMP
ANSIBLE_COLLECTIONS_PATH=../../../ antsibull-docs collection --use-current --squash-hierarchy --dest-dir $DOCS_TMP containers.podman
cd $DOCS_TMP
echo "extensions = ['sphinx.ext.autodoc', 'sphinx.ext.intersphinx', 'sphinx_antsibull_ext']" > conf.py
sphinx-build . $HTML
rm -rf "$HTML/_sources" "$HTML/.buildinfo" "$HTML/.doctrees"

popd
cp -r $HTML/* $DOCS/
