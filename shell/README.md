# Create an asynchronous command line interface with the Shell class

The `shell` package provides several utilities for building your own CLI. Defined commands can be asynchronous and synchronized output to the terminal is supported.

## Building a basic shell

Here is an example of a simple shell:

```default
class MyShell(Shell):
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

**WARNING**: This feature is poorly supported across terminals. If you want to use it, run your shell into a compatible terminal like `xterm`.

Instead of receiving command from the standard input, it is possible of directly capture input form keyboard.

```default
class MyShell(Shell):
    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)
            await asyncio.sleep(1)

    @command(capture_keyboard="listener")
    async def do_print_key(self, listener):
        """
        Print the pressed key
        """
        while True:
            event_key = await listener.get()

            if event_key[0]:
                if event_key[1] == Key.esc:
                    return
                print(repr(event_key[1]))
```

Access to standard input is restored when the command is over.

## Display banners under the prompt

It is possible to display one-line animations under the prompt like loading bars or spinners for visual purpose.

```default
class MyShell(Shell):
    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)

    @command()
    async def do_show_banner(self):
        """
        Print a funky banner for 3 seconds
        """
        async with self.banner(BarSpinner("Spinning..."), refresh_delay_s=60e-3):
            await asyncio.sleep(3)
```

Shell interface


### _class_ shell.shell.KeyboardListener()

#### _async_ get()
Wait for a keyboard event
The return value has the format (is_pressed, key) with is_pressed equaling True if the event is a key press (otherwise, it is a key release) and key the pynput.keyboard.Key object associated with the pressed / released key.


#### start()
Start listening to the keyboard


#### stop()
Stop listening to the keyboard


### _class_ shell.shell.Shell(prompt: str = '[shell] > ', istream: ~typing.TextIO = <_io.TextIOWrapper name='<stdin>' mode='r' encoding='utf-8'>, ostream: ~typing.TextIO = <_io.TextIOWrapper name='<stdout>' mode='w' encoding='utf-8'>)

#### banner(banner: str, refresh_delay_s: int)
Display a banner under the prompt
Only one banner can be displayed at a time.


#### call_soon(f: ~typing.Callable, \*args, cleanup_callback: ~typing.Callable[[], None] = <function Shell.<lambda>>, \*\*kwargs)

#### create_task(coro: ~typing.Coroutine, cleanup_callback: ~typing.Callable[[], None] = <function Shell.<lambda>>)
Schedule a coroutine to be carried out
This method is thread-safe. This function is meant to schedule commands to be done. Thus, if the shell is stopping, this method will have no effect.
A cleanup callback can be provided, which will be invoked when the task is done.
This method make sure the provided coroutine is given the chance to run at least once before another command is processed. This way, the coroutine will not be cancelled by an EOF or any other command that terminates the shell without being given the chance to handle the cancellation.


#### default(line)
Exit the shell if needed
It overrides the base class method of the same name. It allows to leave the shell whatever the input line might be.


#### do_EOF(_)
Exit the shell
It is invoked when an end-of-file is received


#### _property_ is_running(_: boo_ )
Indicate if the shell is not terminated or in termination


#### log(\*args, \*\*kwargs)
Log a message of any choosen style
args and kwargs are forwarded to SynchronizedOStream.log.


#### log_error(msg: str, \*args, \*\*kwargs)
Log an error


#### log_help(msg: str, \*args, \*\*kwargs)
Log a help message


#### log_status(msg: str, \*args, \*\*kwargs)
Log a status message


#### _property_ prompt()
Shadows the prompt class attribute to make it instance-bound.


#### _async_ run()
Start a shell session asynchronously
When the user decides to exit the shell, every running task will be cancelled, and the shell will wait for them to terminate.


#### _property_ use_rawinput()
Shadows the use_rawinput class attribute to make it instance-bound.


### _exception_ shell.shell.ShellError(message: Optional[str] = None)
Used to signal a recoverable error to the shell
When caught, the shell is not interrupted contrary to the other kind of exception.


### shell.command.argument(\*args, \*\*kwargs)
Provide an argument specification
This decorator behaves like the ArgumentParser.add_argument method. However, the result from the call of ArgumentParser.parse_args is unpacked to the command.


### shell.command.command(capture_keyboard: Optional[str] = None)
Make a command compatible with the underlying cmd.Cmd class
It should only be used on methods of a class derived from Shell whose identifiers begin with ‘

```
do_
```

’.
The command can choose to capture keyboard input with the parameter capture_keyboard. Its value should be the name of the command parameter which will receive the keyboard listener.


### _class_ shell.banner.BarSpinner(text: str = '', modifier: ~typing.Callable[[str], str] = <function BarSpinner.<lambda>>)
Preview :
| Spinning… |▅▃▁▇


#### PATTERN(_ = '▁▂▃▄▅▆▇█_ )

### _class_ shell.banner.ProgressBar(text: str = '', modifier: ~typing.Callable[[str], str] = <function ProgressBar.<lambda>>, bg_modifier_when_full: ~typing.Callable[[str], str] = <function ProgressBar.<lambda>>)
Preview :
| Hi ! |██████████████████████████████████████████


#### _property_ progress(_: floa_ )
Current progress in percentage


### _class_ shell.banner.TwoWayBar(text: str = '', modifier: ~typing.Callable[[str], str] = <function TwoWayBar.<lambda>>, bg_modifier: ~typing.Callable[[str], str] = <function TwoWayBar.<lambda>>)
Preview :
| Hello… 

```
|
```

██████████████████████████████████████████████████████████
…
| Hello… |                                                          ████████████████████████████████████████


#### _property_ progress(_: floa_ )
Current progress in percentage
