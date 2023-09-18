import asyncio

import pytest

from shell import *
from shell.banner import *
from shell.command import argument, command


class MyShell(Shell):
    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)

    @command()
    @argument("msg", type=str)
    def do_print(self, msg):
        """
        Print a message
        """
        self.log_status(msg)

    @command()
    @argument("msg", type=str)
    @argument("n", type=int)
    async def do_nprint(self, msg, n):
        """
        Print `n` time a message with a 1 second delay in-between
        """
        for i in range(n):
            self.log_status(msg)
            await asyncio.sleep(1)

    @command(capture_keyboard="listener")
    async def do_print_key(self, listener):
        """
        Print the pressed key
        """
        from pynput.keyboard import Key

        while True:
            event_key = await listener.get()

            if event_key[0]:
                if event_key[1] == Key.esc:
                    return
                print(repr(event_key[1]))

    @command()
    async def do_show_banner(self):
        """
        Print a funky banner for 3 seconds
        """
        async with self.banner(BarSpinner("Spinning..."), refresh_delay_s=60e-3):
            await asyncio.sleep(3)


@pytest.mark.asyncio
async def test_shell():
    mock_shell = MyShell()

    mock_shell.do_print("")
    mock_shell.do_nprint("0")
    mock_shell.do_show_banner("")
