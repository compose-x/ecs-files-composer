.. meta::
    :description: ECS Files Composer input config
    :keywords: AWS, AWS ECS, Docker, Compose, docker-compose, AWS S3, AWS SSM, Secrets, Configuration

===================
ECS Files Composer
===================


.. image:: https://img.shields.io/pypi/v/ecs_files_composer.svg
        :target: https://pypi.python.org/pypi/ecs_files_composer


.. image:: https://codebuild.eu-west-1.amazonaws.com/badges?uuid=eyJlbmNyeXB0ZWREYXRhIjoiRWk3VUhxUi9peEdZRGs2cGFiTk5XM0VDK1FEQTBMN2JTdHh5b091NTVVdFd3RmpoM1lpdGkrTGtTZDJzVCt5dDBCc3Zsc0dXWHI5RHJRSG82UFJNdUJzPSIsIml2UGFyYW1ldGVyU3BlYyI6InJlYXlBWStNMDVZNEoyMnQiLCJtYXRlcmlhbFNldFNlcmlhbCI6MX0%3D&branch=main


What does it do?
=================

ECS Files Composer, although can be used in EKS and other Docker context, is a small program that will allow users
to define files they need pulled out of AWS Services, such as AWS S3 or AWS SSM Parameter Store, and load the content
to a given location, adding builtin capabilities to set file ownership, mode, and other handy features.

The configuration of the job to perform can be written in YAML or JSON (see examples), so long as they comply to a given
schema.

Why use it?
============

Having your core application, when reliant on configuration files, can be tricky to start in a way that the configuration
needs to be pulled first and then started. This can add un-necessary complexity and logic to the application.
And some docker images you might pull off the shelves from DockerHub do not necessarily allow for configuration override
from environment variables.

By using a sidecar that handles all of that logic, you delegate all of these activities to it. And with the ability to define
which container to start first with success criteria, you also ensure that your application won't start without the configuration
files it needs.

.. hint::

    This app / docker image can be used in any context, locally, on-premise, with Docker, on AWS ECS / EKS or in other cloud platforms.

How to use it ?
=================

`Full official documentation <https://docs.files-composer.compose-x.io/index.html>`__


Docker
----------------

.. code-block:: bash

    docker run public.ecr.aws/compose-x/ecs-files-composer:${VERSION:-latest} -h
    docker run -v $PWD:/ /var/tmp,:/public.ecr.aws/compose-x/ecs-files-composer:${VERSION:-latest} -f files.yaml

.. attention::

    The default user is root to avoid running into issues when using chmod/chown and other commands.
    Change behaviour at your own risks.


CLI
------------

.. code-block:: bash


    usage: ecs_files_composer [-h] [-f FILE_PATH | -e ENV_VAR | --from-ssm SSM_CONFIG | --from-s3 S3_CONFIG] [--role-arn ROLE_ARN] [_ ...]

    optional arguments:
      -h, --help            show this help message and exit
      -f FILE_PATH, --from-file FILE_PATH
                            Configuration for execution from a file
      -e ENV_VAR, --from-env-var ENV_VAR
                            Configuration for execution is in an environment variable
      --from-ssm SSM_CONFIG
                            Configuration for execution is in an SSM Parameter
      --from-s3 S3_CONFIG   Configuration for execution is in an S3
      --role-arn ROLE_ARN   The Role ARN to use for the configuration initialization
