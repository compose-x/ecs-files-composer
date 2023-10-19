ARG ARCH=
ARG PY_VERSION=3.10
ARG BASE_IMAGE=public.ecr.aws/docker/library/python:${PY_VERSION}-slim
ARG LAMBDA_IMAGE=public.ecr.aws/lambda/python:latest

FROM $LAMBDA_IMAGE AS builder

WORKDIR /opt
RUN yum install gcc -y
COPY ecs_files_composer /opt/ecs_files_composer
COPY poetry.lock pyproject.toml MANIFEST.in README.rst LICENSE /opt/
RUN python -m pip install pip -U
RUN python -m pip install poetry
RUN poetry build


FROM $BASE_IMAGE
COPY --from=builder /opt/dist/*.whl ${LAMBDA_TASK_ROOT:-/app/}/dist/
RUN python -m pip install pip -U --no-cache-dir
RUN python -m pip install --no-cache-dir /app/dist/*.whl
WORKDIR /
ENTRYPOINT ["python", "-m", "ecs_files_composer.cli"]
