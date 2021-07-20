.. meta::
    :description: ECS Files Composer features
    :keywords: AWS, AWS ECS, Docker, Compose, docker-compose, AWS S3, AWS SSM, Secrets, Configuration

.. _sources:

================
Features
================

Files sources
================

AWS Common configuration
-------------------------

As described in :ref:`iam_override`, you can override the IAM role you want to use when attempting to retrieve files
from an AWS Service.

The IAM override defined the closest to the resource to retrieve is used. See :ref:`iam_priority` for more details.

AWS S3 Source
---------------


This allows you to define an S3 source with the Bucket name and Object key that you want to retrieve.

.. hint::

    All files downloaded from S3 are opened as a StreamingBody to avoid any casting error that could lead to corruption.
    You can download all types of files. (Flat files, Images and ZIP have been tested for that purpose)

.. hint::

    Docker images meant to be immutable and light, we recommend to keep the files you retrieve from AWS S3 light to avoid
    complications and delay the startup of your applications.


AWS SSM Source
---------------

Similarly to AWS S3, this allows to retrieve the content of a SSM Parameter and store it as file.
This can be useful simple credentials syntax and otherwise String defined parameters.

.. warning::

    If you are using a SecureString, make sure that you IAM role has kms:Decrypt permissions on the KMS Key.

AWS Secrets Manager Source
---------------------------

.. attention::

    This should only be used for very edgy use-cases, such as retrieving certificates stored as flat content in AWS SSM.
    You should absolutely use the `AWS ECS Task Definition Secrets`_ definitions

    .. seealso::

        `Secrets usage in ECS Compose-X`_


Url Source
------------

Allows you to download a file from an arbitrary URL. You can specify basic auth credentials if the file is not publicly
accessible.

.. warning::

    We do not recommend to put the basic auth credentials in plain text in the configuration, unless the source
    of the configuration for ECS Files Composer comes from AWS Secrets manager.

Files Rendering
====================

To allow further flexibility, you have the possibility to set a **context** which indicates whether the file should
be used as a template for a supported renderer.

.. note::

    The default value is plain, which means no alteration at all is to be done and the file should be used as-is.

.. warning::

    Do not attempt to perform rendering on a file that is not text (i.e. Images/ZIP etc.)

Jinja2 & Custom filters
-------------------------

Used in a lot of very well known frameworks and Applications, such as Ansible, Jinja2 is a very powerful template
rendering engine. Therefore, that will allow you to use Jinja filters to alter the file as you need it to.

.. hint::

    When using the jinja2 context, the file is placed into a randomly generated folder. That folder then auto-destroys
    itself once the processing of the given file is complete, and the file is then rendered and written at the defined
    location.

.. seealso::

    More about `Jinja2`_ and `Jinja2 filters`_

env_override filter
"""""""""""""""""""""

This filter allows you to very simply interpolate an environment variable value from the key of that env var.
Take the following example

.. code-block:: yaml

    files:
      /tmp/test.txt:
        content: >-
          this is a test {{ "default" | env_override('ENV_VAR_TO_CHANGE') }}
        owner: john
        group: root
        mode: 600
        context: jinja2

Files composer will use the content as template, which has been written to a temporary directory.
It then invokes Jinja, with the custom filter **env_override**. If the filter finds an environment variable
named *ENV_VAR_TO_CHANGE*, it then retrieves the value and pass it to Jinja. If not, Jinja will use *default* as the
value.


.. _AWS ECS Task Definition Secrets: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-ecs-taskdefinition-containerdefinitions.html#cfn-ecs-taskdefinition-containerdefinition-secrets
.. _Secrets usage in ECS Compose-X: https://docs.compose-x.io/syntax/docker-compose/secrets.html
.. _Jinja2: https://jinja.palletsprojects.com/en/3.0.x/
.. _Jinja2 filters: https://jinja.palletsprojects.com/en/3.0.x/templates/#filters
