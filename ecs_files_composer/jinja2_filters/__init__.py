#  -*- coding: utf-8 -*-
# SPDX-License-Identifier: MPL-2.0
# Copyright 2020-2021 John Mille<john@compose-x.io>

"""
Package allowing to expand the Jinja filters to use.
"""

from os import environ


def env(value, key):
    """
    Function to use in new Jinja filter
    :param value:
    :param key:
    :return:
    """
    return environ.get(key, value)
