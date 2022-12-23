from asyncio import run

from tests.mock_shell import MockShell

run(MockShell().run())
