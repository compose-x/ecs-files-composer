# SPDX-License-Identifier: MPL-2.0
# Copyright 2020-2022 John Mille<john@compose-x.io>

"""
Package allowing to expand the Jinja filters to use.
"""
import json
import re
from os import environ

import requests
import yaml
from boto3.session import Session
from flatdict import FlatDict, FlatterDict

from .aws_filters import msk_bootstrap


def env_override(value, key):
    """
    Function to use in new Jinja filter
    :param value:
    :param key:
    :return:
    """
    return environ.get(key, value)


def define_metadata(for_task=False):
    meta_v4 = "ECS_CONTAINER_METADATA_URI_V4"
    meta_v3 = "ECS_CONTAINER_METADATA_URI"

    if environ.get(meta_v3, None):
        meta_url = environ.get(meta_v3)
    elif environ.get(meta_v4, None):
        meta_url = environ.get(meta_v4)
    else:
        raise OSError("No ECS Metadata URL provided. This filter only works on ECS")
    if for_task:
        return requests.get(f"{meta_url}/task")
    else:
        return requests.get(meta_url)


def from_list_to_dict(top_key, new_mapping, to_convert):
    """

    :param str top_key:
    :param dict new_mapping:
    :param list to_convert:
    :return:
    """
    for count, item in enumerate(to_convert):
        list_key = f"{top_key}_{count}"
        if isinstance(item, dict):
            from_dict_to_simple_keys(list_key, new_mapping, item)
        elif isinstance(item, list):
            from_list_to_dict(list_key, new_mapping, item)


def from_dict_to_simple_keys(top_key, new_mapping, to_convert):
    """

    :param str top_key:
    :param dict new_mapping:
    :param dict to_convert:
    :return:
    """
    for key, value in to_convert.items():
        if isinstance(value, str):
            new_mapping[f"{top_key}_{key}"] = value
        elif isinstance(value, dict):
            from_dict_to_simple_keys(f"{top_key}_{key}", new_mapping, value)
        elif isinstance(value, list):
            from_list_to_dict(f"{top_key}_{key}", new_mapping, value)


def from_metadata_to_flat_keys(metadata):
    """
    Function to transform the metadata into simplified structure
    :param dict metadata:
    :return:
    """
    new_metadata = {}
    for key, value in metadata.items():
        if isinstance(value, str):
            new_metadata[key] = value
        elif isinstance(value, dict):
            from_dict_to_simple_keys(key, new_metadata, value)
        elif isinstance(value, list):
            from_list_to_dict(key, new_metadata, value)
    return new_metadata


def get_property(metadata, property_key, separator: str = None):
    if separator is None:
        separator = r"::"
    metadata_mapping = FlatterDict(metadata)
    metadata_mapping.set_delimiter(separator)
    if property_key in metadata_mapping:
        return metadata_mapping[property_key]

    metadata_mapping = from_metadata_to_flat_keys(metadata)
    property_re = re.compile(property_key)
    for key, value in metadata_mapping.items():
        if property_re.findall(key):
            return value
    return None


def ecs_container_metadata(property_key=None, fallback_value=None):
    metadata_raw = define_metadata()
    metadata = metadata_raw.json()
    if property_key:
        value = get_property(metadata, property_key)
        if value is None:
            print(f"No task property found matching {property_key}")
            return fallback_value
        return value
    return metadata


def ecs_task_metadata(property_key=None, fallback_value=None):
    metadata_raw = define_metadata(for_task=True)
    metadata = metadata_raw.json()
    if property_key:
        value = get_property(metadata, property_key)
        if value is None:
            print(f"No task property found matching {property_key}")
            return fallback_value
        return value
    return metadata


def to_yaml(value):
    """
    Filter to render input to YAML formatted content
    :return:
    """
    return yaml.dump(value, Dumper=yaml.Dumper)


def to_json(value, indent=2):
    return json.dumps(value, indent=indent)


def env_var(key, value=None):
    return environ.get(key, value)


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


def hostname(alternative_value: str = None) -> str:
    try:
        import platform

        return str(platform.node())
    except Exception as error:
        print("Error with platform", error)
        try:
            import socket

            return str(socket.gethostname())
        except Exception as error:
            print("Error with socket", error)
            pass
    if alternative_value:
        return alternative_value


JINJA_FUNCTIONS = {
    "ecs_container_metadata": ecs_container_metadata,
    "ecs_task_metadata": ecs_task_metadata,
    "env_var": env_var,
    "from_ssm": from_ssm,
    "from_ssm_json": from_ssm_json,
    "msk_bootstrap": msk_bootstrap,
    "hostname": hostname,
}

JINJA_FILTERS = {"to_yaml": to_yaml, "to_json": to_json, "env_override": env_override}
