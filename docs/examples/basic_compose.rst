
.. _example_basic_compose:

.. code-block:: yaml

    services:
      files-sidecar:
        command: -e ECS_FILES
        environment:
          ECS_FILES: |

            files:
              /opt/files/aws.template:
                source:
                  S3:
                    BucketName: ${BUCKET_NAME:-sacrificial-lamb}
                    Key: aws.yml

              /opt/files/ssm.txt:
                source:
                  Ssm:
                    ParameterName: /cicd/shared/kms/arn
                commands:
                  post:
                    - file /opt/files/ssm.txt

              /opt/files/secret.txt:
                source:
                  Secret:
                    SecretId: GHToken

.. note::

    Note that here, we named the environment variable **ECS_FILES**, and override the command for *ecs_files_composer*
    to use that environment variable name.
