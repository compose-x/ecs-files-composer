
.. _example_basic_secrets:

.. highlight:: shell

.. code-block:: json
    :caption: secret_input.json

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
              "Url": "https://secretdomain.me/all.json",
              "Username": "someuser",
              "Password": "somecomplicatedPassword"
            }
          }
        }
      }
    }

.. hint::

    This is the only place where entering sensitive information, for auth or for the content, that is acceptable.
    Never otherwise put secret information in your job description.

We then create a new secret from the file into Secrets Manager.

.. code-block:: console

    aws secretsmanager create-secret --name /config/files/secret --secret-string file://secret_input.json

.. code-block:: yaml
    :caption: In docker-compose

    services:
      files-sidecar:
        command: --from-secrets /config/files/secret

.. code-block:: console
    :caption: In CLI

    ecs_files_composer --from-secrets /config/files/secret

.. attention::

    Make sure you have permissions on the **Task Role** to perform secretsmanager:GetSecretValue.
    You also need IAM permissions to perform kms:Decrypt on the KMS Key used to encrypt the secret.
