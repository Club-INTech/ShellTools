# Create an asynchronous command line interface with the Shell class

The `shell` package provides several utilities for building your own CLI. Defined commands can be asynchronous and synchronized output to the terminal is supported.

## Building a basic shell

Here is an example of a simple shell:

```default
    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)

    @command()
    @argument("msg", type=str)
    def do_print(self, msg):
        """
        Print a message
        """
        self.log_status(msg)

    @command()
    @argument("msg", type=str)
    @argument("n", type=int)
    async def do_nprint(self, msg, n):
        """
        Print `n` time a message with a 1 second delay in-between
        """
        for i in range(n):
            self.log_status(msg)
            await asyncio.sleep(1)

```

The syntax for the command themselves is simillar to the one from the [cmd](https://docs.python.org/3/library/cmd.html) library, but lots of features are differents:


* You do not need to parse the command line yourself, the decorators to the command methods do it for you.


* The `command` and `argument` decorators are used to specify the input parameters. `argument` accepts the same parameters as `ArgumentParser.add_argument` from [argparse](https://docs.python.org/3/library/argparse.html).


* Return value has no effect. The shell may only be exited by hitting `CTRL+D` or by raising an exception.

### Synchronous commands

`do_print` is defined as a synchronous method. As such, it is executed in one go. The command is not guarantee to be executed immeditely. However, it will run in the same thread as the one running the shell and will not be interrupted by another command once it has started.

### Asynchronous commands

`do_nprint` is defined a an asynchronous method. This command will run within an `asyncio` loop, which means you can use the `asyncio` API in the body of an asynchronous command. The command will be cancelled when the shell is exited. However, it is guaranteed that the command will never be cancelled before starting so you have the opportunity to handle the cancellation the way you like.

### Support for docstrings

When the user wish to see more information for a given command, the docstring of the command is automatically fetched and displayed. Additionally, the help string given for each parameter is also displayed.

## Capturing the keyboard input

:warning: This feature is poorly supported across terminals. If you want to use it, run your shell into a compatible terminal like `xterm`.

Instead of receiving command from the standard input, it is possible of directly capture input form keyboard.

```default
    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)


    @command(capture_keyboard="listener")
    async def do_print_key(self, listener):
        """
        Print the pressed key
        """
        from pynput.keyboard import Key
        
        while True:
            event_key = await listener.get()

            if event_key[0]:
                if event_key[1] == Key.esc:
                    return
```

Access to standard input is restored when the command is over.

## Display banners under the prompt

It is possible to display one-line animations under the prompt like loading bars or spinners for visual purpose.

```default
    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)

                print(repr(event_key[1]))

    @command()
    async def do_show_banner(self):
        """
        Print a funky banner for 3 seconds
        """
        async with self.banner(BarSpinner("Spinning..."), refresh_delay_s=60e-3):
```

## `shell` API


### [class]Shell(prompt=DEFAULT_PROMPT, istream=stdin, ostream=stdout)


* **banner(banner, refresh_delay_s)** 

Display a banner under the prompt

Only one banner can be displayed at a time.



* **create_task(coro, cleanup_callback=lambda : ...)** 

Schedule a coroutine to be carried out

This method is thread-safe. This function is meant to schedule commands to be done. Thus, if the shell is stopping, this method will have no effect.

A cleanup callback can be provided, which will be invoked when the task is done.

This method make sure the provided coroutine is given the chance to run at least once before another command is processed. This way, the coroutine will not be cancelled by an EOF or any other command that terminates the shell without being given the chance to handle the cancellation.



* **default(line)** 

Exit the shell if needed

It overrides the base class method of the same name. It allows to leave the shell whatever the input line might be.



* **do_EOF(_)** 

Exit the shell

It is invoked when an end-of-file is received



* **[property]is_running()** 

Indicate if the shell is not terminated or in termination



* **log(\*args, \*\*kwargs)** 

Log a message of any choosen style

`args` and `kwargs` are forwarded to `SynchronizedOStream.log`.



* **log_error(msg, \*args, \*\*kwargs)** 

Log an error



* **log_help(msg, \*args, \*\*kwargs)** 

Log a help message



* **log_status(msg, \*args, \*\*kwargs)** 

Log a status message



* **[property]prompt()** 

Shadows the `prompt` class attribute to make it instance-bound.



* **[async]run()** 

Start a shell session asynchronously

When the user decides to exit the shell, every running task will be cancelled, and the shell will wait for them to terminate.



* **[property]use_rawinput()** 

Shadows the `use_rawinput` class attribute to make it instance-bound.


### [exception]ShellError(message=None)
Used to signal a recoverable error to the shell

When caught, the shell is not interrupted contrary to the other kind of exception.

## `command` API


### argument(\*args, \*\*kwargs)
Provide an argument specification

This decorator behaves like the `ArgumentParser.add_argument` method. However, the result from the call of `ArgumentParser.parse_args` is unpacked to the command.


### command(capture_keyboard=None)
Make a command compatible with the underlying `cmd.Cmd` class

It should only be used on methods of a class derived from `Shell` whose identifiers begin with `do_`.

The command can choose to capture keyboard input with the parameter `capture_keyboard`. Its value should be the name of the command parameter which will receive the keyboard listener.

## `banner` API


### [class]BarSpinner(text='', modifier=lambda x: ...)
Preview :

`| Spinning... |▅▃▁▇`


### [class]ProgressBar(text='', modifier=lambda x: ..., bg_modifier_when_full=lambda x: ...)
Preview :
`| Hi ! |██████████████████████████████████████████`



* **[property]progress()** 

Current progress in percentage


### [class]TwoWayBar(text='', modifier=lambda x: ..., bg_modifier=lambda x: ...)
Preview :

`| Hello... |██████████████████████████████████████████████████████████`

…

`| Hello... |__________________________________________________________████████████████████████████████████████`



* **[property]progress()** 

Current progress in percentage
