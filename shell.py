"""
Shell interface
"""

import asyncio as aio
import cmd
import os
import threading
from argparse import ArgumentParser, Namespace
from collections.abc import Callable, Coroutine
from contextlib import asynccontextmanager
from functools import partial
from queue import Queue
from sys import stdin, stdout
from textwrap import dedent
from typing import Any, NoReturn, Optional, TextIO, TypeVar

import pynput
import terminology as tmg

from .display.synchronized_ostream import SynchronizedOStream

DEFAULT_PROMPT = "[shell] > "
KEYBOARD_LISTENER_REFRESH_DELAY_S = 10e-3
KNOWN_COMPATIBLE_TERMINALS = ["xterm"]


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

        self.__use_rawinput = istream is stdin and ostream is stdout
        self.__istream = istream
        self.__ostream = SynchronizedOStream(
            ostream, use_rawinput=self.__use_rawinput, modifier=tmg.in_yellow
        )
        self.__prompt = prompt

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

    def create_task(
        self, coro: Coroutine, cleanup_callback: Callable[[], None] = lambda: None
    ) -> bool:
        """
        Schedule a coroutine to be carried out
        This method is thread-safe. This function is meant to schedule commands to be done. Thus, if the shell is stopping, this method will have no effect.
        A cleanup callback can be provided, which will be invoked when the task is done.
        """
        if not self.__continue:
            return True
        self.__loop.call_soon_threadsafe(self.__create_task, coro, cleanup_callback)
        return False

    def log(self, *args, **kwargs) -> None:
        """
        Log a message of any choosen style
        `args` and `kwargs` are forwarded to `SynchronizedOStream.log`.
        """
        self.__ostream.log(*args, **kwargs)

    def log_error(self, msg: str, *args, **kwargs) -> None:
        """
        Log an error
        """
        self.__ostream.log(msg, tmg.in_red, *args, **kwargs)

    def log_help(self, msg: str, *args, **kwargs) -> None:
        """
        Log a help message
        """
        self.__ostream.log(msg, tmg.in_green, *args, **kwargs)

    def log_status(self, msg: str, *args, **kwargs) -> None:
        """
        Log a status message
        """
        self.__ostream.log(
            msg, lambda x: tmg.in_yellow(tmg.in_bold(x)), *args, **kwargs
        )

    @asynccontextmanager
    async def banner(self, banner: str, refresh_delay_s: int):
        """
        Display a banner under the prompt
        Only one banner can be displayed at a time.
        """

        stop_event = aio.Event()
        update_banner_task = aio.create_task(
            self.__ostream.update_banner(
                banner, refresh_delay_s=refresh_delay_s, stop_event=stop_event
            )
        )

        yield banner

        stop_event.set()
        await update_banner_task

    def __create_task(
        self, coro: Coroutine, cleanup_callback: Callable[[], None] = lambda: None
    ):
        """
        Schedule a coroutine to be carried out
        This method is not thread-safe and should only be called through `create_task`.
        """
        task = self.__loop.create_task(coro)
        task.add_done_callback(
            partial(self.__finalize_task, cleanup_callback=cleanup_callback)
        )

    def __finalize_task(
        self, task: aio.Task, cleanup_callback: Callable[[], None] = lambda: None
    ):
        """
        Handle a command finalization and call the cleaning callback
        When a task associated to a command is done, this function is invoked to handle potential exception.
        """
        try:
            cleanup_callback()
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
        extra_parameters: dict[str, Any],
        cleanup: Callable[[dict[str, Any]], None],
        is_blocking: bool,
    ) -> bool:
        """
        Forward the accumulated CLI argument to the held async function
        The async function will also be given the `extra_parameters` keyword parameters.
        If `is_blocking` is `True`, the thread reading the standard input will block until the command is done.
        When the command is done, `cleanup` will be called.
        """
        try:
            result = self.__f(
                shell, **vars(self.parser.parse(shell, line)), **extra_parameters
            )
            cleanup_callback = lambda: cleanup(extra_parameters)
            if self.is_async:
                if is_blocking:
                    done_event = threading.Event()
                    shell.create_task(
                        _run_then_notify(result, done_event), cleanup_callback
                    )
                    done_event.wait()
                else:
                    shell.create_task(result, cleanup_callback)
        except SystemExit:
            pass

        return True


async def _run_then_notify(coro: Coroutine, done_event: threading.Event):
    """
    Await `coro` then notify the caller that `coro` is done through `done_event`
    This function is used to wait the completion of a coroutine from another thread.
    """
    await coro
    done_event.set()


def command(capture_keyboard: Optional[str] = None) -> Callable:
    """
    Make a command compatible with the underlying `cmd.Cmd` class
    It should only be used on methods of a class derived from `Shell` whose identifiers begin with 'do_'.
    The command can choose to capture keyboard input with the parameter `capture_keyboard`. Its value should be the name of the command parameter which will receive the keyboard listener.
    """

    def impl(f: Callable) -> Callable[[ShellType, str], bool]:
        nonlocal capture_keyboard

        wrapper = _ensure_wrapper(f)

        return lambda obj, line: startup(obj, line, wrapper)

    def startup(obj, line, wrapper):
        nonlocal capture_keyboard

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


class KeyboardListener:
    def __init__(self):
        self.__pynput_listener = pynput.keyboard.Listener(
            on_press=self.__push_pressed, on_release=self.__push_released, suppress=True
        )
        self.__event_lock = threading.Lock()

    def start(self):
        """
        Start listening to the keyboard
        """

        self.__event_queue = Queue()
        self.__pynput_listener.start()
        self.__pynput_listener.wait()

    def stop(self):
        """
        Stop listening to the keyboard
        """

        self.__pynput_listener.stop()

    async def get(self):
        """
        Wait for a keyboard event
        The return value has the format `(is_pressed, key)` with `is_pressed` equaling `True` if the event is a key press (otherwise, it is a key release) and `key` the `pynput.keyboard.Key` object associated with the pressed / released key.
        """

        while True:
            if not self.__event_queue.empty():
                return self.__event_queue.get_nowait()
            await aio.sleep(0)

    def __push_pressed(self, key: pynput.keyboard.Key):
        """
        Add a key press event to the queue
        This method is meant to be invoked from `__pynput_listener`.
        """

        if self.__event_lock.locked():
            return
        self.__event_lock.acquire()
        self.__event_queue.put((True, key))
        self.__release_lock_later()

    def __push_released(self, key: pynput.keyboard.Key):
        """
        Add a key release event to the queue
        This method is meant to be invoked from `__pynput_listener`.
        """

        if self.__event_lock.locked():
            return
        self.__event_lock.acquire()
        self.__event_queue.put((False, key))
        self.__release_lock_later()

    def __release_lock_later(self):
        """
        Release the lock on the event callbacks after `KEYBOARD_LISTENER_REFRESH_DELAY_S` seconds
        This method is used within the event callbacks in order to slow down the arrival rate of the keyboard events.
        """

        threading.Timer(
            KEYBOARD_LISTENER_REFRESH_DELAY_S, self.__event_lock.release
        ).start()


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
    if isinstance(f, _Wrapper):
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
