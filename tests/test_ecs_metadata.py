#!/usr/bin/env python
#  -*- coding: utf-8 -*-
# SPDX-License-Identifier: MPL-2.0
# Copyright 2020-2021 John Mille<john@compose-x.io>

import json
import uuid
from base64 import b64encode
from os import path

import boto3.session
import pytest

from ecs_files_composer import input
from ecs_files_composer.ecs_files_composer import start_jobs

HERE = path.abspath(path.dirname(__file__))

test_container = {
    "DockerId": "cd189a933e5849daa93386466019ab50-2495160603",
    "Name": "curl",
    "DockerName": "curl",
    "Image": "111122223333.dkr.ecr.us-west-2.amazonaws.com/curltest:latest",
    "ImageID": "sha256:25f3695bedfb454a50f12d127839a68ad3caf91e451c1da073db34c542c4d2cb",
    "Labels": {
        "com.amazonaws.ecs.cluster": "arn:aws:ecs:us-west-2:111122223333:cluster/default",
        "com.amazonaws.ecs.container-name": "curl",
        "com.amazonaws.ecs.task-arn": "arn:aws:ecs:us-west-2:111122223333:task/default/cd189a933e5849daa93386466019ab50",
        "com.amazonaws.ecs.task-definition-family": "curltest",
        "com.amazonaws.ecs.task-definition-version": "2",
    },
    "DesiredStatus": "RUNNING",
    "KnownStatus": "RUNNING",
    "Limits": {"CPU": 10, "Memory": 128},
    "CreatedAt": "2020-10-08T20:09:11.44527186Z",
    "StartedAt": "2020-10-08T20:09:11.44527186Z",
    "Type": "NORMAL",
    "Networks": [
        {
            "NetworkMode": "awsvpc",
            "IPv4Addresses": ["192.0.2.3"],
            "AttachmentIndex": 0,
            "MACAddress": "0a:de:f6:10:51:e5",
            "IPv4SubnetCIDRBlock": "192.0.2.0/24",
            "DomainNameServers": ["192.0.2.2"],
            "DomainNameSearchList": ["us-west-2.compute.internal"],
            "PrivateDNSName": "ip-10-0-0-222.us-west-2.compute.internal",
            "SubnetGatewayIpv4Address": "192.0.2.0/24",
        }
    ],
    "ContainerARN": "arn:aws:ecs:us-west-2:111122223333:container/05966557-f16c-49cb-9352-24b3a0dcd0e1",
    "LogOptions": {
        "awslogs-create-group": "true",
        "awslogs-group": "/ecs/containerlogs",
        "awslogs-region": "us-west-2",
        "awslogs-stream": "ecs/curl/cd189a933e5849daa93386466019ab50",
    },
    "LogDriver": "awslogs",
}

test_task = {
    "Cluster": "arn:aws:ecs:us-west-2:111122223333:cluster/default",
    "TaskARN": "arn:aws:ecs:us-west-2:111122223333:task/default/e9028f8d5d8e4f258373e7b93ce9a3c3",
    "Family": "curltest",
    "Revision": "3",
    "DesiredStatus": "RUNNING",
    "KnownStatus": "RUNNING",
    "Limits": {"CPU": 0.25, "Memory": 512},
    "PullStartedAt": "2020-10-08T20:47:16.053330955Z",
    "PullStoppedAt": "2020-10-08T20:47:19.592684631Z",
    "AvailabilityZone": "us-west-2a",
    "Containers": [
        {
            "DockerId": "e9028f8d5d8e4f258373e7b93ce9a3c3-2495160603",
            "Name": "curl",
            "DockerName": "curl",
            "Image": "111122223333.dkr.ecr.us-west-2.amazonaws.com/curltest:latest",
            "ImageID": "sha256:25f3695bedfb454a50f12d127839a68ad3caf91e451c1da073db34c542c4d2cb",
            "Labels": {
                "com.amazonaws.ecs.cluster": "arn:aws:ecs:us-west-2:111122223333:cluster/default",
                "com.amazonaws.ecs.container-name": "curl",
                "com.amazonaws.ecs.task-arn": "arn:aws:ecs:us-west-2:111122223333:task/default/e9028f8d5d8e4f258373e7b93ce9a3c3",
                "com.amazonaws.ecs.task-definition-family": "curltest",
                "com.amazonaws.ecs.task-definition-version": "3",
            },
            "DesiredStatus": "RUNNING",
            "KnownStatus": "RUNNING",
            "Limits": {"CPU": 10, "Memory": 128},
            "CreatedAt": "2020-10-08T20:47:20.567813946Z",
            "StartedAt": "2020-10-08T20:47:20.567813946Z",
            "Type": "NORMAL",
            "Networks": [
                {
                    "NetworkMode": "awsvpc",
                    "IPv4Addresses": ["192.0.2.3"],
                    "IPv6Addresses": ["2001:dB8:10b:1a00:32bf:a372:d80f:e958"],
                    "AttachmentIndex": 0,
                    "MACAddress": "02:b7:20:19:72:39",
                    "IPv4SubnetCIDRBlock": "192.0.2.0/24",
                    "IPv6SubnetCIDRBlock": "2600:1f13:10b:1a00::/64",
                    "DomainNameServers": ["192.0.2.2"],
                    "DomainNameSearchList": ["us-west-2.compute.internal"],
                    "PrivateDNSName": "ip-172-31-30-173.us-west-2.compute.internal",
                    "SubnetGatewayIpv4Address": "192.0.2.0/24",
                }
            ],
            "ContainerARN": "arn:aws:ecs:us-west-2:111122223333:container/1bdcca8b-f905-4ee6-885c-4064cb70f6e6",
            "LogOptions": {
                "awslogs-create-group": "true",
                "awslogs-group": "/ecs/containerlogs",
                "awslogs-region": "us-west-2",
                "awslogs-stream": "ecs/curl/e9028f8d5d8e4f258373e7b93ce9a3c3",
            },
            "LogDriver": "awslogs",
        }
    ],
    "LaunchType": "FARGATE",
}
