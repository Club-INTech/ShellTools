ShellTools
==========

Quickly build command line interface to operate a remote target that uses `Unpadded <https://github.com/StarQTius/Unpadded>`_ over serial

Installation
------------

As a user
~~~~~~~~~

Add this repository as a submodule of your project.

.. code-block:: bash

  git submodule add https://github.com/Club-INTech/ShellTools
  git submodule update

Install the Python dependencies from ``requirements.txt``.

.. code-block:: bash
   
  pip3 install -r ShellTools/requirements.txt

`Unpadded <https://github.com/StarQTius/Unpadded>`_ will require `ccache <https://ccache.dev/>`_ to run. Install it from your packet manager (e.g. Aptitude).

.. code-block:: bash
   
  sudo apt install ccache

If you want a taste of the features provided by the ``shell`` package, you can run the demo shell.

.. code-block:: bash
   
  python3 ShellTools/demo.py

As a developper
~~~~~~~~~~~~~~~

If you want to contribute, please install the necessary development tools.

.. code-block:: bash
  
  sudo apt install ccache
  ./configure

Do not forget to test your installation afterwards.

.. code-block:: bash

   ./check  

.. toctree::
   shell/README
   remote/README
   tracker/README
