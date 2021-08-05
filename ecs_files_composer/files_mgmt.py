#  -*- coding: utf-8 -*-
# SPDX-License-Identifier: MPL-2.0
# Copyright 2020-2021 John Mille<john@compose-x.io>

"""Main module."""

import base64
import subprocess
import warnings
from os import path
from tempfile import TemporaryDirectory
from typing import Any

import requests
from botocore.response import StreamingBody
from jinja2 import Environment, FileSystemLoader

from ecs_files_composer.aws_mgmt import S3Fetcher, SecretFetcher, SsmFetcher
from ecs_files_composer.common import LOG
from ecs_files_composer.envsubst import expandvars
from ecs_files_composer.input import Context, Encoding, FileDef
from ecs_files_composer.jinja2_filters import env


class File(FileDef, object):
    """
    Class to wrap common files actions around
    """

    def __init__(self, iam_override=None, **data: Any):
        super().__init__(**data)
        self.templates_dir = None

    def handler(self, iam_override):
        """
        Main entrypoint for files to relate

        :param ecs_files_composer.input.IamOverrideDef iam_override:
        :return:
        """
        if self.context and isinstance(self.context, Context) and self.context.value == "jinja2":
            self.templates_dir = TemporaryDirectory()
        if self.commands and self.commands.pre:
            warnings.warn("Commands are not yet implemented", Warning)
        if self.source and not self.content:
            self.handle_sources(iam_override=iam_override)
            self.write_content()
        if not self.source and self.content:
            self.write_content(decode=True)
        if self.templates_dir:
            self.render_jinja()
        self.set_unix_settings()
        if self.commands and self.commands.post:
            warnings.warn("Commands are not yet implemented", Warning)

    def handle_sources(self, iam_override=None):
        """
        Handles files from external sources

        :param ecs_files_composer.input.IamOverrideDef iam_override:
        :return:
        """
        if self.source.url:
            self.handle_http_content()
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

        :param ecs_files_composer.input.IamOverrideDef iam_override:
        :return:
        """
        parameter_name = expandvars(self.source.ssm.parameter_name)
        LOG.debug(f"Retrieving ssm://{parameter_name}")
        if self.source.ssm.iam_override:
            fetcher = SsmFetcher(iam_config_object=self.source.ssm.iam_override)
        else:
            fetcher = SsmFetcher(iam_config_object=iam_override)
        self.content = fetcher.get_content(parameter_name=parameter_name)

    def handle_s3_source(self, iam_override=None):
        """
        Handles retrieving the content from S3

        :param ecs_files_composer.input.IamOverrideDef iam_override:
        :return:
        """
        bucket_name = expandvars(self.source.s3.bucket_name)
        key = expandvars(self.source.s3.key)
        LOG.debug(f"Retrieving s3://{bucket_name}/{key}")
        if self.source.s3.iam_override:
            fetcher = S3Fetcher(iam_config_object=self.source.s3.iam_override)
        else:
            fetcher = S3Fetcher(iam_config_object=iam_override)
        self.content = fetcher.get_content(s3_bucket=bucket_name, s3_key=key)

    def handle_secret_source(self, iam_override=None):
        """
        Handles retrieving secrets from AWS Secrets Manager

        :param ecs_files_composer.input.IamOverrideDef iam_override:
        :return:
        """
        if self.source.secret.iam_override:
            fetcher = SecretFetcher(iam_config_object=self.source.secret.iam_override)
        else:
            fetcher = SecretFetcher(iam_config_object=iam_override)
        self.content = fetcher.get_content(self.source.secret)

    def handle_http_content(self):
        """
        Fetches the content from a provided URI

        """
        if not self.source.url.username or not self.source.url.password:
            req = requests.get(self.source.url.url)
        else:
            req = requests.get(self.source.url.url, auth=(self.source.url.username, self.source.url.password))
        try:
            req.raise_for_status()
            self.write_content(as_bytes=True, bytes_content=req.content)
        except requests.exceptions.HTTPError as e:
            LOG.error(e)
            raise

    def render_jinja(self):
        """
        Allows to use the temp directory as environment base, the original file as source template, and render
        a final template.
        """
        jinja_env = Environment(loader=FileSystemLoader(self.templates_dir.name), autoescape=True, auto_reload=False)
        jinja_env.filters['env_override'] = env
        template = jinja_env.get_template(path.basename(self.path))
        self.content = template.render()
        self.write_content(is_template=False)

    def set_unix_settings(self):
        """
        Applies UNIX settings to given file

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

    def write_content(self, is_template=True, decode=False, as_bytes=False, bytes_content=None):
        """
        Function to write the content retrieved to path.

        :param bool is_template: Whether the content should be considered to be a template.
        :param decode:
        :param as_bytes:
        :param bytes_content:
        :return:
        """
        file_path = (
            f"{self.templates_dir.name}/{path.basename(self.path)}"
            if (self.templates_dir and is_template)
            else self.path
        )
        LOG.info(f"Outputting {self.path} to {file_path}")
        if isinstance(self.content, str):
            if decode and self.encoding == Encoding["base64"]:
                with open(file_path, "wb") as file_fd:
                    file_fd.write(base64.b64decode(self.content))
            else:
                with open(file_path, "w") as file_fd:
                    file_fd.write(self.content)
        elif isinstance(self.content, StreamingBody):
            with open(file_path, "wb") as file_fd:
                file_fd.write(self.content.read())
        elif as_bytes and bytes_content:
            with open(file_path, "wb") as file_fd:
                file_fd.write(bytes_content)
