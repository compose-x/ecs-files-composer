.. meta::
    :description: ECS Files Composer install
    :keywords: AWS, AWS ECS, Docker, Compose, docker-compose, AWS S3, AWS SSM, Secrets, Configuration

.. highlight:: shell

============
Installation
============

Docker
-------

.. code-block:: console

    docker pull public.ecr.aws/compose-x/ecs-files-composer:${VERSION:-latest}


Docker Compose
---------------

.. code-block:: yaml

    version: "3.8"
    volumes:
      localshared:

    services:
      files-composer:
        image: public.ecr.aws/compose-x/ecs-files-composer:${VERSION:-latest}
        deploy:
          resources:
            limits:
              cpus: 0.1
              memory: 128M
        volumes:
          - localshared:/opt/files/


Stable release
--------------

To install ECS Files Composer, run this command in your terminal:

.. code-block:: console

    $ pip install ecs_files_composer

This is the preferred method to install ECS Files Composer, as it will always install the most recent stable release.

If you don't have `pip`_ installed, this `Python installation guide`_ can guide
you through the process.

.. _pip: https://pip.pypa.io
.. _Python installation guide: http://docs.python-guide.org/en/latest/starting/installation/


From sources
------------

The sources for ECS Files Composer can be downloaded from the `Github repo`_.

You can either clone the public repository:

.. code-block:: console

    $ git clone git://github.com/compose-x/ecs-files-composer

Or download the `tarball`_:

.. code-block:: console

    $ curl -OJL https://github.com/compose-x/ecs-files-composer/tarball/master

Once you have a copy of the source, you can install it with:

.. code-block:: console

    $ python setup.py install


.. _Github repo: https://github.com/compose-x/ecs-files-composer
.. _tarball: https://github.com/compose-x/ecs-files-composer/tarball/master
