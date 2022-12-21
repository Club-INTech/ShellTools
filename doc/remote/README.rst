Handle a communication with a target through a serial line
==========================================================

The package ``remote`` can be used to communicate with a target which uses `Unpadded <https://github.com/StarQTius/Unpadded>`_.

Generating the extension module from the keyring
------------------------------------------------

First thing first, you must generate the extension module with `Unpadded <https://github.com/StarQTius/Unpadded>`_ so you use the keys and the keyring associated with the RPC convention you established. Refer to the documentation of this library to learn how to proceed.

Setting up the connection to the target
---------------------------------------

The ``Remote`` class uses `PySerial <https://pyserial.readthedocs.io/en/latest/>`_ to establish a connection to the target. You just need to provide the port to which the target is connected, a dispatcher which will handle the action request from the target and the key of the action used to store action response.

.. code-block:: python

  remote = Remote(port=..., dispatcher=..., reply_key=...)

Sending an action request to the target
---------------------------------------

Action requests are send to the target through the ``Remote.call`` method.

.. code-block:: python

  response = await remote.call(key, args...)

``remote`` API
--------------

.. automodule:: remote.remote
  :members:
