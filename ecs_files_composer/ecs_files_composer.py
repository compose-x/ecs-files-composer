# SPDX-License-Identifier: MPL-2.0
# Copyright 2020-2022 John Mille<john@compose-x.io>

"""Main module."""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from enum import Enum
from os import environ, path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, ByteString

import yaml
from dacite import Config, from_dict
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
    print_generated_config: bool = False,
):
    """Function to initialize the configuration as if it were a file itself"""
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
        LOG.debug(f"Using env var {env_var}")
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
            _file_content = config_fd.read()
            if print_generated_config:
                LOG.info(_file_content)
            try:
                config = yaml.load(_file_content, Loader=Loader)
                LOG.info(f"Successfully loaded YAML config {config_path}")
            except yaml.YAMLError:
                try:
                    config = json.loads(_file_content)
                    LOG.info(f"Successfully loaded JSON config {config_path}")
                except json.JSONDecodeError:
                    LOG.error("Input content is not valid JSON")
                    raise
            finally:
                if print_generated_config:
                    LOG.info(jobs_input_def)
            return config

    except OSError as error:
        LOG.exception(error)
        LOG.error(f"Failed to read input file from {config_path}")


def process_files(job: input.Model, override_session=None) -> None:
    files: list = []
    for file_path, file in job.files.items():
        if not isinstance(file, File):
            file_redef = from_dict(
                data_class=File, data=asdict(file), config=Config(cast=[Enum, bytes])
            )
            file_redef.path = file_path
            files.append(file_redef)
        else:
            files.append(file)
    for file in files:
        file.handler(job.IamOverride, override_session)
        LOG.info(f"Tasks for {file.path} completed.")


def start_jobs(config: dict, override_session=None):
    """Starting point to run the files job"""
    job = from_dict(
        data_class=input.Model, data=config, config=Config(cast=[Enum, bytes])
    )
    if job.certificates:
        process_x509_certs(job)
    if job.files:
        process_files(job, override_session)
