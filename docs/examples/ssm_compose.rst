
.. _example_basic_ssm:

.. highlight:: shell

.. code-block:: json

    {
      "files": {
        "/tmp/aws.template": {
          "source": {
            "S3": {
              "BucketName": "${BUCKET_NAME:-sacrificial-lamb}",
              "Key": "aws.yml"
            }
          }
        },
        "/tmp/ssm.txt": {
          "source": {
            "Ssm": {
              "ParameterName": "/cicd/shared/kms/arn"
            }
          },
          "commands": {
            "post": [
              "file /tmp/ssm.txt"
            ]
          }
        },
        "/tmp/secret.txt": {
          "source": {
            "Secret": {
              "SecretId": "GHToken"
            }
          }
        },
        "/tmp/public.json": {
          "source": {
            "Url": {
              "Url": "https://ifconfig.me/all.json"
            }
          }
        }
      }
    }

This is a simple translation from YAML to JSON (for simplicity) that we are going to put into SSM as a String

.. code-block:: console

    aws ssm put-parameter --name /files/config/parameter --value file://test.json  --type String

.. code-block:: yaml
    :caption: In docker-compose

    services:
      files-sidecar:
        command: --from-ssm /files/config/parameter

.. code-block:: console
    :caption: In CLI

    ecs_files_composer --from-ssm /files/config/parameter

.. attention::

    Make sure you have permissions on the **Task Role** to perform ssm:GetParameter.
    You also need IAM permissions to perform kms:Decrypt on the KMS Key used to encrypt the SecureString (if used)
