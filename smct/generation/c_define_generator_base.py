#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause

"""Module with generators of C language defines"""

import sys
from io import StringIO
from typing import IO


class CDefineGeneratorBase:
    """Base of C define generators"""

    def __init__(self) -> None:
        self._head_buffer = StringIO()
        self._content_buffer = StringIO()
        self._tail_buffer = StringIO()

    def add_to_head(self, text: str, end: str = "\n") -> None:
        """Adds the given text to the head (name, comment) buffer.

        Args:
            text: The text to add to the head buffer.
            end: The line ending character to use.
        """
        print(text, file=self._head_buffer, end=end)

    def add_to_members(self, text: str, end: str = "\n") -> None:
        """Adds the given text to the content (members) buffer.

        Args:
            text: The text to add to the content buffer.
            end: The line ending character to use.
        """
        print(text, file=self._content_buffer, end=end)

    def add_to_tail(self, text: str, end: str = "\n") -> None:
        """Adds the given text to the tail buffer.

        Args:
            text: The text to add to the tail buffer.
            end: The line ending character to use.
        """
        print(text, file=self._tail_buffer, end=end)

    def get_head_string(self) -> str:
        """Returns the head (name, comment) section content as string.

        Returns:
            The head section content as a string.
        """
        return self._head_buffer.getvalue()

    def get_members_string(self) -> str:
        """Returns the content (members) section content as string.

        Returns:
            The content section content as a string.
        """
        return self._content_buffer.getvalue()

    def get_tail_string(self) -> str:
        """Returns the tail section content as string.

        Returns:
            The tail section content as a string.
        """
        return self._tail_buffer.getvalue()

    def get_string(self) -> str:
        """Returns the entire generator content as string.

        Returns:
            The entire generator content as a string.
        """
        return "".join([self.get_head_string(), self.get_members_string(), self.get_tail_string()])

    def print_head(self) -> None:
        """Print the head (name, comment) of the C define."""

    def print_members(self) -> None:
        """Print the content (members) of the C define."""

    def print_tail(self) -> None:
        """Prints the tail of the C define."""

    def print(self, file: IO | None = None) -> None:
        """Generates entire content of the C define into buffers and prints the contents of all the buffers into given file.

        Args:
            file: File into which the content will be printed without line-ending. If value is None then uses 'sys.stdout'.
        """
        self.print_head()
        self.print_members()
        self.print_tail()
        if file is None:
            file = sys.stdout
        print(self.get_string(), end="", file=file)
