import asyncio as aio
import random as rnd
from io import StringIO

import pytest

from ..display.banner import *
from ..shell import *


class MockShell(Shell):
    def __init__(self, *args, **kwargs):
        self.x = 0
        super().__init__(*args, **kwargs)

    @command
    async def do_increment(self):
        """
        Increment once
        """
        self.x += 1

    @command
    @argument("n", type=int)
    async def do_increment_by(self, n):
        """
        Increment n times
        """
        self.x += n

    @command
    async def do_alert(self):
        """
        Print some alerts
        """
        for i in range(3):
            self.log("alert")

    @command
    async def do_big_alert(self):
        """
        Print many alerts
        """
        for i in range(100):
            self.log("alert")

    @command
    async def do_timmed_alert(self):
        """
        Print asynchronous alerts
        """
        self.log("alert1")
        await aio.sleep(1)
        self.log("alert2")
        await aio.sleep(1)
        self.log("alert3")

    @command
    async def do_panic(self):
        """
        Exit in panic
        """
        raise Exception("I panicked")

    @command
    async def do_error(self):
        """
        Print an error
        """
        raise ShellError("Oops")

    @command
    async def do_banner(self):
        async with self.banner(ProgressBar("Hi !"), refresh_delay_s=60e-3) as bar:
            while bar.progress < 1.2:
                bar.progress += 0.01
                await aio.sleep(50e-3)
            while bar.progress > -0.2:
                bar.progress -= 0.01
                await aio.sleep(50e-3)
        async with self.banner(BarSpinner("Spinning..."), refresh_delay_s=60e-3) as bar:
            await aio.sleep(5)


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
    mock_stdin.write("big_alert\nEOF\n")
    mock_stdin.seek(0)
    await mock_shell.run()

    assert mock_stdout.getvalue() == "alert\n" * 100 + "Exiting the shell...\n"


@pytest.mark.asyncio
async def test_(mock_shell, mock_stdin, mock_stdout):
    mock_stdin.write("increment 5\nEOF\n")
    mock_stdin.seek(0)
    n = rnd.randint(0, 100)
    mock_shell.x = n

    await mock_shell.run()

    assert mock_shell.x == n
