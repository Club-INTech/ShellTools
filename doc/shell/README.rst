Create an asynchronous command line interface with the `Shell` class
====================================================================

The ``shell`` package provides several utilities for building your own CLI. Defined commands can be asynchronous and synchronized output to the terminal is supported.

Building a basic shell
----------------------

Here is an example of a simple shell:

.. literalinclude:: ../../tests/test_snippet.py
   :lines: 11-32 

The syntax for the command themselves is simillar to the one from the `cmd <https://docs.python.org/3/library/cmd.html>`_ library, but lots of features are differents:

- You do not need to parse the command line yourself, the decorators to the command methods do it for you.
- The ``command`` and ``argument`` decorators are used to specify the input parameters. ``argument`` accepts the same parameters as ``ArgumentParser.add_argument`` from `argparse <https://docs.python.org/3/library/argparse.html>`_.
- Return value has no effect. The shell may only be exited by hitting ``CTRL+D`` or by raising an exception.

Synchronous commands
~~~~~~~~~~~~~~~~~~~~

``do_print`` is defined as a synchronous method. As such, it is executed in one go. The command is not guarantee to be executed immeditely. However, it will run in the same thread as the one running the shell and will not be interrupted by another command once it has started.

Asynchronous commands
~~~~~~~~~~~~~~~~~~~~~

``do_nprint`` is defined a an asynchronous method. This command will run within an ``asyncio`` loop, which means you can use the ``asyncio`` API in the body of an asynchronous command. The command will be cancelled when the shell is exited. However, it is guaranteed that the command will never be cancelled before starting so you have the opportunity to handle the cancellation the way you like.

Support for docstrings
~~~~~~~~~~~~~~~~~~~~~~

When the user wish to see more information for a given command, the docstring of the command is automatically fetched and displayed. Additionally, the help string given for each parameter is also displayed.

Capturing the keyboard input
----------------------------

.. warning::
   This feature is poorly supported across terminals. If you want to use it, run your shell into a compatible terminal like ``xterm``.

Instead of receiving command from the standard input, it is possible of directly capture input form keyboard.

.. literalinclude:: ../../tests/test_snippet.py
  :lines: 11-13, 32-45 

Access to standard input is restored when the command is over.

Display banners under the prompt
--------------------------------

It is possible to display one-line animations under the prompt like loading bars or spinners for visual purpose.

.. literalinclude:: ../../tests/test_snippet.py
  :lines: 11-13, 46-53

.. automodule:: shell.shell
  :members:

.. automodule:: shell.command
  :members:

.. automodule:: shell.banner
  :members:
