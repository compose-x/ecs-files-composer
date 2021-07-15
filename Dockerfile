ARG ARCH=
ARG PY_VERSION=3.8
ARG BASE_IMAGE=public.ecr.aws/ews-network/python:${PY_VERSION}
ARG LAMBDA_IMAGE=public.ecr.aws/lambda/python:latest
FROM $BASE_IMAGE as builder

WORKDIR /opt
COPY ecs_config_composer /opt/ecs_config_composer
COPY setup.py requirements.txt MANIFEST.in README.rst LICENSE /opt/
RUN python -m venv venv ; source venv/bin/activate ; pip install wheel;  python setup.py sdist bdist_wheel; ls -l dist/

FROM $BASE_IMAGE

RUN yum upgrade -y
ENV PATH=/app/.local/bin:${PATH}
COPY --from=builder /opt/dist/ecs_config_composer-*.whl ${LAMBDA_TASK_ROOT:-/app/}/
WORKDIR /app
RUN echo $PATH ; pip install pip -U --no-cache-dir && pip install wheel --no-cache-dir && pip install *.whl --no-cache-dir
WORKDIR /
ENTRYPOINT ["ecs_config_composer"]
CMD ["--env", "CONFIG"]
