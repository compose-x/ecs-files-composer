#!/usr/bin/env python
#  -*- coding: utf-8 -*-
# SPDX-License-Identifier: MPL-2.0
# Copyright 2020-2021 John Mille<john@compose-x.io>

"""Tests for `ecs_files_composer` package."""

from os import path

import pytest

from ecs_files_composer import input
from ecs_files_composer.ecs_files_composer import start_jobs

HERE = path.abspath(path.dirname(__file__))


@pytest.fixture
def simple_json_config():
    with open(f"{HERE}/RAW_CONTENT.txt", "r") as raw_fd:
        raw_content = raw_fd.read()
    return {
        "files": {
            "/tmp/test_raw.txt": {"content": raw_content},
            "/tmp/test.txt": {"content": "THIS IS A TEST"},
            "/tmp/test2.txt": {"content": "THIS IS A TEST2"},
            "/tmp/dedoded.txt": {"content": "VEhJUyBJUyBFTkRPREVEIE1FU1NBR0U=", "encoding": "base64"},
        }
    }


@pytest.fixture
def s3_files_config():
    with open(f"{HERE}/RAW_CONTENT.txt", "r") as raw_fd:
        raw_content = raw_fd.read()
    return {
        "files": {
            "/tmp/test_raw.txt": {"content": raw_content},
            "/tmp/aws.yaml": {"source": {"S3": {"BucketName": "sacrificial-lamb", "Key": "aws.yml"}}},
        }
    }


def test_simple_job_import(simple_json_config):
    start_jobs(simple_json_config)


def test_s3_files_simple(s3_files_config):
    start_jobs(s3_files_config)
