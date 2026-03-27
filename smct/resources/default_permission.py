#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause

"""Module related to default permission assignment"""

from typing import Any, Tuple

from smct.utils import FormatedInt


class DefaultPermission:
    """Default permission data class"""

    def __init__(self, begin: FormatedInt, size: FormatedInt, dids: Tuple[int, int], permission: str, should_generate_debug_access: bool = True) -> None:
        """Initialize DefaultPermission instance.

        Args:
            begin: Begin address of the assignment
            size: Number of bytes to use the permission in the assignment
            dids: Tuple with DID range to be configured
            permission: Permission of this assignment
            should_generate_debug_access: Whether this assignment should also generate debug access
        """
        self._begin = begin
        self._size = size
        self._dids = dids
        self._permission = permission
        self._should_generate_debug_access = should_generate_debug_access

    def get_begin(self) -> FormatedInt:
        """Returns begin address of the assignment.

        Returns:
            Begin address of the assignment
        """
        return self._begin

    def get_size(self) -> FormatedInt:
        """Returns number of bytes to use the permission in the assignment.

        Returns:
            Number of bytes to use the permission in the assignment
        """
        return self._size

    def get_dids(self) -> Tuple[int, int]:
        """Returns tuple with DID range to be configured.

        Returns:
            Tuple with DID range to be configured
        """
        return self._dids

    def get_permission(self) -> str:
        """Returns permission of this assignment.

        Returns:
            Permission of this assignment
        """
        return self._permission

    def should_generate_debug_access(self) -> bool:
        """Returns True if this assignment should also generate debug access.

        Returns:
            True if this assignment should also generate debug access
        """
        return self._should_generate_debug_access

    def __eq__(self, other: Any) -> bool:
        """Returns True if this assignment is equal to another assignment.

        Args:
            other: Other assignment to compare

        Returns:
            True if this assignment is equal to another assignment
        """
        if not isinstance(other, self.__class__):
            return False
        return (
            self._begin.get_value() == other._begin.get_value()
            and self._size.get_value() == other._size.get_value()
            and self._dids == other._dids
            and self._permission == other._permission
            and self._should_generate_debug_access == other._should_generate_debug_access
        )
