import asyncio as aio
import random as rnd
from io import StringIO

import pytest

from ..shell import *


class MockShell(Shell):
    def __init__(self, *args, **kwargs):
        self.x = 0
        super().__init__(*args, **kwargs)

    @command
    async def do_increment(self, _: str):
        self.x += 1

    @command
    @argument("n", type=int)
    async def do_increment_by(self, n):
        self.x += n

    @command
    async def do_alert(self, _):
        self.log("alert")
        self.log("alert")
        self.log("alert")

    @command
    async def do_timmed_alert(self, _):
        self.log("alert1")
        await aio.sleep(1)
        self.log("alert2")
        await aio.sleep(1)
        self.log("alert3")


@pytest.fixture
def mock_stdin():
    return StringIO()


@pytest.fixture
def mock_stdout():
    return StringIO()


@pytest.fixture
def mock_shell(mock_stdin, mock_stdout):
    return MockShell(prompt="PROMPT-", istream=mock_stdin, ostream=mock_stdout)


@pytest.mark.asyncio
async def test_run_simple_command(mock_shell, mock_stdin, mock_stdout):
    mock_stdin.write("increment\nEOF\n")
    mock_stdin.seek(0)
    n = rnd.randint(0, 100)
    mock_shell.x = n
    await mock_shell.run()

    assert mock_shell.x == n + 1


@pytest.mark.asyncio
async def test_run_command_with_argument(mock_shell, mock_stdin, mock_stdout):
    mock_stdin.write("increment_by 5\nEOF\n")
    mock_stdin.seek(0)
    n = rnd.randint(0, 100)
    mock_shell.x = n
    await mock_shell.run()

    assert mock_shell.x == n + 5


@pytest.mark.asyncio
async def test_print_to_stdout(mock_shell, mock_stdin, mock_stdout):
    mock_stdin.write("alert\nEOF\n")
    mock_stdin.seek(0)
    await mock_shell.run()

    assert mock_stdout.getvalue() == "alert\nalert\nalert\n"