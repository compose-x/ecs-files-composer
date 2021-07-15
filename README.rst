===================
ECS Files Composer
===================


.. image:: https://img.shields.io/pypi/v/ecs_files_composer.svg
        :target: https://pypi.python.org/pypi/ecs_files_composer

.. image:: https://readthedocs.org/projects/ecs-config-composer/badge/?version=latest
        :target: https://ecs-config-composer.readthedocs.io/en/latest/?version=latest
        :alt: Documentation Status


------------------------------------------------------------------------------------------------------
Files and configuration handler to inject configuration files into volumes for ECS containers.
------------------------------------------------------------------------------------------------------

Usage
=======

.. code-block:: bash


    usage: ecs_files_composer [-h] [-f FILE_PATH | -e ENV_VAR | --from-ssm SSM_CONFIG | --from-s3 S3_CONFIG] [--role-arn ROLE_ARN] [_ ...]

    positional arguments:
      _

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


Example inputs
===============

.. code-block:: yaml

    files:
      /opt/app/test.txt:
        content: >-
          test from a yaml raw content
        owner: john
        group: root
        mode: 600
      /opt/app/aws.template:
        source:
          S3:
            BucketName: ${BUCKET_NAME:-sacrificial-lamb}
            Key: aws.yml

      /opt/app/ssm.txt:
        source:
          Ssm:
            ParameterName: /cicd/shared/kms/arn
        commands:
          post:
            - file /opt/app/ssm.txt

      /opt/app/secret.txt:
        source:
          Secret:
            SecretId: GHToken

.. attention::

    The default user is root to avoid running into issues when using chmod/chown and other commands.
    Change behaviour at your own risks.

Features
=========

* Pulls configuration files from SSM | S3 | Secrets Manager | and inject into volumes
* Allows to use environment variables for your YAML values. Limited operations.
