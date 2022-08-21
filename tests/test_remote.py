import random as rnd

import pytest
import test_extension_module as tem
import unpadded as upd
from mock_serial.pytest import *

from remote import *

pytest_plugins = ("pytest_asyncio",)


@pytest.mark.asyncio
async def test_request_an_action_through_remote(mock_serial):
    remote = Remote(port=mock_serial.port)

    n = rnd.getrandbits(31)
    stub = mock_serial.stub(
        receive_bytes=b"\x00" + n.to_bytes(4, "little"),
        send_bytes=(2 * n).to_bytes(4, "little"),
    )

    assert await remote.call(tem.double_u32, n) == 2 * n
