"""
Shell interface
"""

import asyncio as aio
import cmd
import os
from argparse import ArgumentParser, Namespace
from collections.abc import Callable, Coroutine
from sys import stdin, stdout
from textwrap import dedent
from typing import NoReturn, Optional, TextIO, TypeVar

import terminology as tmg

from ._synchronized_output import _SynchronizedOStream
from .utility import readline_extension as rle  # type: ignore

DEFAULT_PROMPT = "[shell] > "


class Shell(cmd.Cmd):
    def __init__(
        self,
        prompt: str = DEFAULT_PROMPT,
        istream: TextIO = stdin,
        ostream: TextIO = stdout,
    ):
        """
        Initialize the base class with IO streams
        `use_rawinput` will be set to `True` if and only if `istream` is `sys.stdin` and `ostream` is `sys.stdout`.
        """

        self.__istream = istream
        self.__ostream = _SynchronizedOStream(ostream, modifier=tmg.in_yellow)
        self.__prompt = prompt

        self.__use_rawinput = istream is stdin and ostream is stdout

        super().__init__(stdin=istream, stdout=self.__ostream)

    @property
    def prompt(self):
        """
        Shadows the `prompt` class attribute to make it instance-bound.
        """
        return "\r" + self.__prompt if self.__use_rawinput else ""

    @property
    def use_rawinput(self):
        """
        Shadows the `use_rawinput` class attribute to make it instance-bound.
        """
        return self.__use_rawinput

    def default(self, line):
        """
        Exit the shell if needed
        It overrides the base class method of the same name. It allows to leave the shell whatever the input line might be.
        """
        self.log_error("`" + tmg.in_bold(line.split()[0]) + "` is not a command")
        return not self.__continue

    def do_EOF(self, _) -> bool:
        """
        Exit the shell
        It is invoked when an end-of-file is received
        """
        return True

    async def run(self) -> None:
        """
        Start a shell session asynchronously
        """
        self.__loop = aio.get_event_loop()
        self.__continue = True
        await aio.to_thread(self.cmdloop)
        self.log_status("Exiting the shell...", regenerate_prompt=False)

    def create_task(self, coro: Coroutine) -> bool:
        """
        Schedule a coroutine to be carried out
        This method is thread-safe. This function is meant to schedule commands to be done. Thus, if the shell is stopping, this method will have no effect.
        """
        if not self.__continue:
            return True
        self.__loop.call_soon_threadsafe(self.__create_task, coro)
        return False

    def log(
        self,
        msg: str = "",
        modifier: Optional[Callable[[str], str]] = None,
        regenerate_prompt: bool = True,
    ) -> None:
        """
        Print the given message to the output stream
        A new line is inserted after the message.
        """
        line_eraser = "\r" + " " * os.get_terminal_size().columns + "\r"

        self.__ostream.acquire()

        if modifier and self.__use_rawinput:
            msg = modifier(msg)

        if self.__use_rawinput:
            self.__ostream.write_raw(line_eraser + msg + "\n")
        else:
            self.__ostream.write_raw(msg + "\n")

        if self.__use_rawinput and regenerate_prompt:
            rle.forced_update_display()

        self.__ostream.release()

    def log_error(self, msg: str, *args, **kwargs) -> None:
        self.log(msg, tmg.in_red, *args, **kwargs)

    def log_help(self, msg: str, *args, **kwargs) -> None:
        self.log(msg, tmg.in_green, *args, **kwargs)

    def log_status(self, msg: str, *args, **kwargs) -> None:
        self.log(msg, lambda x: tmg.in_yellow(tmg.in_bold(x)), *args, **kwargs)

    def __create_task(self, coro: Coroutine):
        """
        Schedule a coroutine to be carried out
        This method is not thread-safe and should only be called through `create_task`.
        """
        task = self.__loop.create_task(coro)
        task.add_done_callback(self.__finalize_task)

    def __finalize_task(self, task: aio.Task):
        """
        Handle a command finalization
        When a task associated to a command is done, this function is invoked to handle potential exception.
        """
        try:
            e = task.exception()
            if e is not None:
                raise e
        except ShellError as e:
            self.log_error(str(e))
        except Exception as e:
            self.__continue = False
            self.log_error(f"An unrecoverable error has occured : {e}")
            self.log_status("Press ENTER to quit.")


ShellType = TypeVar("ShellType", bound=Shell)


class ShellError(Exception):
    """
    Used to signal a recoverable error to the shell
    When caught, the shell is not interrupted contrary to the other kind of exception.
    """

    def __init__(self, message: str = None):
        super().__init__(message)


class _Wrapper:
    def __init__(self, f: Callable):
        """
        Hold a callable which will received the CLI arguments
        """
        self.__f = f

        doc = tmg.in_bold(dedent(f.__doc__)) if f.__doc__ else None
        self.parser = _Parser(prog=f.__name__, description=doc)

    async def __call__(self, shell: Shell, line: str) -> None:
        """
        Forward the accumulated CLI argument to the held callable
        """
        try:
            await self.__f(shell, **vars(self.parser.parse(shell, line)))
        except SystemExit:
            pass


def command(f: Callable[..., Coroutine] | _Wrapper) -> Callable[[ShellType, str], bool]:
    """
    Make a command compatible with the underlying `cmd.Cmd` class
    It should only be used on methods of a class derived from `Shell` whose identifiers begin with 'do_'.
    """
    return lambda self, line: self.create_task(_ensure_wrapper(f)(self, line))


def argument(*args, **kwargs) -> Callable[[Callable], Callable]:
    """
    Provide an argument specification
    This decorator behaves like the `ArgumentParser.add_argument` method. However, the result from the call of `ArgumentParser.parse_args` is unpacked to the command.
    """

    def impl(f):
        f = _ensure_wrapper(f)
        f.parser.add_argument(*args, **kwargs)
        return f

    return impl


def _ensure_wrapper(f: Callable[..., Coroutine] | _Wrapper) -> _Wrapper:
    """
    Wrap an async function if needed
    """
    if type(f) is _Wrapper:
        return f
    else:
        return _Wrapper(f)


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
        Instead of exiting the program, this method will raise a `ShellError()` if the parsing fails.
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
