#  -*- coding: utf-8 -*-
# SPDX-License-Identifier: MPL-2.0
# Copyright 2020-2021 John Mille<john@compose-x.io>

import logging as logthings
import sys
from os import environ


def keyisset(x, y):
    """
    Macro to figure if the the dictionary contains a key and that the key is not empty

    :param x: The key to check presence in the dictionary
    :type x: str
    :param y: The dictionary to check for
    :type y: dict

    :returns: True/False
    :rtype: bool
    """
    if isinstance(y, dict) and x in y.keys() and y[x]:
        return True
    return False


def keypresent(x, y):
    """
    Macro to figure if the the dictionary contains a key and that the key is not empty

    :param x: The key to check presence in the dictionary
    :type x: str
    :param y: The dictionary to check for
    :type y: dict

    :returns: True/False
    :rtype: bool
    """
    if isinstance(y, dict) and x in y.keys():
        return True
    return False


def setup_logging():
    """Function to setup logging for ECS ComposeX.
    In case this is used in a Lambda function, removes the AWS Lambda default log handler

    :returns: the_logger
    :rtype: Logger
    """
    level = environ.get("LOGLEVEL")
    default_level = True
    formats = {
        "INFO": logthings.Formatter(
            "%(asctime)s [%(levelname)s], %(message)s",
            "%Y-%m-%d %H:%M:%S",
        ),
        "DEBUG": logthings.Formatter(
            "%(asctime)s [%(levelname)s], %(filename)s.%(lineno)d , %(funcName)s, %(message)s",
            "%Y-%m-%d %H:%M:%S",
        ),
    }

    if level is not None and isinstance(level, str):
        print("SETTING TO", level.upper())
        logthings.basicConfig(level=level.upper())
        default_level = False
    else:
        logthings.basicConfig(level="INFO")

    root_logger = logthings.getLogger()
    for h in root_logger.handlers:
        root_logger.removeHandler(h)
    the_logger = logthings.getLogger("EcsComposeX")

    if not the_logger.handlers:
        if default_level:
            formatter = formats["INFO"]
        elif keyisset(level.upper(), formats):
            formatter = formats[level.upper()]
        else:
            formatter = formats["DEBUG"]
        handler = logthings.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)
        the_logger.addHandler(handler)

    return the_logger


LOG = setup_logging()
