"""
Encoder state tracking
"""

import asyncio as aio
import multiprocessing as mp
from enum import IntEnum
from typing import List

import unpadded as upd
from pandas import DataFrame

from .annotation import KeyLike

WRITE_MEASURE_REFRESH_DELAY_S = 1e-3


class Command(IntEnum):
    """
    Command to be sent through the control callback
    """

    START = 0
    STOP = 1


class Tracker:
    def __init__(self, client: upd.Client, control_key: KeyLike, report_key: KeyLike):
        """
        Initialize the report callback in `client`
        """

        self.__client = client
        self.__control_key = control_key
        self.__report_key = report_key
        self.__queue: mp.Queue = mp.Queue()

        client.replace(report_key, self.__append_to_queue)

    async def __aenter__(self) -> None:
        """
        Tell the remote device to start reporting and start the tasks
        """

        self.__timestamps: List[int] = []
        self.__left_measures: List[int] = []
        self.__right_measures: List[int] = []
        self.__tasks = [aio.Task(self.__write_measure())]
        await self.__client.call(self.__control_key, Command.START)

    async def __aexit__(self, *_):
        """
        Tell the remote device to stop reporting, cancel all tasks and erase all measures
        """

        await self.__client.call(self.__control_key, Command.STOP)
        for task in self.__tasks:
            task.cancel()
        self.__timestamps = None
        self.__left_measures = None
        self.__right_measures = None

    async def timeout(self, delay: int) -> DataFrame:
        """
        Wait until no data has been received for at least `timeout` seconds and return all data that have been received so far
        """
        measures_nb = None
        while measures_nb != len(self.__timestamps):
            measures_nb = len(self.__timestamps)
            await aio.sleep(delay)

        return self.__make_data_frame()

    def __append_to_queue(self, timestamp: int, left: int, right: int) -> DataFrame:
        """
        Forward a measure to the main process
        """

        self.__queue.put_nowait((timestamp, left, right))

    def __make_data_frame(self) -> DataFrame:
        """
        Make a `DataFrame` out of all measures reported so far
        """

        df = DataFrame(
            {
                "timestamp": self.__timestamps,
                "left": self.__left_measures,
                "right": self.__right_measures,
            }
        )
        return df.sort_values("timestamp").reset_index(drop=True)

    async def __write_measure(self) -> None:
        """
        Append any measure received from the dispatcher process
        """

        while True:
            while not self.__queue.empty():
                timestamp, left, right = self.__queue.get()
                self.__timestamps.append(timestamp)
                self.__left_measures.append(left)
                self.__right_measures.append(right)
            await aio.sleep(WRITE_MEASURE_REFRESH_DELAY_S)
