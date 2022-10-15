# SPDX-License-Identifier: MPL-2.0
# Copyright 2020-2022 John Mille<john@compose-x.io>

"""Main module."""

import base64
import os
import pathlib
import subprocess
import warnings
from os import path
from tempfile import TemporaryDirectory
from typing import Any

import jinja2.exceptions
import requests
from botocore.response import StreamingBody
from compose_x_common.compose_x_common import keyisset
from jinja2 import Environment, FileSystemLoader

from ecs_files_composer.aws_mgmt import S3Fetcher, SecretFetcher, SsmFetcher
from ecs_files_composer.common import LOG
from ecs_files_composer.envsubst import expandvars
from ecs_files_composer.input import Context, Encoding, FileDef, IgnoreFailureItem
from ecs_files_composer.jinja2_filters import JINJA_FILTERS, JINJA_FUNCTIONS


class File(FileDef):
    """
    Class to wrap common files actions around
    """

    def __init__(self, **data: Any):
        super().__init__(**data)
        self.templates_dir = None

    def handler(self, iam_override=None, session_override=None):
        """
        Main entrypoint for files to relate

        :param ecs_files_composer.input.IamOverrideDef iam_override:
        :param boto3.session.Session session_override:
        """
        if not path.exists(self.dir_path):
            print(f"Creating {self.dir_path} folder")
            dir_path = pathlib.Path(path.abspath(self.dir_path))
            dir_path.mkdir(parents=True, exist_ok=True)
        if self.commands and self.commands.pre:
            warnings.warn("Commands are not yet implemented", Warning)
        if (
            self.context
            and isinstance(self.context, Context)
            and self.context.value == "jinja2"
        ):
            self.templates_dir = TemporaryDirectory()
        if self.source and not self.content:
            retrieved, ignore = self.handle_sources(
                iam_override=iam_override, session_override=session_override
            )
            if not retrieved and ignore:
                LOG.warn(
                    f"Failed to fetch content for {self.path}. Ignoring all post processing."
                )
                return
            elif not retrieved and not ignore:
                raise Exception("Failed to retrieve content from source", self.path)
        self.files_content_processing()
        self.post_processing()

    def files_content_processing(self) -> None:

        if self.content and self.encoding and self.encoding == Encoding["base64"]:
            self.content = base64.b64decode(self.content).decode()
        if self.templates_dir:
            self.write_content(is_template=True)
            self.render_jinja()
        else:
            self.write_content(is_template=False)

    def post_processing(self):
        self.set_unix_settings()
        if self.commands and self.commands.post:
            self.exec_post_commands()

    @property
    def dir_path(self) -> str:
        return path.abspath(path.dirname(self.path))

    def handle_sources(
        self, iam_override=None, session_override=None
    ) -> tuple[bool, bool]:
        """
        Handles files from external sources

        :param ecs_files_composer.input.IamOverrideDef iam_override:
        :param boto3.session.Session session_override:
        """
        ignore_source_download_error = (
            self.ignore_failure
            if self.ignore_failure and isinstance(self.ignore_failure, bool)
            else False
        )
        if self.ignore_failure and isinstance(self.ignore_failure, IgnoreFailureItem):
            ignore_source_download_error = self.ignore_failure.source_download
        retrieved = False
        if self.source.url:
            retrieved = self.handle_url_source()
        elif self.source.ssm:
            retrieved = self.handle_ssm_source(iam_override, session_override)
        elif self.source.s3:
            retrieved = self.handle_s3_source(iam_override, session_override)
        elif self.source.secret:
            retrieved = self.handle_secret_source(iam_override, session_override)
        LOG.debug(
            f"Return from source for {self.path}: {retrieved}-{ignore_source_download_error}"
        )
        return retrieved, ignore_source_download_error

    def handle_ssm_source(self, iam_override=None, session_override=None) -> bool:
        """
        Handles retrieving the content from SSM Parameter

        :param ecs_files_composer.input.IamOverrideDef iam_override:
        :param boto3.session.Session session_override:
        :return:
        """
        parameter_name = expandvars(self.source.ssm.parameter_name)
        LOG.debug(f"Retrieving ssm://{parameter_name}")
        if self.source.ssm.iam_override:
            fetcher = SsmFetcher(iam_config_object=self.source.ssm.iam_override)
        elif iam_override:
            fetcher = SsmFetcher(iam_config_object=iam_override)
        elif session_override:
            fetcher = SsmFetcher(client_session_override=session_override)
        else:
            fetcher = SsmFetcher()
        try:
            self.content = fetcher.get_content(parameter_name=parameter_name)
            return True
        except Exception as error:
            LOG.error("Failed to retrieve file from AWS Systems Manager Parameter")
            LOG.error(error)
            return False

    def handle_s3_source(self, iam_override=None, session_override=None) -> bool:
        """
        Handles retrieving the content from S3

        :param ecs_files_composer.input.IamOverrideDef iam_override:
        :param boto3.session.Session session_override:
        :return: bool, result of the download from S3.
        """
        from ecs_files_composer.input import S3Def1

        if not isinstance(self.source.s3.__root__, S3Def1):
            raise TypeError(
                "S3 source is not of type S3Def1", type(self.source.s3.__root__)
            )

        if self.source.s3.__root__.iam_override:
            fetcher = S3Fetcher(iam_config_object=self.source.s3.__root__.iam_override)
        elif iam_override:
            fetcher = S3Fetcher(iam_config_object=iam_override)
        elif session_override:
            fetcher = S3Fetcher(client_session_override=session_override)
        else:
            fetcher = S3Fetcher()
        try:
            if self.source.s3.__root__.s3_uri:
                self.content = fetcher.get_content(
                    s3_uri=self.source.s3.__root__.s3_uri.__root__,
                )
            elif self.source.s3.__root__.compose_x_uri:
                self.content = fetcher.get_content(
                    composex_uri=self.source.s3.__root__.compose_x_uri.__root__,
                )
            else:
                bucket_name = expandvars(self.source.s3.__root__.bucket_name)
                key = expandvars(self.source.s3.__root__.key)
                self.content = fetcher.get_content(
                    s3_bucket=bucket_name,
                    s3_key=key,
                )
            return True
        except Exception as error:
            LOG.error("Failed to retrieve file from AWS S3")
            LOG.error(error)
            return False

    def handle_secret_source(self, iam_override=None, session_override=None) -> bool:
        """
        Handles retrieving secrets from AWS Secrets Manager

        :param ecs_files_composer.input.IamOverrideDef iam_override:
        :param boto3.session.Session session_override:
        :return:
        """
        if self.source.secret.iam_override:
            fetcher = SecretFetcher(iam_config_object=self.source.secret.iam_override)
        elif iam_override:
            fetcher = SecretFetcher(iam_config_object=iam_override)
        elif session_override:
            fetcher = SecretFetcher(client_session_override=session_override)
        else:
            fetcher = SecretFetcher()
        try:
            self.content = fetcher.get_content(self.source.secret)
            return True
        except Exception as error:
            LOG.error("Failed to retrieve file from AWS Secrets Manager")
            LOG.error(error)
            return False

    def handle_url_source(self) -> bool:
        """
        Fetches the content from a provided URI

        """
        if not self.source.url.username or not self.source.url.password:
            req = requests.get(self.source.url.url)
        else:
            req = requests.get(
                self.source.url.url,
                auth=(self.source.url.username, self.source.url.password),
            )
        try:
            req.raise_for_status()
            self.write_content(as_bytes=True, bytes_content=req.content)
            return True
        except requests.exceptions.HTTPError as error:
            LOG.error("Failed to retrieve file provided URL")
            LOG.error(error)
            return False

    def render_jinja(self):
        """
        Allows to use the temp directory as environment base, the original file as source template, and render
        a final template.
        """
        from os import listdir

        LOG.info(f"Rendering Jinja for {self.path} - {self.templates_dir.name}")
        jinja_env = Environment(
            loader=FileSystemLoader(self.templates_dir.name),
            autoescape=True,
            auto_reload=False,
        )
        jinja_env.filters.update(JINJA_FILTERS)
        jinja_env.globals.update(JINJA_FUNCTIONS)
        try:
            template = jinja_env.get_template(path.basename(self.path))
            self.content = template.render(env=os.environ)
            self.write_content(is_template=False)
        except jinja2.exceptions.TemplateNotFound:
            LOG.error(listdir(self.templates_dir.name))
            raise

    def set_unix_settings(self):
        """
        Applies UNIX settings to given file

        """
        ignore_mode_failure = (
            self.ignore_failure
            if self.ignore_failure and isinstance(self.ignore_failure, bool)
            else False
        )
        ignore_owner_failure = (
            self.ignore_failure
            if self.ignore_failure and isinstance(self.ignore_failure, bool)
            else False
        )
        if self.ignore_failure and isinstance(self.ignore_failure, IgnoreFailureItem):
            ignore_mode_failure = self.ignore_failure.mode
        if self.ignore_failure and isinstance(self.ignore_failure, IgnoreFailureItem):
            ignore_mode_failure = self.ignore_failure.owner

        cmd = ["chmod", self.mode, self.path]
        LOG.debug(f"{self.path} - {cmd}")
        try:
            res = subprocess.run(
                cmd,
                text=True,
                capture_output=True,
                shell=False,
            )
        except subprocess.CalledProcessError as error:
            if ignore_mode_failure:
                LOG.error(error)
            else:
                raise
        cmd = ["chown", f"{self.owner}:{self.group}", self.path]
        LOG.debug(f"{self.path} - {cmd}")
        try:
            res = subprocess.run(
                cmd,
                text=True,
                capture_output=True,
                shell=False,
            )
        except subprocess.CalledProcessError as error:
            if ignore_owner_failure:
                LOG.error(error)
            else:
                raise

    def exec_post_commands(self):

        ignore_post_command_failure = (
            self.ignore_failure
            if self.ignore_failure and isinstance(self.ignore_failure, bool)
            else False
        )
        if self.ignore_failure and isinstance(self.ignore_failure, IgnoreFailureItem):
            ignore_post_command_failure = self.ignore_failure.commands
        commands = self.commands.post.__root__
        for command in commands:
            cmd = command
            if isinstance(command, str):
                cmd = command.split(" ")
            LOG.info(f"{self.path} - {cmd}")
            try:
                res = subprocess.run(
                    cmd,
                    text=True,
                    capture_output=True,
                    shell=False,
                )
            except subprocess.CalledProcessError as error:
                if ignore_post_command_failure:
                    LOG.error(error)
                else:
                    raise

    def write_content(self, is_template=True, as_bytes=False, bytes_content=None):
        """
        Function to write the content retrieved to path.

        :param bool is_template: Whether the content should be considered to be a template.
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
            with open(file_path, "w") as file_fd:
                file_fd.write(self.content)
        elif isinstance(self.content, StreamingBody):
            with open(file_path, "wb") as file_fd:
                file_fd.write(self.content.read())
        elif as_bytes and bytes_content:
            with open(file_path, "wb") as file_fd:
                file_fd.write(bytes_content)
