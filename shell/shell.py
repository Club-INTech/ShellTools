import asyncio as aio
import cmd
import threading
from contextlib import asynccontextmanager
from functools import partial
from queue import Queue
from sys import stdin, stdout
from typing import Callable, Coroutine, List, TextIO, TypeVar, Optional

import terminology as tmg

from utility.synchronized_ostream import SynchronizedOStream

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
        ``use_rawinput`` will be set to ``True`` if and only if ``istream`` is ``sys.stdin`` and ``ostream`` is ``sys.stdout``.
        """

        self.__use_rawinput = istream is stdin and ostream is stdout
        self.__istream = istream
        self.__ostream = SynchronizedOStream(
            ostream, use_rawinput=self.__use_rawinput, modifier=tmg.in_yellow
        )
        self.__prompt = prompt
        self.__running_tasks: List[aio.Task] = []
        self.__continue = False

        super().__init__(stdin=istream, stdout=self.__ostream)

    @property
    def prompt(self):
        """
        Shadows the ``prompt`` class attribute to make it instance-bound.
        """
        return "\r" + self.__prompt if self.__use_rawinput else ""

    @property
    def use_rawinput(self):
        """
        Shadows the ``use_rawinput`` class attribute to make it instance-bound.
        """
        return self.__use_rawinput

    def default(self, line):
        """
        Exit the shell if needed
        It overrides the base class method of the same name. It allows to leave the shell whatever the input line might be.
        """
        if not self.__continue:
            return True

        self.log_error("`" + tmg.in_bold(line.split()[0]) + "` is not a command")

    def do_EOF(self, _) -> bool:
        """
        Exit the shell
        It is invoked when an end-of-file is received
        """
        self.__continue = False
        return True

    async def run(self) -> None:
        """
        Start a shell session asynchronously
        When the user decides to exit the shell, every running task will be cancelled, and the shell will wait for them to terminate.
        """
        self.__loop = aio.get_event_loop()
        self.__continue = True
        await self.__to_thread(self.cmdloop)

        self.log_status("Exiting the shell...", regenerate_prompt=False)

        for task in self.__running_tasks:
            task.cancel()

        while self.__running_tasks != []:
            await aio.sleep(0)

    @property
    def is_running(self) -> bool:
        """
        Indicate if the shell is not terminated or in termination
        """
        return self.__continue

    def call_soon(
        self,
        f: Callable,
        *args,
        cleanup_callback: Callable[[], None] = lambda: None,
        **kwargs,
    ) -> None:
        async def impl(f, *args, **kwargs):
            f(*args, **kwargs)

        self.create_task(impl(f, *args, **kwargs), cleanup_callback)

    def create_task(
        self, coro: Coroutine, cleanup_callback: Callable[[], None] = lambda: None
    ) -> None:
        """
        Schedule a coroutine to be carried out
        This method is thread-safe. This function is meant to schedule commands to be done. Thus, if the shell is stopping, this method will have no effect.
        A cleanup callback can be provided, which will be invoked when the task is done.
        This method make sure the provided coroutine is given the chance to run at least once before another command is processed. This way, the coroutine will not be cancelled by an EOF or any other command that terminates the shell without being given the chance to handle the cancellation.
        """
        task_running_event = threading.Event()
        self.__loop.call_soon_threadsafe(
            self.__create_task, coro, cleanup_callback, task_running_event
        )
        task_running_event.wait()

    def log(self, *args, **kwargs) -> None:
        """
        Log a message of any choosen style
        ``args`` and ``kwargs`` are forwarded to ``SynchronizedOStream.log``.
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
        Reimplement the behavior of ``asyncio.to_thread`` (which is not available for <3.9)
        """

        thread = threading.Thread(target=callback)
        thread.start()

        while thread.is_alive():
            await aio.sleep(0)

        thread.join()

    def __create_task(
        self,
        coro: Coroutine,
        cleanup_callback: Callable[[], None],
        event: threading.Event,
    ):
        """
        Schedule a coroutine to be carried out
        This method is not thread-safe and should only be called through ``create_task``.
        """

        async def impl(coro, event):
            event.set()
            await coro

        task = self.__loop.create_task(impl(coro, event))
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

            if task.cancelled():
                return

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

    def __init__(self, message: Optional[str] = None):
        super().__init__(message)
