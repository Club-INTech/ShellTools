import asyncio as aio
import io
import os
from collections.abc import Callable
from itertools import chain
from threading import Lock
from typing import Iterable, List, NoReturn, Optional, TextIO

from . import readline_extension as rle  # type: ignore

UP_GOER = "\033[F"


class SynchronizedOStream(TextIO):
    def __init__(
        self, ostream: TextIO, use_rawinput: bool, modifier: Callable[[str], str]
    ):
        """
        Wrap an output stream
        """
        self.__ostream = ostream
        self.__lock = Lock()
        self.__use_rawinput = use_rawinput
        self.__modifier = modifier
        self.__in_context = False
        self.__banners: List[str] = []

    def __enter__(self) -> "SynchronizedOStream":
        """
        Acquire the stream
        Call to methods other than `__exit__` will not have any effect on the lock after entering the context (for example, `write` will not try to release the stream).
        """
        self.__lock.acquire()
        self.__in_context = True
        return self

    def __exit__(self, *_) -> None:
        """
        Release the stream
        """
        self.__in_context = False
        self.__lock.release()

    def __iter__(*_) -> NoReturn:
        raise NotImplementedError()

    def __next__(*_) -> NoReturn:
        raise NotImplementedError()

    def close(self) -> None:
        return self.__ostream.close()

    def isatty(self) -> bool:
        return self.__ostream.isatty()

    def read(self, *_) -> NoReturn:
        raise NotImplementedError()

    def fileno(self) -> int:
        return self.__ostream.fileno()

    def readable(self) -> bool:
        return False

    def readline(self, *_) -> NoReturn:
        raise NotImplementedError()

    def readlines(self, *_) -> NoReturn:
        raise NotImplementedError()

    def seek(self, offset: int, whence: int = io.SEEK_SET) -> int:
        return self.__ostream.seek(offset, whence)

    def seekable(self) -> bool:
        return self.__ostream.seekable()

    def tell(self) -> int:
        return self.__ostream.tell()

    def truncate(self, size: Optional[int] = None) -> int:
        return self.__ostream.truncate(size)

    def writable(self) -> bool:
        return self.__ostream.writable()

    def writelines(self, lines: Iterable[str]) -> None:
        """
        Write several lines consecutively
        """
        self.__ostream.write(str(chain(lines)))

    def write(self, msg: str) -> int:
        """
        Write a string to the wrapped output stream
        If this stream has not been locked yet with the context manager, the lock is released if and only if `msg` is newline-terminated or is empty.
        """

        if msg == "":
            return 0

        if not self.__in_context:
            self.__lock.acquire()
        n = self.__ostream.write(
            self.__modifier(msg) if self.__in_context and self.__use_rawinput else msg
        )
        if msg[-1] == "\n" and not self.__in_context:
            self.__lock.release()

        return n

    def flush(self) -> None:
        """
        Call the underlying stream `flush` method
        """
        return self.__ostream.flush()

    def log(
        self,
        msg: str,
        modifier: Optional[Callable[[str], str]] = None,
        regenerate_prompt: bool = True,
    ) -> None:
        """
        Print the given message to the output stream
        A new line is inserted after the message.
        """

        with self:
            if modifier and self.__use_rawinput:
                msg = modifier(msg)

            if self.__use_rawinput:
                msg = _linewiper(msg)
                for i, banner in enumerate(self.__banners):
                    msg += _below(str(banner), position=i) + _linewiper()
            else:
                msg += "\n"

            self.__ostream.write(msg)

            if self.__use_rawinput and regenerate_prompt:
                rle.forced_update_display()

    async def update_banner(
        self, banner: str, refresh_delay_s: int, stop_event: aio.Event
    ) -> None:
        """
        Add a banner to display, update its output regulary and remove it
        The banner update can be stopped by setting `stop_event`.
        """
        self.__banners.append(banner)

        if not self.__use_rawinput:
            return

        with self:
            self.__ostream.write(_below(str(banner)))
            rle.forced_update_display()

        while not stop_event.is_set():
            with self:
                self.__ostream.write(
                    _below(str(banner), position=self.__banners.index(banner))
                    + _linewiper()
                )
                rle.forced_update_display()
            await aio.sleep(refresh_delay_s)

        with self:
            self.__ostream.write(_below(position=self.__banners.index(banner)))
            rle.forced_update_display()

        self.__banners.remove(banner)

    def acquire(self) -> None:
        """
        Acquire the output stream
        """
        self.__lock.acquire()

    def release(self) -> None:
        """
        Release the output stream
        """
        self.__lock.release()


def _linewiper(msg: Optional[str] = None) -> str:
    """
    Return a string that can erase a whole line in the current terminal
    With no argument, the line is just wiped and no newlines are inserted.
    """
    return (
        "\r"
        + " " * os.get_terminal_size().columns
        + "\r"
        + (msg + "\n" if msg is not None else "")
    )


def _below(msg: str = "", position: int = 0) -> str:
    """
    Write a message below the cursor and go back up at the beginning of the line
    A message can be printed several lines below with the `position` parameter.
    """
    return (
        "\n" * (position + 1)
        + " " * os.get_terminal_size().columns
        + "\r"
        + msg
        + UP_GOER * (position + 1)
    )
