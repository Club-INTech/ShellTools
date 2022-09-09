import asyncio as aio
import cmd
import os
from argparse import ArgumentParser, Namespace
from collections.abc import Callable, Coroutine
from contextlib import asynccontextmanager
from sys import stdin, stdout
from textwrap import dedent
from typing import NoReturn, Optional, TextIO, TypeVar

import terminology as tmg


class ProgressBar:
    """
    Preview :
    `| Hi ! |██████████████████████████████████████████`
    """

    def __init__(
        self,
        text: str = "",
        modifier: Callable[[str], str] = lambda x: x,
        bg_modifier_when_full: Callable[[str], str] = lambda x: x,
    ):
        """
        Set the text to display before the bar
        A modifier can be specified to change the color of the bar.
        """
        self.__text = text
        self.__modifier = modifier
        self.__bg_modifier_when_full = bg_modifier_when_full
        self.__progress = 0.0

    def __str__(self) -> str:
        """
        Get the string representation of the bar
        """
        prefix = f"| {self.__text} |"

        if self.__progress > 1:
            overflow_text = "OVERFLOW >>"
            return self.__modifier(prefix) + self.__bg_modifier_when_full(
                (os.get_terminal_size().columns - len(prefix + overflow_text)) * " "
                + overflow_text
            )
        if self.__progress < 0:
            return self.__modifier(prefix + " << UNDERFLOW")

        blocks_nb = int(
            8 * (os.get_terminal_size().columns - len(prefix)) * self.__progress
        )
        remainder = blocks_nb % 8
        last_chr = chr(ord("█") + 7 - remainder)
        return self.__modifier(prefix + int(blocks_nb / 8) * "█" + last_chr)

    @property
    def progress(self) -> float:
        """
        Current progress in percentage
        """
        return self.__progress

    @progress.setter
    def progress(self, p: float) -> None:
        self.__progress = p


class BarSpinner:
    """
    Preview :
    `| Spinning... |▅▃▁▇`
    """

    PATTERN = "▁▂▃▄▅▆▇█"

    def __init__(self, text: str = "", modifier: Callable[[str], str] = lambda x: x):
        """
        Set the text to display before the bar
        A modifier can be specified to change the color of the bar.
        """
        self.__text = text
        self.__modifier = modifier
        self.__progress = 0

    def __str__(self) -> str:
        """
        Update the progress and return the new representation
        """
        self.__progress = (self.__progress + 1) % len(self.PATTERN)

        line = f"| {self.__text} |" + (
            self.PATTERN[(self.__progress + 4) % len(self.PATTERN)]
            + self.PATTERN[self.__progress]
            + self.PATTERN[(self.__progress + 6) % len(self.PATTERN)]
            + self.PATTERN[(self.__progress + 2) % len(self.PATTERN)]
        )

        return self.__modifier(
            line + (os.get_terminal_size().columns - len(line)) * " "
        )
