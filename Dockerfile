ARG ARCH=
ARG PY_VERSION=3.9
ARG BASE_IMAGE=public.ecr.aws/docker/library/python:${PY_VERSION}-slim
ARG LAMBDA_IMAGE=public.ecr.aws/lambda/python:latest

FROM $LAMBDA_IMAGE as builder

WORKDIR /opt
COPY ecs_files_composer /opt/ecs_files_composer
COPY poetry.lock pyproject.toml MANIFEST.in README.rst LICENSE /opt/
RUN yum install gcc -y
RUN python -m pip install pip -U; python -m pip install poetry; poetry build
RUN pip install wheel --no-cache-dir && pip install dist/*.whl --no-cache-dir -t /opt/venv
RUN find /opt/venv -type d -name "*pycache*" | xargs -i -P10 rm -rf {}

FROM $BASE_IMAGE

COPY --from=builder /opt/venv ${LAMBDA_TASK_ROOT:-/app/}/venv
ENV PYTHONPATH /app/venv:$PYTHONPATH
ENV LD_LIBRARY_PATH=/app/venv:$LD_LIBRARY_PATH
ENV PATH /app/venv/bin:$PATH
WORKDIR /
ENTRYPOINT ["python", "-m", "ecs_files_composer.cli"]
CMD ["-h"]
