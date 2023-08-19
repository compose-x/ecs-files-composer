# SPDX-License-Identifier: MPL-2.0
# Copyright 2020-2022 John Mille<john@compose-x.io>

"""
AWS Based Functions
"""

from __future__ import annotations

import json
from os import environ

import requests
from aws_cfn_custom_resource_resolve_parser import handle
from boto3.session import Session
from botocore.exceptions import ClientError
from compose_x_common.compose_x_common import keyisset

from ecs_files_composer.jinja2_filters import get_property

from .aws_tools import get_ec2_subnet_from_vpc_and_ip_cidr


def define_ecs_metadata(for_task=False):
    meta_v4 = "ECS_CONTAINER_METADATA_URI_V4"
    meta_v3 = "ECS_CONTAINER_METADATA_URI"

    if environ.get(meta_v4, None):
        meta_url = environ.get(meta_v4)
    elif environ.get(meta_v3, None):
        meta_url = environ.get(meta_v3)
    else:
        raise OSError("No ECS Metadata URL provided. This filter only works on ECS")
    if for_task:
        return requests.get(f"{meta_url}/task")
    else:
        return requests.get(meta_url)


def msk_bootstrap(msk_arn: str, broker_type: str) -> str:
    """
    Uses the ARN of a MSK cluster,
    and returns the list of BootStrap endpoints for a private MSK cluster using SASL IAM.
    If failed, returns the ARN.
    """
    session = Session()
    client = session.client("kafka")
    brokers_r = client.get_bootstrap_brokers(ClusterArn=msk_arn)
    if keyisset(broker_type, brokers_r):
        return brokers_r[broker_type]
    return msk_arn


def from_ssm_json(parameter_name: str) -> dict:
    """
    Function to retrieve an SSM parameter value

    :param parameter_name: Name of the parameter
    """
    value_str = (
        Session()
        .client("ssm")
        .get_parameter(Name=parameter_name, WithDecryption=True)["Parameter"]["Value"]
    )
    try:
        return json.loads(value_str)
    except json.JSONDecodeError:
        return {}


def from_ssm(parameter_name: str) -> str:
    """
    Function to retrieve an SSM parameter value

    :param parameter_name: Name of the parameter
    """
    return (
        Session()
        .client("ssm")
        .get_parameter(Name=parameter_name, WithDecryption=True)["Parameter"]["Value"]
    )


def ecs_container_metadata(property_key=None, fallback_value=None):
    metadata_raw = define_ecs_metadata()
    metadata = metadata_raw.json()
    if property_key:
        value = get_property(metadata, property_key)
        if value is None:
            print(f"No task property found matching {property_key}")
            return fallback_value
        return value
    return metadata


def ecs_task_metadata(property_key=None, fallback_value=None):
    metadata_raw = define_ecs_metadata(for_task=True)
    metadata = metadata_raw.json()
    if property_key:
        value = get_property(metadata, property_key)
        if value is None:
            print(f"No task property found matching {property_key}")
            return fallback_value
        return value
    return metadata


def using_resolve(resolve_string: str) -> str:
    return handle(resolve_string)


def ec2_zone_id(subnet_id: str = None):
    """
    Defines which AWS ZoneID the container is into based on the subnet if provided, otherwise using EC2 Region API
    """
    session = Session()
    if not subnet_id:
        vpc_id = ecs_task_metadata("VPCID")
        subnet_range = ecs_task_metadata("Networks::0::IPv4SubnetCIDRBlock")
        subnet_details = get_ec2_subnet_from_vpc_and_ip_cidr(
            vpc_id, subnet_range, session
        )
        return subnet_details["AvailabilityZoneId"]
    elif subnet_id:
        ec2_client = session.client("ec2")
        try:
            subnet_r = ec2_client.describe_subnets(SubnetIds=[subnet_id])
            return subnet_r["Subnets"][0]["AvailabilityZoneId"]
        except ClientError as error:
            print("Failed to retrieve ZoneID from Subnet API call", error)
    print("Unable to find subnet using API calls")
    return ""


def dump_ecs_details():
    print("Dumping ECS Details")
    print("ECS Container Metadata: ", ecs_container_metadata)
    print("ECS Task Metadata: ", ecs_task_metadata)
    vpc_id = ecs_task_metadata("VPCID")
    subnet_range = ecs_task_metadata("Networks::0::IPv4SubnetCIDRBlock")
    subnet_details = get_ec2_subnet_from_vpc_and_ip_cidr(
        vpc_id, subnet_range, Session()
    )
    print("Container subnet details: ", subnet_details)
