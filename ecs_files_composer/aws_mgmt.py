# SPDX-License-Identifier: MPL-2.0
# Copyright 2020-2022 John Mille<john@compose-x.io>

"""AWS module."""

import re

import boto3
from boto3.session import Session
from botocore.exceptions import ClientError

from ecs_files_composer import input
from ecs_files_composer.common import LOG
from ecs_files_composer.envsubst import expandvars


def create_session_from_creds(tmp_creds: dict, region: str = None):
    """
    Function to easily convert the AssumeRole reply into a boto3 session
    :param tmp_creds:
    :return:
    :rtype boto3.session.Session
    """
    creds = tmp_creds["Credentials"]
    params = {
        "aws_AccessKeyId": creds["AccessKeyId"],
        "aws_SecretAccessKey": creds["SecretAccessKey"],
        "aws_session_token": creds["SessionToken"],
    }
    if region:
        params["RegionName"] = region
    return boto3.session.Session(**params)


def set_session_from_iam_object(iam_config_object, source_session: Session = None):
    """
    Function to define the client session based on config input

    :param ecs_files_composer.input.IamOverrideDef iam_config_object:
    :param source_session:
    :return: boto session
    :rtype: boto3.session.Session
    """
    if source_session is None:
        source_session = boto3.Session()
    if not iam_config_object.AccessKeyId and not iam_config_object.SecretAccessKey:
        params = {
            "RoleArn": iam_config_object.RoleArn,
            "RoleSessionName": f"{iam_config_object.SessionName}@AwsResourceHandlerInit",
        }
        if iam_config_object.ExternalId:
            params["ExternalId"] = iam_config_object.ExternalId
        tmp_creds = source_session.client("sts").assume_role(**params)
        client_session = create_session_from_creds(
            tmp_creds, region=iam_config_object.RegionName
        )
    else:
        client_session = boto3.session.Session(
            aws_access_key_id=iam_config_object.AccessKeyId,
            aws_secret_access_key=iam_config_object.SecretAccessKey,
            aws_session_token=(
                iam_config_object.SessionToken
                if iam_config_object.SessionToken
                else None
            ),
        )
    return client_session


class AwsResourceHandler:
    """
    Class to handle all AWS related credentials init.
    """

    def __init__(
        self,
        RoleArn=None,
        ExternalId=None,
        region=None,
        iam_config_object=None,
        client_session_override=None,
    ):
        """
        :param str RoleArn:
        :param str ExternalId:
        :param str region:
        :param ecs_files_composer.input.IamOverrideDef iam_config_object:
        """
        self.session = Session()
        self.client_session = Session()
        if client_session_override:
            self.client_session = client_session_override
        elif not client_session_override and (RoleArn or iam_config_object):
            if RoleArn and not iam_config_object:
                params = {
                    "RoleArn": RoleArn,
                    "RoleSessionName": "EcsConfigComposer@AwsResourceHandlerInit",
                }
                if ExternalId:
                    params["ExternalId"] = ExternalId
                tmp_creds = self.session.client("sts").assume_role(**params)
                self.client_session = create_session_from_creds(
                    tmp_creds, region=region
                )
            elif (
                iam_config_object
                and hasattr(iam_config_object, "RoleArn")
                and iam_config_object.RoleArn
            ):
                self.client_session = set_session_from_iam_object(
                    iam_config_object, self.session
                )


class S3Fetcher(AwsResourceHandler):
    """
    Class to handle S3 actions
    """

    bucket_re = re.compile(r"^s3://(?P<bucket>[a-zA-Z\d\-.]+)/(?P<key>[\S]+)$")
    compose_x_re = re.compile(r"^(?P<bucket>[a-zA-Z\d\-.]+)::(?P<key>[\S]+)$")

    def __init__(
        self,
        RoleArn=None,
        ExternalId=None,
        region=None,
        iam_config_object=None,
        client_session_override=None,
    ):
        super().__init__(
            RoleArn, ExternalId, region, iam_config_object, client_session_override
        )

    @property
    def client(self):
        return self.client_session.client("s3")

    def get_content(
        self,
        s3_uri: str = None,
        s3_bucket: str = None,
        s3_key: str = None,
        composex_uri: str = None,
    ):
        """
        Retrieves a file in a temp dir and returns content

        :return: The Stream Body for the file, allowing to do various things
        """

        if s3_uri and self.bucket_re.match(s3_uri):
            s3_bucket = self.bucket_re.match(s3_uri).group("bucket")
            s3_key = self.bucket_re.match(s3_uri).group("key")
        elif composex_uri and self.compose_x_re.match(composex_uri):
            s3_bucket = self.compose_x_re.match(composex_uri).group("bucket")
            s3_key = self.compose_x_re.match(composex_uri).group("key")
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

    arn_re = re.compile(
        r"^arn:aws(?:-[a-z]+)?:ssm:[\S]+:[\d]{12}:parameter(?P<name>/[\S]+)$"
    )

    def __init__(
        self,
        RoleArn=None,
        ExternalId=None,
        region=None,
        iam_config_object=None,
        client_session_override=None,
    ):
        super().__init__(
            RoleArn, ExternalId, region, iam_config_object, client_session_override
        )
        self.client = self.client_session.client("ssm")

    def get_content(self, parameter_name):
        """
        Import the Content of a given parameter
        If the parameter name is a valid ARN, parses and uses the name from ARN

        :param parameter_name:
        :return:
        """
        if self.arn_re.match(parameter_name):
            parameter_name = self.arn_re.match(parameter_name).group("name")
        parameter = self.client.get_parameter(Name=parameter_name, WithDecryption=True)
        return parameter["Parameter"]["Value"]


class SecretFetcher(AwsResourceHandler):
    """
    Class to handle Secret Manager actions
    """

    def __init__(
        self,
        RoleArn=None,
        ExternalId=None,
        region=None,
        iam_config_object=None,
        client_session_override=None,
    ):
        super().__init__(
            RoleArn, ExternalId, region, iam_config_object, client_session_override
        )
        self.client = self.client_session.client("secretsmanager")

    def get_content(self, secret):
        """
        Import the Content of a given parameter

        :param input.SecretDef secret:
        :return:
        """
        secret_id = expandvars(secret.SecretId)
        params = {"SecretId": secret_id}
        LOG.debug(f"Retrieving secretsmanager://{secret_id}")
        if secret.VersionId:
            params["VersionId"] = secret.VersionId
        if secret.VersionStage:
            params["VersionStage"] = secret.VersionStage

        parameter = self.client.get_secret_value(**params)
        return parameter["SecretString"]
