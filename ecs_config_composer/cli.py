#  -*- coding: utf-8 -*-
# SPDX-License-Identifier: MPL-2.0
# Copyright 2020-2021 John Mille<john@compose-x.io>

"""Console script for ecs_config_composer."""
import argparse
import sys


def main():
    """Console script for ecs_config_composer."""
    parser = argparse.ArgumentParser()
    parser.add_argument("_", nargs="*")
    args = parser.parse_args()

    print("Arguments: " + str(args._))
    print("Replace this message by putting your code into " "ecs_config_composer.cli.main")
    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
