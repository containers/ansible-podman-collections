FROM alpine

LABEL "key"="amazing value"
LABEL nobody=cares

ARG build_arg

ENV password root
ENV username root

WORKDIR /work

RUN adduser -D user && \
	adduser -D user2

COPY start.sh /start

RUN chmod a+rwx /start

EXPOSE 80
EXPOSE 8080/tcp
VOLUME ["/data", "/data2"]
USER user
STOPSIGNAL SIGKILL

# problem with OS w/o systemd
# HEALTHCHECK --interval=5m --timeout=3s \
#   CMD date

CMD ["1d"]
ENTRYPOINT ["/start"]

