.. meta::
    :description: Files Commands
    :keywords: Configuration, commands

.. _commands_docs:

Commands
=========

.. warning::

    When using docker, the container user is root to simplify access to filesystem.

Within files, you have the ability to run `post` commands, which are commands to run after writing the file to disk
was done successfully.


Commands can come in handy to change permissions on files and all sorts of things so that the application that will
read/consume the file & folders will have permissions to do so.

Commands can be written in 2 ways

* a simple string: will execute the command, won't output the result
* a mapping, with the command, and options


Using the mapping option
-------------------------

As of 2.0, the available options are

* display_output: bool
* ignore_error: bool


display_output
^^^^^^^^^^^^^^^

As its name would suggest, this will log the output of the command.

.. warning::

    Use carefully as it won't be filtering out any secret values & details

ignore_error
^^^^^^^^^^^^^^^

You can already set error conditions and ignore at the top level of the file. This option allows for a localized setting.
For example, if every other commands must succeed but one of them can fail without causing an error, you would set this to true

In the example below, we want to see the content of `/tmp/testing/toto.txt` which we know must work because
it will be rendered.

However, file `/tmp/init/init.con` might not exist on the file system, so if it doesn't, we ignore.

.. code-block:: yaml

files:
  /tmp/testing/toto.txt:
    content: |
      HELLO YOU
    context: plain
    commands:
      post:
        - chown 1000:1000 -R /opt/files
        - command: ls /tmp/
          display_output: true
        - command: cat /tmp/init/init.con
          display_output: true
          ignore_error: true
