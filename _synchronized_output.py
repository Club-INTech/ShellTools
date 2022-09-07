from threading import Lock
from typing import TextIO


class _SynchronizedOStream(TextIO):
    def __init__(self, ostream: TextIO):
        """
        Wrap an output stream
        """
        self.__ostream = ostream
        self.__lock = Lock()

    def __enter__(*_):
        raise NotImplementedError()

    def __exit__(*_):
        raise NotImplementedError()

    def __iter__(*_):
        raise NotImplementedError()

    def __next__(*_):
        raise NotImplementedError()

    def close(*_):
        raise NotImplementedError()

    def isatty(*_):
        raise NotImplementedError()

    def read(*_):
        raise NotImplementedError()

    def fileno(*_):
        raise NotImplementedError()

    def readable(*_):
        raise NotImplementedError()

    def readline(*_):
        raise NotImplementedError()

    def readlines(*_):
        raise NotImplementedError()

    def seek(*_):
        raise NotImplementedError()

    def seekable(*_):
        raise NotImplementedError()

    def tell(*_):
        raise NotImplementedError()

    def truncate(*_):
        raise NotImplementedError()

    def writable(*_):
        raise NotImplementedError()

    def writelines(*_):
        raise NotImplementedError()

    def write(self, msg: str) -> int:
        """
        Write a string to the wrapped output stream
        The lock is release if and only if `msg` is newline-terminated.
        """
        self.__lock.acquire()
        n = self.write_raw(msg)
        if n == 0 or msg[n - 1] == "\n":
            self.__lock.release()

        return n

    def flush(self) -> None:
        """
        Call the underlying stream `flush` method
        """
        return self.__ostream.flush()

    def write_raw(self, msg: str) -> int:
        """
        Write a string to the wrapped output stream without checking on the lock
        This method is not threadsafe.
        """
        return self.__ostream.write(msg)

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
