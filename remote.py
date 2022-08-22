"""
Remote communication interface
"""

import asyncio as aio
import multiprocessing as mp
import time as tm
from collections import deque
from enum import Enum
from random import randint
from warnings import warn

import serial as sr
import unpadded as upd

from utility.match import Match

IO_REFRESH_DELAY_S = 50e-3
GET_ACTION_RESPONSE_DELAY_S = 1e-3
SERIAL_TIMEOUT_S = 500e-3


class Remote(upd.Client):
    """
    Handles a serial communication stream with a remote device
    """

    def __init__(self, port, dispatcher, reply_key):
        """
        Start listening to a serial port and hold a pipe to a tracker process
        """

        self.__pipe, remote_pipe = mp.Pipe()
        self.__dispatcher = dispatcher
        self.__loop = aio.get_event_loop()
        self.__future = None
        self.__process = mp.Process(
            target=_RemoteProcess(
                port=port, pipe=remote_pipe, dispatcher=dispatcher, reply_key=reply_key
            ),
            daemon=True,
        )
        self.__process.start()

    def new_request(self, payload):
        """
        Have the process send a new request
        Only one request can be pending at a time. If the user try to send a request while one is already pending, the pending request is awaited first.
        """
        if self.__future is not None:
            aio.wait(self.__future)
        self.__pipe.send(payload)
        self.__future = self.__loop.create_future()
        self.__request_response_awaiter = self.__loop.create_task(
            self.__get_action_response()
        )
        return self.__future

    async def __get_action_response(self):
        """
        Wait asynchronously for the pending request to be fulfilled
        This function is waiting for data to come from the process pipe.
        """
        while not self.__pipe.poll():
            await aio.sleep(GET_ACTION_RESPONSE_DELAY_S)
        self.__future.set_result(self.__pipe.recv())


class _RemoteProcess:
    """
    Manages the communication to the remote device and resolve request from the remote device
    """

    def __init__(self, port, pipe, dispatcher, reply_key):
        """
        Open the serial port to the device
        """
        self.__pipe = pipe
        self.__dispatcher = dispatcher
        self.__serial = sr.Serial(
            port=port,
            baudrate=115200,
            bytesize=sr.EIGHTBITS,
            parity=sr.PARITY_NONE,
            stopbits=sr.STOPBITS_ONE,
            timeout=SERIAL_TIMEOUT_S,
        )

        self.__dispatcher.replace(reply_key, lambda reply: self.__pipe.send(reply))

    def __call__(self):
        """
        Start the listening of the remote device
        """
        aio.run(self.__start())

    async def __start(self):
        """
        Receive request from the remote device and handle command from the control pipe
        """
        loop = aio.get_event_loop()
        handle_tx = loop.create_task(self.__handle_tx())
        handle_rx = loop.create_task(self.__handle_rx())
        await handle_tx
        await handle_rx

    async def __handle_tx(self):
        """
        Transmit the packets received from the main process want to send to the remote device
        """
        while True:
            if self.__pipe.poll():
                self.__serial.write(self.__pipe.recv())

            await aio.sleep(IO_REFRESH_DELAY_S)

    async def __handle_rx(self):
        """
        Receive the packets from the remote device and send them to the main process
        """
        while True:
            if self.__serial.in_waiting > 0:
                result = self.__dispatcher.resolve(
                    self.__serial.read(self.__serial.in_waiting)
                )
                if result != b"":
                    warn(
                        f"Action request from remote device would return non-empty response ({result}) which is not supported. The result will be discarded."
                    )

            await aio.sleep(IO_REFRESH_DELAY_S)
