import pytest
import test_extension_module as tem
import unpadded as upd

from tracker import *


class MockClient(upd.Client):
    def __init__(self, dispatcher, trigger, stop, response):
        self.__dispatcher = dispatcher
        self.__trigger = trigger
        self.__stop = stop
        self.__response = response
        self.is_running = False

    async def new_request(self, payload):
        if payload == self.__trigger:
            assert not self.is_running
            self.is_running = True
            self.__dispatcher.resolve_completely(self.__response)
        if payload == self.__stop:
            assert self.is_running
            self.is_running = False

    def replace(self, key, f):
        self.__dispatcher.replace(key, f)


@pytest.fixture
def triple_reporter_client():
    return MockClient(
        dispatcher=tem.Dispatcher(),
        trigger=tem.control_tracker.encode(Command.START),
        stop=tem.control_tracker.encode(Command.STOP),
        response=tem.report.encode(2, 2, 2)
        + tem.report.encode(0, 2, 0)
        + tem.report.encode(1, 1, 1),
    )


@pytest.mark.asyncio
async def test_track_until_timeout(triple_reporter_client):
    tracker = Tracker(
        client=triple_reporter_client,
        control_key=tem.control_tracker,
        report_key=tem.report,
    )

    async with tracker:
        assert DataFrame(
            {"timestamp": [0, 1, 2], "left": [2, 1, 2], "right": [0, 1, 2]}
        ).equals(await tracker.timeout(10e-3))
