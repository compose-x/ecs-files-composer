ARG ARCH=
ARG PY_VERSION=3.9
ARG BASE_IMAGE=public.ecr.aws/docker/library/python:${PY_VERSION}-slim
ARG LAMBDA_IMAGE=public.ecr.aws/lambda/python:latest
FROM $BASE_IMAGE as builder

WORKDIR /opt
COPY ecs_files_composer /opt/ecs_files_composer
COPY poetry.lock pyproject.toml MANIFEST.in README.rst LICENSE /opt/
RUN python -m pip install pip -U; python -m pip install poetry; poetry build

FROM $BASE_IMAGE

RUN yum upgrade -y; yum install -y tar unzip xz gzip;\
    yum autoremove -y; yum clean packages; yum clean headers; yum clean metadata; yum clean all; rm -rfv /var/cache/yum
ENV PATH=/app/.local/bin:${PATH}
COPY --from=builder /opt/dist/ecs_files_composer-*.whl ${LAMBDA_TASK_ROOT:-/app/}/
WORKDIR /app
RUN echo $PATH ; pip install pip -U --no-cache-dir && pip install wheel --no-cache-dir && pip install *.whl --no-cache-dir
WORKDIR /
ENTRYPOINT ["ecs_files_composer"]
