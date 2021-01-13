#!/bin/bash

DOCS_DIR=${1:-/tmp/docs}
HTML=${2:-/tmp/html}

mkdir -p $DOCS_DIR
chmod g-w $DOCS_DIR
antsibull-docs collection --use-current --squash-hierarchy --dest-dir $DOCS_DIR containers.podman
cd $DOCS_DIR
echo "extensions = ['sphinx.ext.autodoc', 'sphinx.ext.intersphinx', 'sphinx_antsibull_ext']" > conf.py
sphinx-build . $HTML
