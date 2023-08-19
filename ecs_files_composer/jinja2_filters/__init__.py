# SPDX-License-Identifier: MPL-2.0
# Copyright 2020-2022 John Mille<john@compose-x.io>

"""
Package allowing to expand the Jinja filters to use.
"""
import json
import re
from base64 import b64decode, b64encode
from os import environ

import yaml
from flatdict import FlatterDict

from .aws_filters import msk_bootstrap


def env_override(value, key):
    """
    Function to use in new Jinja filter
    :param value:
    :param key:
    :return:
    """
    return environ.get(key, value)


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


def to_yaml(value):
    """
    Filter to render input to YAML formatted content
    :return:
    """
    return yaml.dump(value, Dumper=yaml.Dumper)


def to_json(value, indent=2):
    return json.dumps(value, indent=indent)


def base64encode(value: str):
    """Return value base64 encoded"""
    try:
        return b64encode(value).decode("utf-8")
    except TypeError:
        return b64encode(value.encode("utf-8")).decode("utf-8")


def base64decode(value) -> bytes:
    """Decodes base64 encoded value"""
    return b64decode(value)


JINJA_FILTERS = {
    "to_yaml": to_yaml,
    "to_json": to_json,
    "env_override": env_override,
    "base64encode": base64encode,
    "base64decode": base64decode,
}
