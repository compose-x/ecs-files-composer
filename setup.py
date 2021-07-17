#!/usr/bin/env python
#  -*- coding: utf-8 -*-
# SPDX-License-Identifier: MPL-2.0
# Copyright 2020-2021 John Mille<john@compose-x.io>

import os
import re

from setuptools import find_packages, setup

DIR_HERE = os.path.abspath(os.path.dirname(__file__))
# REMOVE UNSUPPORTED RST syntax
REF_REGX = re.compile(r"(\:ref\:)")

try:
    with open(f"{DIR_HERE}/README.rst", encoding="utf-8") as readme_file:
        readme = readme_file.read()
        readme = REF_REGX.sub("", readme)
except FileNotFoundError:
    readme = "ECS Files Composer"

try:
    with open(f"{DIR_HERE}/HISTORY.rst", encoding="utf-8") as history_file:
        history = history_file.read()
except FileNotFoundError:
    history = "Latest packaged version."

requirements = []
with open(f"{DIR_HERE}/requirements.txt", "r") as req_fd:
    for line in req_fd:
        requirements.append(line.strip())

test_requirements = []
try:
    with open(f"{DIR_HERE}/requirements_dev.txt", "r") as req_fd:
        for line in req_fd:
            test_requirements.append(line.strip())
except FileNotFoundError:
    print("Failed to load dev requirements. Skipping")


setup_requirements = [
    "pytest-runner",
]

setup(
    author="John Preston",
    author_email="john@compose-x.io",
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
    ],
    description="Files and configuration handler to inject configuration files into volumes for ECS containers",
    entry_points={
        "console_scripts": [
            "ecs_files_composer=ecs_files_composer.cli:main",
        ],
    },
    install_requires=requirements,
    long_description=readme,
    long_description_content_type="text/x-rst",
    include_package_data=True,
    keywords="ecs_files_composer",
    name="ecs_files_composer",
    packages=find_packages(include=["ecs_files_composer", "ecs_files_composer.*"]),
    setup_requires=setup_requirements,
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/compose-x/ecs-files-composer",
    version="0.2.0",
    zip_safe=False,
    license="MPL-2.0",
)
