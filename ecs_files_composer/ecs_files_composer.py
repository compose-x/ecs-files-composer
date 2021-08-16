#  -*- coding: utf-8 -*-
# SPDX-License-Identifier: MPL-2.0
# Copyright 2020-2021 John Mille<john@compose-x.io>

"""Main module."""

import json
from os import environ, path

import yaml
from compose_x_common.compose_x_common import keyisset
from yaml import Loader

from ecs_files_composer import input
from ecs_files_composer.aws_mgmt import S3Fetcher, SecretFetcher, SsmFetcher
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
    :return: The ECS Config description
    :rtype: dict
    """
    if ssm_parameter or s3_config or secret_config:
        role_arn = environ.get("CONFIG_IAM_ROLE_ARN", role_arn)
        external_id = environ.get("CONFIG_IAM_EXTERNAL_ID", None)
    if ssm_parameter:
        config_client = SsmFetcher(role_arn, external_id)
        config_content = config_client.get_content(ssm_parameter)
    elif s3_config:
        config_client = S3Fetcher(role_arn, external_id)
        config_content = config_client.get_content(s3_uri=s3_config).read()
    elif secret_config:
        config_client = SecretFetcher(role_arn, external_id)
        config_content = config_client.get_content(
            input.SecretDef(SecretId=secret_config)
        )
    elif file_path:
        with open(path.abspath(file_path), "r") as file_fd:
            config_content = file_fd.read()
    elif raw:
        config_content = raw
    elif env_var:
        config_content = environ.get(env_var, None)
    else:
        raise Exception("No input source was provided")
    if not config_content:
        raise ImportError("Failed to import a configuration content")
    LOG.debug(config_content)
    try:
        config = yaml.load(config_content, Loader=Loader)
    except yaml.YAMLError:
        config = json.loads(config_content)
    except Exception:
        LOG.error("Input content is neither JSON nor YAML formatted")
        raise
    LOG.debug(config)
    return config


def start_jobs(config):
    """
    Starting point to run the files job

    :param config:
    :return:
    """
    if not keyisset("files", config):
        raise KeyError("Missing required files from configuration input")
    job = input.Model(files=config["files"]).parse_obj(config)
    process_x509_certs(job)
    for file_path, file in job.files.items():
        if not isinstance(file, File):
            file_def = File().parse_obj(file)
            job.files[file_path] = file_def
            file_def.path = file_path
    for file in job.files.values():
        file.handler(job.iam_override)
        LOG.info(f"Tasks for {file.path} completed.")
