FROM alpine

LABEL install="podman run --env IMAGE=IMAGE --rm IMAGE /bin/sh /testinstall.sh"
LABEL run="/usr/bin/touch /tmp/testedrunfortests"

ADD testinstall.sh /
