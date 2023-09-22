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


* [Create an asynchronous command line interface with the Shell class](shelltools/shell/README.md)


    * [Building a basic shell](shelltools/shell/README.md#building-a-basic-shell)


        * [Synchronous commands](shelltools/shell/README.md#synchronous-commands)


        * [Asynchronous commands](shelltools/shell/README.md#asynchronous-commands)


        * [Support for docstrings](shelltools/shell/README.md#support-for-docstrings)


    * [Capturing the keyboard input](shelltools/shell/README.md#capturing-the-keyboard-input)


    * [Display banners under the prompt](shelltools/shell/README.md#display-banners-under-the-prompt)


    * [`shell` API](shelltools/shell/README.md#module-shelltools.shell.shell)


        * [`Shell`](shelltools/shell/README.md#shelltools.shell.shell.Shell)


            * [`Shell.banner()`](shelltools/shell/README.md#shelltools.shell.shell.Shell.banner)


            * [`Shell.create_task()`](shelltools/shell/README.md#shelltools.shell.shell.Shell.create_task)


            * [`Shell.default()`](shelltools/shell/README.md#shelltools.shell.shell.Shell.default)


            * [`Shell.do_EOF()`](shelltools/shell/README.md#shelltools.shell.shell.Shell.do_EOF)


            * [`Shell.is_running`](shelltools/shell/README.md#shelltools.shell.shell.Shell.is_running)


            * [`Shell.log()`](shelltools/shell/README.md#shelltools.shell.shell.Shell.log)


            * [`Shell.log_error()`](shelltools/shell/README.md#shelltools.shell.shell.Shell.log_error)


            * [`Shell.log_help()`](shelltools/shell/README.md#shelltools.shell.shell.Shell.log_help)


            * [`Shell.log_status()`](shelltools/shell/README.md#shelltools.shell.shell.Shell.log_status)


            * [`Shell.prompt`](shelltools/shell/README.md#shelltools.shell.shell.Shell.prompt)


            * [`Shell.run()`](shelltools/shell/README.md#shelltools.shell.shell.Shell.run)


            * [`Shell.use_rawinput`](shelltools/shell/README.md#shelltools.shell.shell.Shell.use_rawinput)


        * [`ShellError`](shelltools/shell/README.md#shelltools.shell.shell.ShellError)


    * [`command` API](shelltools/shell/README.md#module-shelltools.shell.command)


        * [`argument()`](shelltools/shell/README.md#shelltools.shell.command.argument)


        * [`command()`](shelltools/shell/README.md#shelltools.shell.command.command)


    * [`banner` API](shelltools/shell/README.md#module-shelltools.shell.banner)


        * [`BarSpinner`](shelltools/shell/README.md#shelltools.shell.banner.BarSpinner)


        * [`ProgressBar`](shelltools/shell/README.md#shelltools.shell.banner.ProgressBar)


            * [`ProgressBar.progress`](shelltools/shell/README.md#shelltools.shell.banner.ProgressBar.progress)


        * [`TwoWayBar`](shelltools/shell/README.md#shelltools.shell.banner.TwoWayBar)


            * [`TwoWayBar.progress`](shelltools/shell/README.md#shelltools.shell.banner.TwoWayBar.progress)


* [Handle a communication with a target through a serial line](shelltools/remote/README.md)


    * [Generating the extension module from the keyring](shelltools/remote/README.md#generating-the-extension-module-from-the-keyring)


    * [Setting up the connection to the target](shelltools/remote/README.md#setting-up-the-connection-to-the-target)


    * [Sending an action request to the target](shelltools/remote/README.md#sending-an-action-request-to-the-target)


    * [`remote` API](shelltools/remote/README.md#module-shelltools.remote.remote)


        * [`Remote`](shelltools/remote/README.md#shelltools.remote.remote.Remote)


            * [`Remote.new_request()`](shelltools/remote/README.md#shelltools.remote.remote.Remote.new_request)
