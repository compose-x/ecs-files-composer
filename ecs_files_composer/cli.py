# SPDX-License-Identifier: MPL-2.0
# Copyright 2020-2022 John Mille<john@compose-x.io>

"""Console script for ecs_files_composer."""
import argparse
import sys
from os import environ

from ecs_files_composer.common import LOG
from ecs_files_composer.ecs_files_composer import init_config, start_jobs


def main():
    """Console script for ecs_files_composer."""
    parser = argparse.ArgumentParser()
    options = parser.add_mutually_exclusive_group()
    options.add_argument(
        "-f",
        "--from-file",
        help="Configuration for execution from a file",
        type=str,
        required=False,
        dest="file_path",
    )
    options.add_argument(
        "-e",
        "--from-env-var",
        dest="env_var",
        required=False,
        help="Configuration for execution is in an environment variable",
    )
    options.add_argument(
        "--from-ssm",
        dest="ssm_config",
        help="Configuration for execution is in an SSM Parameter",
        required=False,
    )
    options.add_argument(
        "--from-s3",
        dest="s3_config",
        required=False,
        help="Configuration for execution is in an S3",
    )
    options.add_argument(
        "--from-secrets",
        dest="secret_config",
        required=False,
        help="Configuration for execution is in an AWS Secrets Manager",
    )
    parser.add_argument(
        "--role-arn",
        help="The Role ARN to use for the configuration initialization",
        required=False,
    )
    parser.add_argument(
        "--decode-base64",
        help="Whether the source config is in base64 encoded",
        action="store_true",
        required=False,
        default=False,
    )
    parser.add_argument(
        "--context",
        help="Indicate which context to use (valid: jinja2|plain). Default is jinja2",
        required=False,
        default="jinja2",
    )
    parser.add_argument(
        "--override-init-folder",
        dest="init_folder",
        required=False,
        type=str,
        default="",
    )
    parser.add_argument("_", nargs="*")
    args = parser.parse_args()
    print("Arguments: " + str(args._))
    if not (
        args.env_var or args.ssm_config or args.s3_config or args.file_path
    ) and environ.get("ECS_CONFIG_CONTENT", None):
        LOG.info("Using default env variable ECS_CONFIG_CONTENT")
        config = init_config(
            env_var="ECS_CONFIG_CONTENT",
            decode_base64=bool(environ.get("DECODE_BASE64", False)),
            context=environ.get("context", "jinja2"),
        )
    elif args.env_var:
        config = init_config(
            env_var=args.env_var,
            decode_base64=args.decode_base64,
            context=args.context,
            override_folder=args.init_folder,
        )
    elif args.file_path:
        config = init_config(
            file_path=args.file_path,
            decode_base64=args.decode_base64,
            context=args.context,
            override_folder=args.init_folder,
        )
    elif args.ssm_config:
        config = init_config(
            ssm_parameter=args.ssm_config,
            decode_base64=args.decode_base64,
            context=args.context,
            override_folder=args.init_folder,
        )
    elif args.s3_config:
        config = init_config(
            s3_config=args.s3_config,
            decode_base64=args.decode_base64,
            context=args.context,
            override_folder=args.init_folder,
        )
    elif args.secret_config:
        config = init_config(
            secret_config=args.secret_config,
            decode_base64=args.decode_base64,
            context=args.context,
            override_folder=args.init_folder,
        )
    else:
        raise parser.error(
            "You must specify where the execution configuration comes from or set ECS_CONFIG_CONTENT."
        )

    start_jobs(config)
    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
