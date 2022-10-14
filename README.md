# ShellTools

## Quickly build command line interface to operate a remote target that uses [Unpadded](https://github.com/StarQTius/Unpadded) over serial

With this package, you can :


* Build an asynchronous shell which handles synchronized output


* Send and receive action requests from a remote target through serial communication


* Track position data and process them


* Display asynchronous animations under your shell prompt


* [Create an asynchronous command line interface with the Shell class](shell/README.md)


    * [Building a basic shell](shell/README.md#building-a-basic-shell)


        * [Synchronous commands](shell/README.md#synchronous-commands)


        * [Asynchronous commands](shell/README.md#asynchronous-commands)


        * [Support for docstrings](shell/README.md#support-for-docstrings)


    * [Capturing the keyboard input](shell/README.md#capturing-the-keyboard-input)


    * [Display banners under the prompt](shell/README.md#display-banners-under-the-prompt)


* [Handle a communication with a target through a serial line](remote/README.md)


    * [Generating the extension module from the keyring](remote/README.md#generating-the-extension-module-from-the-keyring)


    * [Setting up the connection to the target](remote/README.md#setting-up-the-connection-to-the-target)


    * [Sending an action request to the target](remote/README.md#sending-an-action-request-to-the-target)
