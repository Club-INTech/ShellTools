# Handle a communication with a target through a serial line

The package `remote` can be used to communicate with a target which uses [Unpadded](https://github.com/StarQTius/Unpadded).

## Generating the extension module from the keyring

First thing first, you must generate the extension module with [Unpadded](https://github.com/StarQTius/Unpadded) so you use the keys and the keyring associated with the RPC convention you established. Refer to the documentation of this library to learn how to proceed.

## Setting up the connection to the target

The `Remote` class uses [PySerial](https://pyserial.readthedocs.io/en/latest/) to establish a connection to the target. You just need to provide the port to which the target is connected, a dispatcher which will handle the action request from the target and the key of the action used to store action response.

```python
remote = Remote(port=..., dispatcher=..., reply_key=...)
```

## Sending an action request to the target

Action requests are send to the target through the `Remote.call` method.

```python
response = await remote.call(key, args...)
```

## `remote` API


###  Remote(port, dispatcher, reply_key)
Handles a serial communication stream with a remote device



* **new_request(payload)** 

Have the process send a new request

Each request is given an UID which is used to keep track of the order of creation. The newest request are resolved first by the remote device.
