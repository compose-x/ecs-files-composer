.. meta::
    :description: ECS Files Composer input config
    :keywords: AWS, ECS, Configuration, Jinja

====================================
Custom Jinja2 filters & Functions
====================================

These filters come in addition to existing `Jinja2 Filters`_ & Functions.

------------
Functions
------------

AWS ECS
=================

ecs_container_metadata
------------------------

Filter that returns the ECS Container Metadata information

Parameters:

* ``property_key``: the property in the metadata you want to retrieve
* ``fallback_value``: a value to use if case the property is missing.


ecs_task_metadata
------------------

Filter that returns the ECS Task Metadata information

Parameters:

* ``property_key``: the property in the metadata you want to retrieve
* ``fallback_value``: a value to use if case the property is missing.


from_resolve
--------------

Parameter: A string that looks like the {{resolve:}} string in AWS CloudFormation

For example, building the string below, we retrieve the key `SASL_JAAS_CONFIG` from the content of the secret, which we
get the ARN from the `env_var` function with value `SECRET_ARN`

.. code-block:: yaml

    files:
      /tmp/secret.test:
        content: |
          client.id=sainsburys.applications.sc-ce.cdk-gateway
          sasl.mechanism=PLAIN
          sasl.jaas.config={{ from_resolve('{{resolve:secretsmanager:'  + env_var('SECRET_ARN') + ':SecretString:SASL_JAAS_CONFIG}}') | safe }}
          security.protocol=SASL_SSL
          #EOF



AWS Specific Filters
=====================

These filters use AWS API to retrieve specific properties.

msk_bootstrap
---------------

Parameters:
    * ``cluster_arn``: the ARN of the MSK cluster to use
    * ``broker_type``: the type of Broker endpoints to use.


For valid values for ``broker_type``, refer to `boto3.kafka.get_bootstrap_brokers`_ documentation,
and see the ``Response Syntax`` section.


Example to retrieve the Bootstrap servers for SASL + IAM for privately addressed cluster.

.. code-block:: yaml

    files:
      /tmp/conduktor-cdk.yaml:
        context: jinja2
        content: |
          organization:
            name: ${ORG_NAME:-testing}
          clusters:
            - id: amazon-msk-iam
              name: Amazon MSK IAM
              color: #FF9900
              bootstrapServers: {{ msk_bootstrap(env_var('BOOTSTRAP_ARN'), 'BootstrapBrokerStringSaslIam') }}
              properties: |
                security.protocol=SASL_SSL
                sasl.mechanism=AWS_MSK_IAM
                sasl.jaas.config=software.amazon.msk.auth.iam.IAMLoginModule required;
                sasl.client.callback.handler.class=io.conduktor.aws.IAMClientCallbackHandler

from_ssm
----------

Returns a value pulled from a SSM parameter.

Parameters

* ``parameter_name``: The name of the SSM parameter to get the value from.

Example

.. code-block:: yaml

    files:
      testing:
        content: |
          my_value: {{ from_ssm('my/ssm/parameter') }}


Generic Functions
====================

Simple functions to gap missing ones from Jinja2

env_var
-----------

Retrieves a value from environment variable. Can set a default value.

Parameters

* ``key``: Name of the environment variable
* ``value``: Default value in case the environment variable is not set.


Example

.. code-block:: yaml

    files:
      testing:
        content: |
          my_config_from_env_var: {{ env_var('ENV_VAR_NAME', "a default value") }}


---------------
Filters
---------------

Generic filters
=================

env_override
-------------

Similar to `env_var`_, it sets a value from environment variable, but expect a value to be already set.

to_yaml
---------

Renders an input into YAML

to_json
--------

Renders an input into JSON


.. _boto3.kafka.get_bootstrap_brokers: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/kafka.html#Kafka.Client.get_bootstrap_brokers
.. _Jinja2 Filters: https://jinja.palletsprojects.com/en/3.1.x/templates/#id11
