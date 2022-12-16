import asyncio as aio
import multiprocessing as mp
from enum import IntEnum
from typing import List

from unpadded import Client # type: ignore
from pandas import DataFrame

from annotation import KeyLike

WRITE_MEASURE_REFRESH_DELAY_S = 1e-3


class Command(IntEnum):
    """
    Command to be sent through the control callback
    """

    START = 0
    STOP = 1


class Tracker:
    def __init__(self, client: Client, control_key: KeyLike, report_key: KeyLike):
        """
        Initialize the report callback in ``client``
        """

        self.__client = client
        self.__control_key = control_key
        self.__report_key = report_key
        self.__queue: mp.Queue = mp.Queue()
        self.__stop_tracking_event = aio.Event()
        self.__timestamps: List[int] = []
        self.__left_measures: List[int] = []
        self.__right_measures: List[int] = []

        client.replace(report_key, self.__append_to_queue)

    @property
    def timestamps(self) -> List[int]:
        """
        Get the reported timestamps so far
        """
        return self.__timestamps

    @property
    def left_measures(self) -> List[int]:
        """
        Get the reported left measures so far
        """
        return self.__left_measures

    @property
    def right_measures(self) -> List[int]:
        """
        Get the reported right measures so far
        """
        return self.__right_measures

    @property
    def data_frame(self) -> DataFrame:
        """
        Make a ``DataFrame`` out of all measures reported so far
        """

        df = DataFrame(
            {
                "timestamp": self.__timestamps,
                "left": self.__left_measures,
                "right": self.__right_measures,
            }
        )
        return df.sort_values("timestamp").reset_index(drop=True)

    async def __aenter__(self) -> "_TrackerContextManager":
        """
        Tell the remote device to start reporting
        """

        self.__timestamps = []
        self.__left_measures = []
        self.__right_measures = []
        self.__stop_tracking_event.clear()
        self.__write_measure_task = aio.Task(self.__write_measure())
        await self.__client.call(self.__control_key, Command.START)
        return _TrackerContextManager(self)

    async def __aexit__(self, *_):
        """
        Tell the remote device to stop reporting
        """

        await self.__client.call(self.__control_key, Command.STOP)
        self.__stop_tracking_event.set()
        await self.__write_measure_task

    def __append_to_queue(self, timestamp: int, left: int, right: int) -> DataFrame:
        """
        Forward a measure to the main process
        """
        if not self.__stop_tracking_event.is_set():
            self.__queue.put_nowait((timestamp, left, right))

    async def __write_measure(self) -> None:
        """
        Append any measure received from the dispatcher process
        """

        while not self.__stop_tracking_event.is_set():
            while not self.__queue.empty():
                timestamp, left, right = self.__queue.get()
                self.__timestamps.append(timestamp)
                self.__left_measures.append(left)
                self.__right_measures.append(right)
            await aio.sleep(WRITE_MEASURE_REFRESH_DELAY_S)


class _TrackerContextManager:
    def __init__(self, tracker: Tracker):
        self.__tracker = tracker

    async def timeout(self, delay: int) -> DataFrame:
        """
        Wait until no data has been received for at least ``timeout`` seconds and return all data that have been received so far
        """
        measures_nb = None
        while measures_nb != len(self.__tracker.timestamps):
            measures_nb = len(self.__tracker.timestamps)
            await aio.sleep(delay)

        return self.__tracker.data_frame
