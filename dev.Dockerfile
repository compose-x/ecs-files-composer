ARG ARCH=
ARG PY_VERSION=3.9
ARG BASE_IMAGE=public.ecr.aws/docker/library/python:${PY_VERSION}-slim
ARG LAMBDA_IMAGE=public.ecr.aws/lambda/python:latest

FROM $LAMBDA_IMAGE AS builder

WORKDIR /opt
RUN yum install gcc -y
COPY ecs_files_composer /opt/ecs_files_composer
COPY poetry.lock pyproject.toml MANIFEST.in README.rst LICENSE /opt/
RUN python -m pip install pip -U; python -m pip install poetry; poetry build


FROM $BASE_IMAGE

COPY --from=builder /opt/dist/*.whl ${LAMBDA_TASK_ROOT:-/app/}/dist/
RUN apt-get update; apt-get install gcc -y
RUN python -m pip install pip -U --no-cache-dir; \
    python -m pip install /app/dist/*.whl

WORKDIR /
ENTRYPOINT ["python", "-m", "ecs_files_composer.cli"]
CMD ["-h"]
