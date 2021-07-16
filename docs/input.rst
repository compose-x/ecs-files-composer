.. meta::
    :description: ECS Files Composer input config
    :keywords: AWS, AWS ECS, Docker, Compose, docker-compose, AWS S3, AWS SSM, Secrets, Configuration

.. _input:

========================
Configuration input
========================

Input definition sources
==========================

ECS Files Composer aims to provide a lof of flexibility to user in how they want to configure the job definition.
The inspiration of the files input schema comes from `AWS CloudFormation ConfigSets.files`_ which could be defined
in JSON or YAML.

So in that spirit, so long as the file can be parsed down into an object that complies to the `JSON Schema`_, the source
can be varied.

From environment variable
--------------------------

The primary way to override configuration on the fly with containers is either change ENTRYPOINT/CMD or environment
variables.

So in that spirit, you can define a specific environment variables or simply use the default one, **ECS_CONFIG_CONTENT**

You can do the JSON string encoding yourself, or more simply you could do that in docker-compose, as follows

.. code-block:: yaml


    version: "3.8"
    services:
      files-sidecar:
        environment:
          AWS_CONTAINER_CREDENTIALS_RELATIVE_URI: "/creds"
          AWS_DEFAULT_REGION: ${AWS_DEFAULT_REGION:-eu-west-1}
          ECS_CONFIG_CONTENT: |

            files:
              /opt/files/test.txt:
                content: >-
                  test from a yaml raw content
                owner: john
                group: root
                mode: 600
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

From JSON or YAML file
-----------------------

If you prefer to use ECS Files Composer as a CLI tool, or simply to test (don't forget about IAM permissions!) the configuration
itself, you can write the configuration into a simple file.

So, you could have the following config file for the execution

.. code-block:: yaml
    :caption: test.yaml

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


And run

.. code-block:: bash

    ecs_files_composer -f test.yaml

From AWS S3 / SSM / SecretsManager
-------------------------------------

This allows the ones who might need to generate the job instruction/input through CICD and store the execution file into
AWS services.

.. hint::

    If to retrieve the configuration file from another account, you can specify a Role ARN to use.

.. hint::

    When running on ECS and storing the above configuration, you can use `AWS ECS Task Definition Secrets`_ which
    creates an environment variable for you. Therefore, you could just indicate to use that.

.. _input_schema:

JSON Schema
============

The input for ECS Files Composer has to follow the JSON Schema below.

.. jsonschema::../ecs-files-input.json

.. _iam_override:



AWS IAM Override
=================

ECS Files Composer uses AWS Boto3 as the SDK. So wherever you are running it, the SDK will follow the priority chain
of credentials in order to figure out which to use.

In the case of running it on AWS ECS, your container will have an IAM Task Role associated with it.
You are responsible for configuring the permissions you want to give to your service.

The IamOverride definition allows you to define whether the credentials used by the tool should be used to acquire
temporary credential by assuming another role.

This can present a number of advantages, such as retrieving files from another AWS Account than the one you are currently
using to run the application.

.. _iam_priority:

IAM Override Priority
-------------------------

When building the boto3 session to use, by default the boto3 SDK will pick the first valid set of credentials.

If you specify the IamOverride properties **at the root level**, as follows

.. code-block:: yaml

    files:
      /path/to/file1:
        source:
          S3:
            BucketName: some-bucket
            Key: file.txt
    IamOverride:
      RoleArn: arn:aws:iam::012345678901:role/role-name

Then **all subsequent API calls to AWS will be made by assuming this IAM role.**

If however you needed to change the IamOverride for a single file, or use two different profiles for different files,
then apply the IamOverride at that source level, as follows.

.. code-block:: yaml

    files:
      /path/to/file1:
        source:
          S3:
            BucketName: some-bucket
            Key: file.txt
            IamOverride:
              RoleArn: arn:aws:iam::012345678901:role/role-name
      /path/to/file2:
        source:
          Ssm:
            ParameterName: /path/to/parameter
            IamOverride:
              RoleArn: arn:aws:iam::012345678901:role/role-name-2

      /path/to/file3:
        source:
          S3:
            BucketName: some-other-other-bucket
            Key: file.txt

In the above example, to retrieve /path/to/file1, the program will attempt to assume role and use **arn:aws:iam::012345678901:role/role-name**,
same logic applies for /path/to/file2, and  /path/to/file3 will use the default credentials found by the SDK.

.. attention::

    If the SDK cannot find the credentials, the program will throw an exception.

.. _env_var_subst:

Environment Variables substitution
===================================

ECS Files composer was created with the primary assumption that you might be running it in docker-compose or on AWS ECS.
When you define environment variables in docker-compose or `ECS Compose-X`_, the environment variables are by default
interpolated.

docker compose allows to not interpolate environment variables, but it is all or nothing, which might not be flexible
enough.

So to solve that, the environment files substitution has decided to use the AWS CFN !Sub function syntax to declare
literal variables that shall not be interpolated.

So for example, if you have in docker-compose the following

.. code-block:: yaml

    services:
      connect-files:
        environment:
          ENV: stg
          ECS_CONFIG_CONTENT: |

            files:
              /opt/connect/truststore.jks:
                mode: 555
                source:
                  S3:
                    BucketName: ${CONNECT_BUCKET}
                    Key: commercial/core/truststore.jks
              /opt/connect/core.jks:
                mode: 555
                source:
                  S3:
                    BucketName: ${CONNECT_BUCKET}
                Key: commercial/core/${ENV}.jks

docker-compose and compose-x would interpolate the value for **${ENV}** and **${CONNECT_BUCKET}** from the execution context.
But here, you defined that ENV value should be **stg**, and it will create an environment variable that gets exposed to the
container at runtime.

To avoid this situation and have the environment variable interpolated at runtime within the context of your container,
not the context of docker-compose or ECS Compose-X, simply write it with **${!ENV_VAR_NAME}**.

So this would give us the following as a result.

.. code-block:: yaml

    services:
      connect-files:
        environment:
          ENV: stg
          ECS_CONFIG_CONTENT: |

            files:
              /opt/connect/truststore.jks:
                mode: 555
                source:
                  S3:
                    BucketName: ${!CONNECT_BUCKET}
                    Key: commercial/core/truststore.jks
              /opt/connect/core.jks:
                mode: 555
                source:
                  S3:
                    BucketName: ${!CONNECT_BUCKET}
                    Key: commercial/core/${!ENV}.jks

When running, ECS Compose-X (or ECS Files Composer) will not interpolate the environment variable and remove the **!**
from the raw string and allow the environment variable **name** to remain intact once rendered.

.. _ECS Compose-X: https://docs.compose-x.io
.. _AWS ECS Task Definition Secrets: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-ecs-taskdefinition-containerdefinitions.html#cfn-ecs-taskdefinition-containerdefinition-secrets
.. _Secrets usage in ECS Compose-X: https://docs.compose-x.io/syntax/docker-compose/secrets.html
.. _AWS CloudFormation ConfigSets.files: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-init.html#aws-resource-init-files
