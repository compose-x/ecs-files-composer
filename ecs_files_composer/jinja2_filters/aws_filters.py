# SPDX-License-Identifier: MPL-2.0
# Copyright 2020-2022 John Mille<john@compose-x.io>

"""
AWS Based filters
"""

from __future__ import annotations

from boto3.session import Session
from compose_x_common.compose_x_common import keyisset


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
