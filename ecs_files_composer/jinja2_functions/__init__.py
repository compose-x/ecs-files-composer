# SPDX-License-Identifier: MPL-2.0
# Copyright 2020-2022 John Mille<john@compose-x.io>

from __future__ import annotations

from os import environ

from ecs_files_composer.jinja2_functions.aws import (
    ec2_zone_id,
    ecs_container_metadata,
    ecs_task_metadata,
    from_ssm,
    from_ssm_json,
    msk_bootstrap,
    using_resolve,
)


def env_var(key, value=None):
    return environ.get(key, value)


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
    if alternative_value:
        return alternative_value


JINJA_FUNCTIONS = {
    "ecs_container_metadata": ecs_container_metadata,
    "ecs_task_metadata": ecs_task_metadata,
    "env_var": env_var,
    "from_ssm": from_ssm,
    "from_ssm_json": from_ssm_json,
    "from_resolve": using_resolve,
    "msk_bootstrap": msk_bootstrap,
    "hostname": hostname,
    "ec2_zone_id": ec2_zone_id,
    "subnet_zone_id": ec2_zone_id,
}
