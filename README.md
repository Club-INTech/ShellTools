# ShellTools

Quickly build command line interface to operate a remote target that uses [Unpadded](https://github.com/StarQTius/Unpadded) over serial

## Installation

### As a user

Add this repository as a submodule of your project.

```bash
git submodule add https://github.com/Club-INTech/ShellTools
git submodule update
```

Install the Python dependencies from `requirements.txt`.

```bash
pip3 install -r ShellTools/requirements.txt
```

[Unpadded](https://github.com/StarQTius/Unpadded) will require [ccache](https://ccache.dev/) to run. Install it from your packet manager (e.g. Aptitude).

```bash
sudo apt install ccache
```

If you want a taste of the features provided by the `shell` package, you can run the demo shell.

```bash
python3 ShellTools/demo.py
```

### As a developper

If you want to contribute, please install the necessary development tools.

```bash
sudo apt install ccache
./configure
```

Do not forget to test your installation afterwards.

```bash
./check
```


* [Create an asynchronous command line interface with the Shell class](shell/README.md)


    * [Building a basic shell](shell/README.md#building-a-basic-shell)


        * [Synchronous commands](shell/README.md#synchronous-commands)


        * [Asynchronous commands](shell/README.md#asynchronous-commands)


        * [Support for docstrings](shell/README.md#support-for-docstrings)


    * [Capturing the keyboard input](shell/README.md#capturing-the-keyboard-input)


    * [Display banners under the prompt](shell/README.md#display-banners-under-the-prompt)


    * [`shell` API](shell/README.md#module-shell.shell)


        * [`Shell`](shell/README.md#shell.shell.Shell)


            * [`Shell.banner()`](shell/README.md#shell.shell.Shell.banner)


            * [`Shell.create_task()`](shell/README.md#shell.shell.Shell.create_task)


            * [`Shell.default()`](shell/README.md#shell.shell.Shell.default)


            * [`Shell.do_EOF()`](shell/README.md#shell.shell.Shell.do_EOF)


            * [`Shell.is_running`](shell/README.md#shell.shell.Shell.is_running)


            * [`Shell.log()`](shell/README.md#shell.shell.Shell.log)


            * [`Shell.log_error()`](shell/README.md#shell.shell.Shell.log_error)


            * [`Shell.log_help()`](shell/README.md#shell.shell.Shell.log_help)


            * [`Shell.log_status()`](shell/README.md#shell.shell.Shell.log_status)


            * [`Shell.prompt`](shell/README.md#shell.shell.Shell.prompt)


            * [`Shell.run()`](shell/README.md#shell.shell.Shell.run)


            * [`Shell.use_rawinput`](shell/README.md#shell.shell.Shell.use_rawinput)


        * [`ShellError`](shell/README.md#shell.shell.ShellError)


    * [`command` API](shell/README.md#module-shell.command)


        * [`argument()`](shell/README.md#shell.command.argument)


        * [`command()`](shell/README.md#shell.command.command)


    * [`banner` API](shell/README.md#module-shell.banner)


        * [`BarSpinner`](shell/README.md#shell.banner.BarSpinner)


        * [`ProgressBar`](shell/README.md#shell.banner.ProgressBar)


            * [`ProgressBar.progress`](shell/README.md#shell.banner.ProgressBar.progress)


        * [`TwoWayBar`](shell/README.md#shell.banner.TwoWayBar)


            * [`TwoWayBar.progress`](shell/README.md#shell.banner.TwoWayBar.progress)


* [Handle a communication with a target through a serial line](remote/README.md)


    * [Generating the extension module from the keyring](remote/README.md#generating-the-extension-module-from-the-keyring)


    * [Setting up the connection to the target](remote/README.md#setting-up-the-connection-to-the-target)


    * [Sending an action request to the target](remote/README.md#sending-an-action-request-to-the-target)


    * [`remote` API](remote/README.md#module-remote.remote)


        * [`Remote`](remote/README.md#remote.remote.Remote)


            * [`Remote.new_request()`](remote/README.md#remote.remote.Remote.new_request)
