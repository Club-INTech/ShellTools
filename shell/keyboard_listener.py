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

from utility.synchronized_ostream import SynchronizedOStream

DEFAULT_PROMPT = "[shell] > "
KEYBOARD_LISTENER_REFRESH_DELAY_S = 10e-3

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
        The return value has the format ``(is_pressed, key)`` with ``is_pressed`` equaling ``True`` if the event is a key press (otherwise, it is a key release) and ``key`` the ``pynput.keyboard.Key`` object associated with the pressed / released key.
        """

        while True:
            if not self.__event_queue.empty():
                return self.__event_queue.get_nowait()
            await aio.sleep(0)

    def __push_pressed(self, key: pynput.keyboard.Key):
        """
        Add a key press event to the queue
        This method is meant to be invoked from ``__pynput_listener``.
        """

        if self.__event_lock.locked():
            return
        self.__event_lock.acquire()
        self.__event_queue.put((True, key))
        self.__release_lock_later()

    def __push_released(self, key: pynput.keyboard.Key):
        """
        Add a key release event to the queue
        This method is meant to be invoked from ``__pynput_listener``.
        """

        if self.__event_lock.locked():
            return
        self.__event_lock.acquire()
        self.__event_queue.put((False, key))
        self.__release_lock_later()

    def __release_lock_later(self):
        """
        Release the lock on the event callbacks after ``KEYBOARD_LISTENER_REFRESH_DELAY_S`` seconds
        This method is used within the event callbacks in order to slow down the arrival rate of the keyboard events.
        """

        threading.Timer(
            KEYBOARD_LISTENER_REFRESH_DELAY_S, self.__event_lock.release
        ).start()
