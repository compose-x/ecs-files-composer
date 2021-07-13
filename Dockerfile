ARG PY_VERSION=3.8
ARG BASE_IMAGE=public.ecr.aws/ews-network/python:${PY_VERSION}
FROM $BASE_IMAGE

RUN yum upgrade -y ;                                                            \
    yum install -y shadow-utils ;                                               \
    groupadd -r app -g 1042 &&                                                  \
    useradd -u 1042 -r -g app -m -d /app -s /sbin/nologin -c "App user" app &&  \
    chown -R app: /app &&                                                       \
    yum erase shadow-utils -y && yum clean all && rm -rfv /var/cache/yum


WORKDIR /app
USER app
ENTRYPOINT ["ecs-config-composer"]
CMD ["--env", "CONFIG"]
