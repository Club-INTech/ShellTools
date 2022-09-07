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


@pytest.fixture
def mock_stdin():
    return StringIO()


@pytest.fixture
def mock_stdout():
    return StringIO()


@pytest.fixture
def mock_shell(mock_stdin, mock_stdout):
    return MockShell(istream=mock_stdin, ostream=mock_stdout)


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
