import asyncio as aio
import random as rnd
from io import StringIO
from math import sin

import pytest
import terminology as tmg

from shell import *
from shell.banner import *
from shell.command import argument, command
from utility.match import Match

from .mock_shell import MockShell


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


@pytest.mark.asyncio
async def test_cancel_tasks_on_exit(mock_shell, mock_stdin):
    mock_stdin.write("freeze\nEOF\n")
    mock_stdin.seek(0)

    await mock_shell.run()

    assert mock_shell.cancelled == True
