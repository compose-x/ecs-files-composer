# SPDX-License-Identifier: MPL-2.0
# Copyright 2020-2022 John Mille<john@compose-x.io>

"""Main module."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .input import Model

import json
from os import environ, path
from tempfile import TemporaryDirectory

import yaml
from yaml import Loader

from ecs_files_composer import input
from ecs_files_composer.aws_mgmt import S3Fetcher
from ecs_files_composer.certificates_mgmt import process_x509_certs
from ecs_files_composer.common import LOG
from ecs_files_composer.files_mgmt import File


def init_config(
    raw=None,
    file_path=None,
    env_var=None,
    ssm_parameter=None,
    s3_config=None,
    secret_config=None,
    role_arn=None,
    external_id=None,
    decode_base64=False,
    context=None,
    override_folder: str = None,
):
    """
    Function to initialize the configuration

    :param raw: The raw content of a content
    :param str file_path: The path to a job configuration file
    :param str env_var:
    :param str ssm_parameter:
    :param str s3_config:
    :param str secret_config:
    :param str role_arn:
    :param str external_id:
    :param bool decode_base64:
    :return: The ECS Config description
    :rtype: dict
    """
    iam_override = {"SessionName": "FilesComposerInit"}
    if ssm_parameter or s3_config or secret_config:
        role_arn = environ.get("CONFIG_IAM_ROLE_ARN", role_arn)
        external_id = environ.get("CONFIG_IAM_EXTERNAL_ID", external_id)
        if role_arn:
            iam_override.update({"RoleArn": role_arn})
        if external_id:
            iam_override.update({"ExternalId": external_id})
    if ssm_parameter:
        initial_config = {"source": {"Ssm": {"ParameterName": ssm_parameter}}}
    elif s3_config:
        if not S3Fetcher.bucket_re.match(s3_config):
            raise ValueError(
                "The value for S3 URI is not valid.",
                s3_config,
                "Expected to match",
                S3Fetcher.bucket_re.pattern,
            )
        initial_config = {
            "source": {
                "S3": {
                    "BucketName": S3Fetcher.bucket_re.match(s3_config).group("bucket"),
                    "Key": S3Fetcher.bucket_re.match(s3_config).group("key"),
                }
            }
        }
    elif secret_config:
        initial_config = {"source": {"Secret": {"SecretId": secret_config}}}
    elif file_path:
        with open(path.abspath(file_path)) as file_fd:
            config_content = file_fd.read()
        initial_config = {"content": config_content}
    elif raw:
        initial_config = {"content": raw}
    elif env_var:
        initial_config = {"content": environ.get(env_var, None)}
    else:
        raise ValueError("No input source was provided")
    if not initial_config:
        raise ImportError("Failed to import a configuration content")
    LOG.debug(initial_config)
    if not override_folder:
        temp_dir = TemporaryDirectory()
        config_path = f"{temp_dir.name}/init.conf"
    else:
        config_path = f"{override_folder}/init.conf"
    jobs_input_def = {
        "files": {config_path: initial_config},
        "IamOverride": iam_override,
    }
    if decode_base64:
        initial_config["encoding"] = "base64"
    if context:
        initial_config["context"] = context
    start_jobs(jobs_input_def)
    try:
        with open(config_path) as config_fd:
            try:
                config = yaml.load(config_fd.read(), Loader=Loader)
                LOG.info(f"Successfully loaded YAML config {config_path}")
                return config
            except yaml.YAMLError:
                config = json.loads(config_fd.read())
                LOG.info(f"Successfully loaded JSON config {config_path}")
                return config
            except Exception:
                LOG.error("Input content is neither JSON nor YAML formatted")
                raise
    except OSError as error:
        LOG.exception(error)
        LOG.error(f"Failed to read input file from {config_path}")


def process_files(job: Model, override_session=None) -> None:
    files: list = []
    for file_path, file in job.files.items():
        config = json.loads(file.json(by_alias=True))
        file_redef = File(**config)
        file_redef.path = file_path
        files.append(file_redef)
    for file in files:
        file.handler(job.iam_override, override_session)
        LOG.info(f"Tasks for {file.path} completed.")


def start_jobs(config: dict, override_session=None):
    """
    Starting point to run the files job

    :param config:
    :param override_session:
    :return:
    """
    job = input.Model(**config)
    if job.certificates:
        process_x509_certs(job)
    if job.files:
        process_files(job, override_session)
