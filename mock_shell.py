from asyncio import run

from .tests.test_shell import MockShell

run(MockShell().run())
