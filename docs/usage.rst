=====
Usage
=====

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
