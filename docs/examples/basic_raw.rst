
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

.. code-block:: console
    :caption: In CLI

    ecs_files_composer -f input.yaml
