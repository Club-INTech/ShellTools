import asyncio as aio
from math import sin

import terminology as tmg

from shell import *
from shell.banner import *
from shell.command import argument, command
from utility.match import Match


class MockShell(Shell):
    def __init__(self, *args, **kwargs):
        self.x = 0
        self.cancelled = False
        super().__init__(*args, **kwargs)

    @command()
    def do_increment(self):
        """
        Increment once
        """
        self.x += 1

    @command()
    @argument("n", type=int)
    def do_increment_by(self, n):
        """
        Increment n times
        """
        self.x += n

    @command()
    def do_alert(self):
        """
        Print some alerts
        """
        for i in range(3):
            self.log("alert")

    @command()
    def do_big_alert(self):
        """
        Print many alerts
        """
        for i in range(100):
            self.log("alert")

    @command()
    async def do_timmed_alert(self):
        """
        Print asynchronous alerts
        """
        self.log("alert1")
        await aio.sleep(1)
        self.log("alert2")
        await aio.sleep(1)
        self.log("alert3")

    @command()
    def do_panic(self):
        """
        Exit in panic
        """
        raise Exception("I panicked")

    @command()
    def do_error(self):
        """
        Print an error
        """
        raise ShellError("Oops")

    @command()
    async def do_freeze(self):
        while True:
            try:
                await aio.sleep(0)
            except aio.CancelledError:
                self.cancelled = True
                return

    @command()
    async def do_banner(self):
        async with self.banner(
            ProgressBar(
                "Hi !",
                modifier=tmg.in_red,
                bg_modifier_when_full=lambda x: tmg.on_red(tmg.in_black(x)),
            ),
            refresh_delay_s=60e-3,
        ) as bar:
            while bar.progress < 1.2:
                bar.progress += 0.01
                await aio.sleep(10e-3)
            while bar.progress > -0.2:
                bar.progress -= 0.01
                await aio.sleep(10e-3)
        async with self.banner(
            BarSpinner("Spinning...", modifier=lambda x: tmg.in_black(tmg.on_cyan(x))),
            refresh_delay_s=60e-3,
        ) as bar:
            await aio.sleep(3)
        async with self.banner(
            TwoWayBar("Hello..."), refresh_delay_s=60e-3
        ) as bar, self.banner(BarSpinner("...there !"), refresh_delay_s=60e-3):
            for i in range(100):
                bar.progress = 1.2 * sin(i / 10)
                await aio.sleep(5 / 100)

    @command(capture_keyboard="listener")
    async def do_move_bar(self, listener):
        from pynput.keyboard import Key

        keep_going = True

        async with self.banner(
            TwoWayBar("Move me !"), refresh_delay_s=10e-3
        ) as bar, self.banner(
            BarSpinner("Press LEFT or RIGHT to move the bar (ESC to quit)"),
            refresh_delay_s=60e-3,
        ):

            def move_left():
                nonlocal bar
                bar.progress -= 0.01

            def move_right():
                nonlocal bar
                bar.progress += 0.01

            def stop():
                nonlocal keep_going
                keep_going = False

            while keep_going:
                Match(await listener.get()) & {
                    (True, Key.left): move_left,
                    (True, Key.right): move_right,
                    (False, Key.esc): stop,
                    tuple: lambda _: None,
                }
                await aio.sleep(10e-3)
