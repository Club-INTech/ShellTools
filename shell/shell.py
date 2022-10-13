"""
Shell interface
"""

import asyncio as aio
import cmd
import threading
from contextlib import asynccontextmanager
from functools import partial
from queue import Queue
from sys import stdin, stdout
from typing import Callable, Coroutine, List, TextIO, TypeVar

import pynput
import terminology as tmg

from ..utility.synchronized_ostream import SynchronizedOStream

DEFAULT_PROMPT = "[shell] > "
KEYBOARD_LISTENER_REFRESH_DELAY_S = 10e-3


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
        self.__running_tasks: List[aio.Task] = []

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
        await self.__to_thread(self.cmdloop)
        self.log_status("Exiting the shell...", regenerate_prompt=False)
        for task in self.__running_tasks:
            task.cancel()

        # Yield to scheduler so running tasks can handle cancellation properly
        await aio.sleep(0)

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

    async def __to_thread(self, callback: Callable[[], None]):
        """
        Reimplement the behavior of `asyncio.to_thread` (which is not available for <3.9)
        """

        thread = threading.Thread(target=callback)
        thread.start()

        while thread.is_alive():
            await aio.sleep(0)

        thread.join()

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
        self.__running_tasks.append(task)

    def __finalize_task(
        self, task: aio.Task, cleanup_callback: Callable[[], None] = lambda: None
    ):
        """
        Handle a command finalization and call the cleaning callback
        When a task associated to a command is done, this function is invoked to handle potential exception.
        """
        try:
            cleanup_callback()
            self.__running_tasks.remove(task)
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
