#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause

"""Module related to MBC block generation."""

import typing
from typing import Tuple

from smct.resources.res_mbc import MbcResource


class MbcBlock:
    """Block of MBC."""

    def __init__(self, domain: int, resource: MbcResource, block_range: Tuple[int, int], permission: int, clearing: bool = False) -> None:
        """Initialize MBC block.

        Args:
            domain: Domain of the block
            resource: MBC resource
            block_range: Range of blocks for the resource
            permission: Permission of the block
            clearing: Whether this block is for clearing
        """
        self._domain = domain
        self._resource = resource
        self._block_range = block_range
        self._permission = permission
        self._clearing = clearing

    def get_mbc(self) -> int:
        """Return MBC index of the block.

        Returns:
            MBC index of the block
        """
        return self._resource.get_index()

    def get_domain(self) -> int:
        """Returns domain of the block.

        Returns:
            Domain of the block
        """
        return self._domain

    def get_mem(self) -> int:
        """Return memory index of the block.

        Returns:
            Memory index of the block
        """
        return self._resource.get_mem()

    def get_block_range(self) -> Tuple[int, int]:
        """Returns range of blocks for the resource.

        Returns:
            Range of blocks for the resource
        """
        return self._block_range

    def get_register_name(self, word: int) -> str:
        """Return register name of the block.

        Args:
            word: Word parameter for register name

        Returns:
            Register name of the block
        """
        return self._resource.get_register_name(self._domain, word)

    def get_permission(self) -> int:
        """Returns permission of the block.

        Returns:
            Permission of the block
        """
        return self._permission

    def merge_permission(self, permission: int) -> None:
        """Merges (ORs) additional permission bits into this block.

        Args:
            permission: Permission bits to OR with existing permission
        """
        self._permission |= permission

    def get_name(self) -> str:
        """Return name of the block.

        Returns:
            Name of the block
        """
        return self._resource.get_name()

    def is_dom_clearing(self) -> bool:
        """Returns clearing flag of the block.

        Returns:
            Clearing flag of the block
        """
        return self._clearing

    def overwrites(self, other: object) -> bool:
        """Check if other block is overwritten by this block.

        Args:
            other: Object to check

        Returns:
            True if this block overwrites the other block
        """
        if not isinstance(other, MbcBlock):
            return False
        other_mbc = typing.cast(MbcBlock, other)
        if self.get_domain() != other_mbc.get_domain():
            return False
        if self.get_name() != other_mbc.get_name():
            return False
        if self.get_block_range() != other_mbc.get_block_range():
            return False
        return True

    def __eq__(self, other: object) -> bool:
        """Check equality with another object.

        Args:
            other: Object to compare with

        Returns:
            True if objects are equal, False otherwise
        """
        if not isinstance(other, MbcBlock):
            return False
        other_mbc = typing.cast(MbcBlock, other)
        if self._domain != other_mbc._domain:
            return False
        if self._resource != other_mbc._resource:
            return False
        if self._block_range != other_mbc._block_range:
            return False
        if self._permission != other_mbc._permission:
            return False
        return True

    def __str__(self) -> str:
        """Return string representation of the MBC block.

        Returns:
            String representation of the MBC block
        """
        return f"Mbc block mbc:{self._resource.get_index()} domain:{self._domain} mem:{self._resource.get_mem()} range:{self._block_range}"
