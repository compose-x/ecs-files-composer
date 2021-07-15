#  -*- coding: utf-8 -*-
# SPDX-License-Identifier: MPL-2.0
# Copyright 2020-2021 John Mille<john@compose-x.io>

"""Main module."""

import base64
import json
import re
import subprocess
import tempfile
import warnings
from os import environ, path
from typing import Any

import boto3
import yaml
from boto3 import client, session
from botocore.exceptions import ClientError
from botocore.response import StreamingBody
from yaml import Dumper, Loader

from ecs_files_composer import input
from ecs_files_composer.chmod import chmod
from ecs_files_composer.common import LOG, keyisset, keypresent
from ecs_files_composer.envsubst import expandvars


def create_session_from_creds(tmp_creds, region=None):
    """
    Function to easily convert the AssumeRole reply into a boto3 session
    :param tmp_creds:
    :return:
    :rtype boto3.session.Session
    """
    creds = tmp_creds["Credentials"]
    params = {
        "aws_access_key_id": creds["AccessKeyId"],
        "aws_secret_access_key": creds["SecretAccessKey"],
        "aws_session_token": creds["SessionToken"],
    }
    if region:
        params["region_name"] = region
    return boto3.session.Session(**params)


class AwsResourceHandler(object):
    """
    Class to handle all AWS related credentials init.
    """

    def __init__(self, role_arn=None, external_id=None, region=None, iam_config_object=None):
        """
        :param str role_arn:
        :param str external_id:
        :param str region:
        :param ecs_files_composer.input.IamOverrideDef iam_config_object:
        """
        self.session = session.Session()
        self.client_session = session.Session()
        if role_arn or iam_config_object:
            if role_arn and not iam_config_object:
                params = {"RoleArn": role_arn, "RoleSessionName": "EcsConfigComposer@AwsResourceHandlerInit"}
                if external_id:
                    params["ExternalId"] = external_id
                tmp_creds = self.session.client("sts").assume_role(**params)
                self.client_session = create_session_from_creds(tmp_creds, region=region)
            elif iam_config_object:
                params = {
                    "RoleArn": iam_config_object.role_arn,
                    "RoleSessionName": f"{iam_config_object.session_name}@AwsResourceHandlerInit",
                }
                if iam_config_object.external_id:
                    params["ExternalId"] = iam_config_object.external_id
                tmp_creds = self.session.client("sts").assume_role(**params)
                self.client_session = create_session_from_creds(tmp_creds, region=iam_config_object.region_name)


class S3Fetcher(AwsResourceHandler):
    """
    Class to handle S3 actions
    """

    def __init__(self, role_arn=None, external_id=None, region=None, iam_config_object=None):
        super().__init__(role_arn, external_id, region, iam_config_object)
        self.client = self.client_session.client("s3")

    def get_content(self, s3_uri=None, s3_bucket=None, s3_key=None):
        """
        Retrieves a file in a temp dir and returns content

        :param str s3_uri:
        :param str s3_bucket:
        :param str s3_key:
        :return: The Stream Body for the file, allowing to do various things
        """
        bucket_re = re.compile(r"(?:s3://)(?P<bucket>[a-z0-9-.]+)/(?P<key>[\S]+$)")
        if s3_uri and bucket_re.match(s3_uri).groups():
            s3_bucket = bucket_re.match(s3_uri).group("bucket")
            s3_key = bucket_re.match(s3_uri).group("key")
        try:
            file_r = self.client.get_object(Bucket=s3_bucket, Key=s3_key)
            file_content = file_r["Body"]
            return file_content
        except self.client.exceptions.NoSuchKey:
            LOG.error(f"Failed to download the file {s3_key} from bucket {s3_bucket}")
            raise


class SsmFetcher(AwsResourceHandler):
    """
    Class to handle SSM actions
    """

    def __init__(self, role_arn=None, external_id=None, region=None, iam_config_object=None):
        super().__init__(role_arn, external_id, region, iam_config_object)
        self.client = self.client_session.client("ssm")

    def get_content(self, parameter_name):
        """
        Import the Content of a given parameter

        :param parameter_name:
        :return:
        """
        try:
            parameter = self.client.get_parameter(Name=parameter_name, WithDecryption=True)
            return parameter["Parameter"]["Value"]
        except self.client.exceptions:
            raise
        except ClientError:
            raise


class SecretFetcher(AwsResourceHandler):
    """
    Class to handle Secret Manager actions
    """

    def __init__(self, role_arn=None, external_id=None, region=None, iam_config_object=None):
        super().__init__(role_arn, external_id, region, iam_config_object)
        self.client = self.client_session.client("secretsmanager")

    def get_content(self, secret):
        """
        Import the Content of a given parameter

        :param input.SecretDef secret:
        :return:
        """
        params = {"SecretId": expandvars(secret.secret_id)}
        if secret.version_id:
            params["VersionId"] = secret.version_id
        if secret.version_stage:
            params["VersionStage"] = secret.version_stage
        try:
            parameter = self.client.get_secret_value(**params)
            return parameter["SecretString"]
        except self.client.exceptions:
            raise
        except ClientError:
            raise


class File(input.FileDef, object):
    """
    Class to wrap common files actions around
    """

    def __init__(self, iam_override=None, **data: Any):
        super().__init__(**data)

    def handler(self, iam_override):
        """
        Main entrypoint for files to relate

        :param input.IamOverrideDef iam_override:
        :return:
        """
        if self.commands and self.commands.pre:
            warnings.warn("Commands are not yet implemented", Warning)
        if self.source and not self.content:
            self.handle_sources(iam_override=iam_override)
            self.write_content()
        if not self.source and self.content:
            self.write_content(decode=True)
        self.set_unix_settings()
        if self.commands and self.commands.post:
            warnings.warn("Commands are not yet implemented", Warning)

    def handle_sources(self, iam_override=None):
        """
        Handles files from external sources

        :param input.IamOverrideDef iam_override:
        :return:
        """
        if self.source.url:
            pass
        elif self.source.ssm:
            self.handle_ssm_source(iam_override)
        elif self.source.s3:
            self.handle_s3_source(iam_override)
        elif self.source.secret:
            LOG.warn("When using ECS, we recommend to use the Secrets in Task Definition")
            self.handle_secret_source(iam_override)

    def handle_url_source(self):
        """
        Handles retrieving files from URLs
        :return:
        """

    def handle_ssm_source(self, iam_override=None):
        """
        Handles retrieving the content from SSM Parameter

        :param input.IamOverrideDef iam_override:
        :return:
        """
        parameter_name = expandvars(self.source.ssm.parameter_name)
        if self.source.ssm.iam_override:
            fetcher = SsmFetcher(iam_config_object=self.source.ssm.iam_override)
        else:
            fetcher = SsmFetcher(iam_config_object=iam_override)
        self.content = fetcher.get_content(parameter_name=parameter_name)

    def handle_s3_source(self, iam_override=None):
        """
        Handles retrieving the content from S3

        :param input.IamOverrideDef iam_override:
        :return:
        """
        bucket_name = expandvars(self.source.s3.bucket_name)
        key = expandvars(self.source.s3.key)
        if self.source.s3.iam_override:
            fetcher = S3Fetcher(iam_config_object=self.source.s3.iam_override)
        else:
            fetcher = S3Fetcher(iam_config_object=iam_override)
        self.content = fetcher.get_content(s3_bucket=bucket_name, s3_key=key)

    def handle_secret_source(self, iam_override=None):
        """
        Handles retrieving secrets from AWS Secrets Manager

        :param input.IamOverrideDef iam_override:
        :return:
        """
        if self.source.secret.iam_override:
            fetcher = SecretFetcher(iam_config_object=self.source.secret.iam_override)
        else:
            fetcher = SecretFetcher(iam_config_object=iam_override)
        self.content = fetcher.get_content(self.source.secret)

    def set_unix_settings(self):
        """
        Applies UNIX settings to given file
        :return:
        """
        cmd = ["chmod", self.mode, self.path]
        try:
            res = subprocess.run(
                cmd, universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False
            )
        except subprocess.CalledProcessError:
            if self.ignore_if_failed:
                LOG.error(res.stderr)
            else:
                raise
        cmd = ["chown", f"{self.owner}:{self.group}", self.path]
        try:
            res = subprocess.run(
                cmd, universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False
            )
        except subprocess.CalledProcessError:
            if self.ignore_if_failed:
                LOG.error(res.stderr)
            else:
                raise

    def write_content(self, decode=False):
        if isinstance(self.content, str):
            if decode and self.encoding == input.Encoding["base64"]:
                with open(self.path, "wb") as file_fd:
                    file_fd.write(base64.b64decode(self.content))
            else:
                with open(self.path, "w") as file_fd:
                    file_fd.write(self.content)
        elif isinstance(self.content, StreamingBody):
            with open(self.path, "wb") as file_fd:
                file_fd.write(self.content.read())


def init_config(
    raw=None, file_path=None, env_var=None, ssm_parameter=None, s3_config=None, role_arn=None, external_id=None
):
    """
    Function to initialize the configuration

    :param raw: The raw content of a content
    :param str file_path: The path to a job configuration file
    :param str env_var:
    :param str ssm_parameter:
    :param str s3_config:
    :param str role_arn:
    :param str external_id:
    :return: The ECS Config description
    :rtype: dict
    """
    if ssm_parameter or s3_config:
        role_arn = environ.get("CONFIG_IAM_ROLE_ARN", role_arn)
        external_id = environ.get("CONFIG_IAM_EXTERNAL_ID", None)
    if ssm_parameter:
        config_client = SsmFetcher(role_arn, external_id)
        config_content = config_client.get_content(ssm_parameter)
    elif s3_config:
        config_client = S3Fetcher(role_arn, external_id)
        config_content = config_client.get_content(s3_uri=s3_config).read()
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
    try:
        config = yaml.load(config_content, Loader=Loader)
    except yaml.YAMLError:
        config = json.loads(config_content)
    except Exception:
        LOG.error("Input content is neither JSON nor YAML formatted")
        raise
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
    for file_path, file in job.files.items():
        file_def = File().parse_obj(file)
        job.files[file_path] = file_def
        file_def.path = file_path
    for file in job.files.values():
        file.handler(job.iam_override)
        LOG.info(f"Tasks for {file.path} completed.")
