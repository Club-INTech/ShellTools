import asyncio as aio
import os
import threading
from argparse import ArgumentParser, Namespace
from textwrap import dedent
from typing import Any, Callable, Coroutine, Dict, NoReturn, Optional, Union

import terminology as tmg

from .keyboard_listener import KeyboardListener
from .shell import Shell, ShellType

KNOWN_COMPATIBLE_TERMINALS = ["xterm"]


def command(capture_keyboard: Optional[str] = None) -> Callable:
    """
    Make a command compatible with the underlying ``cmd.Cmd`` class
    It should only be used on methods of a class derived from ``Shell`` whose identifiers begin with ``do_``.
    The command can choose to capture keyboard input with the parameter ``capture_keyboard``. Its value should be the name of the command parameter which will receive the keyboard listener.
    """

    def impl(f: Callable) -> Callable[[ShellType, str], bool]:
        nonlocal capture_keyboard

        wrapper = _ensure_wrapper(f)

        return lambda obj, line: startup(obj, line, wrapper)

    def startup(obj, line, wrapper):
        nonlocal capture_keyboard

        if not obj.is_running:
            return True

        extra_parameters = {}
        is_blocking = False

        if capture_keyboard is not None:
            if not "TERM" in os.environ:
                obj.log_status(
                    "The terminal name could not be retreived. It might not be a problem, but do note that pyinput will not work with any terminal. If possible, run this program under a compatible terminal (xterm for example)."
                )

            terminal_name = os.environ["TERM"]
            if terminal_name not in KNOWN_COMPATIBLE_TERMINALS:
                obj.log_status(
                    f"{terminal_name} might not be compatible with pyinput. If possible, run this program under a compatible terminal (xterm for example)."
                )

            is_blocking = True
            extra_parameters[capture_keyboard] = KeyboardListener()
            extra_parameters[capture_keyboard].start()

        wrapper.call_command(obj, line, extra_parameters, cleanup, is_blocking)

    def cleanup(extra_parameters):
        nonlocal capture_keyboard

        if capture_keyboard is not None:
            extra_parameters[capture_keyboard].stop()

    return impl


def argument(*args, **kwargs) -> Callable[[Callable], Callable]:
    """
    Provide an argument specification
    This decorator behaves like the ``ArgumentParser.add_argument`` method. However, the result from the call of ``ArgumentParser.parse_args`` is unpacked to the command.
    """

    def impl(f):
        f = _ensure_wrapper(f)
        f.parser.add_argument(*args, **kwargs)
        return f

    return impl


class _Wrapper:
    def __init__(self, f: Callable):
        """
        Hold a callable which will received the CLI arguments
        """
        self.__f = f

        doc = tmg.in_bold(dedent(f.__doc__)) if f.__doc__ else None
        self.parser = _Parser(prog=f.__name__, description=doc)

    @property
    def is_async(self) -> bool:
        """
        Tell whether the stored callable is an async function
        """
        return aio.iscoroutinefunction(self.__f)

    def call_command(
        self,
        shell: Shell,
        line: str,
        extra_parameters: Dict[str, Any],
        cleanup: Callable[[Dict[str, Any]], None],
        is_blocking: bool,
    ) -> bool:
        """
        Forward the accumulated CLI argument to the held async function
        The async function will also be given the ``extra_parameters`` keyword parameters.
        If ``is_blocking`` is ``True``, the thread reading the standard input will block until the command is done.
        When the command is done, ``cleanup`` will be called.
        """
        cleanup_callback = lambda: cleanup(extra_parameters)

        try:
            if self.is_async:
                coro = self.__f(
                    shell, **vars(self.parser.parse(shell, line)), **extra_parameters
                )
                if is_blocking:
                    done_event = threading.Event()
                    shell.create_task(
                        _run_then_notify(coro, done_event), cleanup_callback
                    )
                    done_event.wait()
                else:
                    shell.create_task(coro, cleanup_callback)
            else:
                shell.call_soon(
                    self.__f,
                    shell,
                    **vars(self.parser.parse(shell, line)),
                    **extra_parameters,
                    cleanup_callback=cleanup_callback,
                )
        except SystemExit:
            pass
        finally:
            if not self.is_async:
                cleanup_callback()

        return True


class _Parser(ArgumentParser):
    def __init__(self, *args, **kwargs):
        """
        Initialize the underlying parser
        """
        super().__init__(
            *args,
            **kwargs,
        )

    def parse(self, shell: Shell, line: str) -> Namespace:
        """
        Parse the argument from a command line
        Instead of exiting the program, this method will raise a ``ShellError()`` if the parsing fails.
        """
        self.__shell = shell
        return self.parse_args(line.split())

    def print_usage(self, _=None) -> None:
        """
        Print the usage string to the output stream of the shell
        """
        self.__shell.log_error(self.format_usage().strip())

    def print_help(self, _=None) -> None:
        """
        Print the help string to the output stream of the shell
        """
        self.__shell.log_help(self.format_help())

    def error(self, msg: str) -> NoReturn:
        """
        Print the usage and the reason of the parsing failure
        """
        self.print_usage()
        self.__shell.log_error(msg)
        raise SystemExit()

    def _print_message(self, message: str, _=None) -> None:
        """
        Print to the output stream
        It overrides the method of the base class so it does not write to the standard error.
        """
        self.__shell.log(message)


async def _run_then_notify(coro: Coroutine, done_event: threading.Event):
    """
    Await ``coro`` then notify the caller that ``coro`` is done through ``done_event``
    This function is used to wait the completion of a coroutine from another thread.
    """
    await coro
    done_event.set()


def _ensure_wrapper(f: Union[Callable[..., Coroutine], _Wrapper]) -> _Wrapper:
    """
    Wrap an async function if needed
    """
    if isinstance(f, _Wrapper):
        return f
    else:
        return _Wrapper(f)
