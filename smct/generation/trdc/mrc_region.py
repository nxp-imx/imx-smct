#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause

"""Module related to MRC region generation"""

import typing


class MrcRegion:
    """Region of MRC"""

    def __init__(self, domain: int, start_address: int, end_address: int, permission: int) -> None:
        """Initialize MrcRegion.

        Args:
            domain: Domain of the region
            start_address: Start address of the region
            end_address: End address of the region
            permission: Permission of the region
        """
        self._domain = domain
        self._start_address = start_address
        self._end_address = end_address
        self._permission = permission

    def get_domain(self) -> int:
        """Returns domain of the regions.

        Returns:
            Domain of the region
        """
        return self._domain

    def get_start_address(self) -> int:
        """Returns start address of the regions.

        Returns:
            Start address of the region
        """
        return self._start_address

    def get_end_address(self) -> int:
        """Returns end address of the region.

        Returns:
            End address of the region
        """
        return self._end_address

    def get_permission(self) -> int:
        """Returns permission of the region.

        Returns:
            Permission of the region
        """
        return self._permission

    def is_clearing(self) -> bool:
        """Returns True is the region is used just to clear the register.

        Returns:
            True if the region is used just to clear the register
        """
        return self._permission < 0

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, MrcRegion):
            return False
        other_mrc = typing.cast(MrcRegion, other)
        if self._domain != other_mrc._domain:
            return False
        if self._start_address != other_mrc._start_address:
            return False
        if self._end_address != other_mrc._end_address:
            return False
        if self._permission != other_mrc._permission:
            return False
        return True

    def __str__(self) -> str:
        return f"Mrc region domain:{self._domain} start:{self._start_address} end:{self._end_address} permission:{self._permission}"
