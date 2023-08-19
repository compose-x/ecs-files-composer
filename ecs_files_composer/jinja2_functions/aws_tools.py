# SPDX-License-Identifier: MPL-2.0
# Copyright 2020-2022 John Mille<john@compose-x.io>

"""Tools for AWS Functions / Filters"""

from __future__ import annotations

from boto3.session import Session
from botocore.exceptions import ClientError
from compose_x_common.aws import get_session


def get_ec2_subnet_from_vpc_and_ip_cidr(
    vpc_id: str, ip_cidr: str, session: Session = None
) -> dict:
    """Function to get the Subnet details from the VPC ID and the subnet CIDR"""
    session = get_session(session)
    client = session.client("ec2")
    try:
        subnets_r = client.describe_subnets(
            Filters=[
                {"Name": "vpc-id", "Values": [vpc_id]},
                {"Name": "cidr-block", "Values": [ip_cidr]},
            ]
        )
        return subnets_r["Subnets"][0]
    except ClientError as error:
        print("Failed to retrieve Subnet from VPC ID and CIDR", error)
        return {}
    except Exception as error:
        print("An exception occurred", error)
        raise
