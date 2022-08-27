"""
Remote communication interface
"""

import asyncio as aio
import multiprocessing as mp
from warnings import warn

import serial as sr
import unpadded as upd

from utility.match import Match

IO_REFRESH_DELAY_S = 50e-3
RESPONSE_CHECK_DELAY_S = 1e-3
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
        self.__active_request_uid, self.__next_request_uid = 0, 0
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
        Each request is given an UID which is used to keep track of the order of creation. The newest request are resolved first by the remote device.
        """
        self.__pipe.send(payload)
        request_awaiter = self.__loop.create_task(
            self.__get_response(self.__next_request_uid)
        )
        self.__next_request_uid += 1
        return request_awaiter

    async def __get_response(self, uid):
        """
        Wait asynchronously for the pending request with the given UID to be resolved
        The responses are received in the same order as the requests, so the coroutine wait for the other requests with lesser UID to be resolved first.
        """
        while not (self.__active_request_uid == uid and self.__pipe.poll()):
            await aio.sleep(RESPONSE_CHECK_DELAY_S)

        self.__active_request_uid += 1
        return self.__pipe.recv()


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

        self.__response_received_condition = aio.Condition()
        self.__dispatcher.replace(
            reply_key, lambda reply: aio.create_task(self.__reply_callback(reply))
        )

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
        It is assumed that the remote device can handle only one request at a time. Once a request is sent, the coroutine await for `__reply_callback` to be invoked (which occurs when the response has been received).
        """
        while True:
            if self.__pipe.poll():
                self.__serial.write(self.__pipe.recv())
                async with self.__response_received_condition:
                    await self.__response_received_condition.wait()

            await aio.sleep(IO_REFRESH_DELAY_S)

    async def __handle_rx(self):
        """
        Receive the packets from the remote device and send them to the main process
        It forwards the packet to the underlying dispatcher, but does not send back any response.
        """
        while True:
            if self.__serial.in_waiting > 0:
                results = self.__dispatcher.resolve_completely(
                    self.__serial.read(self.__serial.in_waiting)
                )
                if any(map(lambda result: result != b"", results)):
                    warn(
                        f"Action request from remote device would return non-empty responses ({results}) which is not supported. Those results will be discarded."
                    )

            await aio.sleep(IO_REFRESH_DELAY_S)

    async def __reply_callback(self, reply):
        """
        Callback invoked when received the remote device response
        When called, `__handle_tx` is notified of the availability of the remote device.
        """
        self.__pipe.send(bytes(reply))
        async with self.__response_received_condition:
            self.__response_received_condition.notify_all()
