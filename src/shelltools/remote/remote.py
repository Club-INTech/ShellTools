import asyncio as aio
import multiprocessing as mp
import multiprocessing.connection
from typing import Any, Optional
from warnings import warn

import serial as sr
from unpadded import Client, PacketStatus  # type: ignore

from shelltools.annotation import DispatcherLike, KeyLike
from shelltools.utility.match import Match

IO_REFRESH_DELAY_S = 50e-3
RESPONSE_CHECK_DELAY_S = 1e-3
SERIAL_TIMEOUT_S = 500e-3

HEADER = b"\xff\xff\xff\xff"


class Remote(Client):
    """
    Handles a serial communication stream with a remote device
    """

    def __init__(self, port: str, dispatcher: DispatcherLike, reply_key: KeyLike):
        """
        Start listening to a serial port and hold a pipe to a tracker process
        """

        self.__pipe, remote_pipe = mp.Pipe()
        self.__dispatcher = dispatcher
        self.__loop = aio.get_event_loop()
        self.__active_request_uid, self.__next_request_uid = 0, 0
        self.__exception: Optional[Exception] = None
        self.__process = mp.Process(
            target=_RemoteProcess(
                port=port, pipe=remote_pipe, dispatcher=dispatcher, reply_key=reply_key
            ),
            daemon=True,
        )
        self.__process.start()

    def new_request(self, payload: bytes) -> aio.Task:
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

    async def __get_response(self, uid: int) -> Any:
        """
        Wait asynchronously for the pending request with the given UID to be resolved

        The responses are received in the same order as the requests, so the coroutine wait for the other requests with lesser UID to be resolved first.
        If the process send an exception through the pipe, then every current and future pending request raise this exception when awaited.
        """
        while not (
            self.__active_request_uid == uid
            and self.__pipe.poll()
            or self.__exception is not None
        ):
            await aio.sleep(RESPONSE_CHECK_DELAY_S)
        self.__active_request_uid += 1

        if self.__exception is not None:
            raise self.__exception

        result = self.__pipe.recv()
        if isinstance(result, Exception):
            self.__exception = result
            raise self.__exception
        else:
            return result


class _RemoteProcess:
    """
    Manages the communication to the remote device and resolve request from the remote device
    """

    def __init__(
        self,
        port: str,
        pipe: mp.connection.Connection,
        dispatcher: DispatcherLike,
        reply_key: KeyLike,
    ):
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

        self.__dispatcher.replace(
            reply_key, lambda reply: aio.create_task(self.__reply_callback(reply))
        )

    def __call__(self) -> None:
        """
        Start the listening of the remote device
        """
        aio.run(self.__start())

    async def __start(self) -> None:
        """
        Receive request from the remote device and handle command from the control pipe

        This coroutine start two other coroutines (``__handle_tx`` and ``__handle_rx``) which can only finish when an exception is raised by either or both of them. When it happens, those exceptions are sent to main process through the pipe and any coroutine that did not throw is cancelled, then the ``__start`` coroutine finishes.
        """
        self.__response_received_condition = aio.Condition()
        loop = aio.get_event_loop()
        handle_tx, handle_rx = loop.create_task(self.__handle_tx()), loop.create_task(
            self.__handle_rx()
        )
        done, pending = await aio.wait(
            [handle_tx, handle_rx], return_when=aio.FIRST_EXCEPTION
        )
        for coro in done:
            self.__pipe.send(coro.exception())
        for coro in pending:
            coro.cancel()

    async def __handle_tx(self) -> None:
        """
        Transmit the packets received from the main process want to send to the remote device

        It is assumed that the remote device can handle only one request at a time. Once a request is sent, the coroutine await for ``__reply_callback`` to be invoked (which occurs when the response has been received).
        """
        while True:
            if self.__pipe.poll():
                self.__serial.write(HEADER + self.__pipe.recv())
                async with self.__response_received_condition:
                    await self.__response_received_condition.wait()

            await aio.sleep(IO_REFRESH_DELAY_S)

    async def __handle_rx(self) -> None:
        """
        Receive the packets from the remote device and send them to the main process

        It forwards the packet to the underlying dispatcher, but does not send back any response.
        """

        header_sentinel = len(HEADER)

        def raise_corrupted_packet():
            raise RuntimeError(
                "A corrupted packet has been received. Process will stop."
            )

        def check_unloaded_dispatcher():
            nonlocal header_sentinel
            header_sentinel = len(HEADER)
            if self.__dispatcher.is_loaded():
                warn(
                    f"Action request from remote device would return a non-empty response which is not supported. That result will be discarded.",
                    RuntimeWarning,
                )
                self.__dispatcher.write_to(lambda x: None)

        while True:
            while self.__serial.in_waiting > 0:
                x = self.__serial.read(1)
                if header_sentinel == 0:
                    Match(self.__dispatcher.put(int.from_bytes(x, "little"))) & {
                        PacketStatus.DROPPED_PACKET: raise_corrupted_packet,
                        PacketStatus.RESOLVED_PACKET: check_unloaded_dispatcher,
                        PacketStatus.LOADING_PACKET: lambda: None,
                    }
                else:
                    header_sentinel = (
                        header_sentinel - 1 if x == HEADER[:1] else len(HEADER)
                    )

            await aio.sleep(IO_REFRESH_DELAY_S)

    async def __reply_callback(self, reply: bytes) -> None:
        """
        Callback invoked when received the remote device response

        When called, `__handle_tx` is notified of the availability of the remote device.
        """
        self.__pipe.send(bytes(reply))
        async with self.__response_received_condition:
            self.__response_received_condition.notify_all()
