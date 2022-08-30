import random as rnd
from multiprocessing import Value

import pytest
import test_extension_module as tem
import unpadded as upd
from mock_serial.pytest import *

from remote import *

pytest_plugins = ("pytest_asyncio",)


@pytest.mark.asyncio
async def test_request_an_action_through_remote(mock_serial):
    remote = Remote(
        port=mock_serial.port, dispatcher=tem.Dispatcher(), reply_key=tem.reply
    )

    u8 = rnd.getrandbits(6)
    u16 = rnd.getrandbits(14)
    u32 = rnd.getrandbits(30)
    i8 = -u8
    i16 = -u16
    i32 = -u32
    i64 = -rnd.getrandbits(62)
    max_int, min_int = 2**63 - 1, -(2**63)

    mock_serial.stub(
        receive_bytes=b"\x00" + u8.to_bytes(1, "little"),
        send_bytes=b"\x00" + (2 * u8).to_bytes(32, "little"),
    )
    mock_serial.stub(
        receive_bytes=b"\x01" + u16.to_bytes(2, "little"),
        send_bytes=b"\x00" + (2 * u16).to_bytes(32, "little"),
    )
    mock_serial.stub(
        receive_bytes=b"\x02" + u32.to_bytes(4, "little"),
        send_bytes=b"\x00" + (2 * u32).to_bytes(32, "little"),
    )
    mock_serial.stub(
        receive_bytes=b"\x03" + i8.to_bytes(1, "little", signed=True),
        send_bytes=b"\x00" + (2 * i8).to_bytes(32, "little", signed=True),
    )
    mock_serial.stub(
        receive_bytes=b"\x04" + i16.to_bytes(2, "little", signed=True),
        send_bytes=b"\x00" + (2 * i16).to_bytes(32, "little", signed=True),
    )
    mock_serial.stub(
        receive_bytes=b"\x05" + i32.to_bytes(4, "little", signed=True),
        send_bytes=b"\x00" + (2 * i32).to_bytes(32, "little", signed=True),
    )
    mock_serial.stub(
        receive_bytes=b"\x06" + i64.to_bytes(8, "little", signed=True),
        send_bytes=b"\x00" + (2 * i64).to_bytes(32, "little", signed=True),
    )
    mock_serial.stub(
        receive_bytes=b"\x07" + max_int.to_bytes(8, "little", signed=True),
        send_bytes=b"\x00" + max_int.to_bytes(32, "little", signed=True),
    )
    mock_serial.stub(
        receive_bytes=b"\x07" + min_int.to_bytes(8, "little", signed=True),
        send_bytes=b"\x00" + min_int.to_bytes(32, "little", signed=True),
    )

    assert await remote.call(tem.double_u8, u8) == 2 * u8
    assert await remote.call(tem.double_u16, u16) == 2 * u16
    assert await remote.call(tem.double_u32, u32) == 2 * u32
    assert await remote.call(tem.double_i8, i8) == 2 * i8
    assert await remote.call(tem.double_i16, i16) == 2 * i16
    assert await remote.call(tem.double_i32, i32) == 2 * i32
    assert await remote.call(tem.double_i64, i64) == 2 * i64
    assert await remote.call(tem.identity_i64, max_int) == max_int
    assert await remote.call(tem.identity_i64, min_int) == min_int

    awaitables = [
        remote.call(tem.double_u8, u8),
        remote.call(tem.double_u16, u16),
        remote.call(tem.double_u32, u32),
    ]
    awaitables.reverse()
    for (awaitable, value) in zip(awaitables, [u32, u16, u8]):
        assert await awaitable == 2 * value


@pytest.mark.asyncio
async def test_handle_request_to_and_from_device_simulatneously(mock_serial):
    arg_to, arg_from = rnd.getrandbits(31), rnd.getrandbits(31)
    witness = Value("i", ~arg_from)

    def set_witness(x):
        nonlocal witness
        witness.value = x

    mock_serial.stub(
        receive_bytes=b"\x02" + arg_to.to_bytes(4, "little"),
        send_bytes=b"\x01"
        + arg_from.to_bytes(4, "little")
        + b"\x00"
        + (2 * arg_to).to_bytes(32, "little"),
    )

    dispatcher = tem.Dispatcher()
    dispatcher.replace(tem.do_something, set_witness)
    remote = Remote(port=mock_serial.port, dispatcher=dispatcher, reply_key=tem.reply)

    assert await remote.call(tem.double_u32, arg_to) == 2 * arg_to
    assert witness.value == arg_from


@pytest.mark.asyncio
async def test_progagate_exception_back_to_main_thread(mock_serial):
    remote = Remote(
        port=mock_serial.port, dispatcher=tem.Dispatcher(), reply_key=tem.reply
    )

    mock_serial.stub(
        receive_bytes=b"\x00\x00",
        send_bytes=b"\xff",
    )

    request = remote.call(tem.double_u16, 0x00)

    with pytest.raises(ValueError):
        await remote.call(tem.double_u8, 0x00)

    with pytest.raises(ValueError):
        await request

    with pytest.raises(ValueError):
        await remote.call(tem.double_u16, 0x00)
