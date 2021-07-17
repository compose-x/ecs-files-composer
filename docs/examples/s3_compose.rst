
.. _example_basic_s3:

.. highlight:: shell

.. code-block:: yaml
    :caption: input.yaml

    files:
      /tmp/test.txt:
        content: >-
          test from a yaml raw content
        owner: john
        group: root
        mode: 600
      /tmp/aws.template:
        source:
          S3:
            BucketName: ${BUCKET_NAME:-sacrificial-lamb}
            Key: aws.yml

      /tmp/ssm.txt:
        source:
          Ssm:
            ParameterName: /cicd/shared/kms/arn
        commands:
          post:
            - file /tmp/ssm.txt

      /tmp/secret.txt:
        source:
          Secret:
            SecretId: GHToken

      /tmp/public.json:
        source:
          Url:
            Url: https://ifconfig.me/all.json

      /tmp/aws.png:
        source:
          Url:
            Url: https://dunhamconnect.com/wp-content/uploads/aws-migration-1200x675.jpg


We then upload the file to S3.

.. code-block:: console

    aws s3 cp input.yaml s3://sacrificial-lamb/

.. code-block:: yaml
    :caption: In docker-compose

    services:
      files-sidecar:
        command: --from-s3 s3://sacrificial-lamb/input.yaml

.. code-block:: console
    :caption: In CLI

    ecs_files_composer --from-s3 s3://sacrificial-lamb/input.yaml

.. attention::

    Make sure you have permissions on the **Task Role** to perform s3:GetObject.
    You also need IAM permissions to perform kms:Decrypt on the KMS Key used to encrypt the object (if used)
