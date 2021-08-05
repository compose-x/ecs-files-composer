#  -*- coding: utf-8 -*-
# SPDX-License-Identifier: MPL-2.0
# Copyright 2020-2021 John Mille<john@compose-x.io>

"""AWS module."""

import re

import boto3
from boto3 import session
from botocore.exceptions import ClientError

from ecs_files_composer import input
from ecs_files_composer.common import LOG
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
        secret_id = expandvars(secret.secret_id)
        params = {"SecretId": secret_id}
        LOG.debug(f"Retrieving secretsmanager://{secret_id}")
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
