#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Module related to domains"""
from typing import Any, Dict

from .owner_base import ResourceOwner


class DOM(ResourceOwner):
    """Represents a DOMAIN to which we can assign resources (only TRDC resources)"""

    def __init__(self, domain_id: str, did: int, name: str | None = None) -> None:
        """Initialize a DOM instance.

        Args:
            domain_id: The domain identifier string.
            did: The domain identifier integer.
        """
        super().__init__(domain_id)
        dom_name = f"DOM{did}" if not name else name
        self.set_name(dom_name)
        self._did: int = did  # domain identifier
        self._debug: bool = False  # true if all permissions granted

    def get_did(self) -> int:
        """Returns domain ID.

        Returns:
            The domain identifier integer.
        """
        return self._did

    def set_debug(self, debug: bool = True) -> None:
        """Sets the debug flag. If used without parameters, then the flag is set to True.

        Args:
            debug: The debug flag value. Defaults to True.
        """
        self._debug = debug

    def is_debug(self) -> bool:
        """Returns True if the domain is used for debugging.

        Returns:
            True if the domain is in debug mode, False otherwise.
        """
        return self._debug

    def get_assignment_json(self) -> Dict[str, Any]:
        """Returns JSON object with all data.

        Returns:
            A dictionary containing all domain data for JSON serialization.
        """
        ret = super().get_assignment_json()
        ret |= {
            "type": "DOM",
            "did": self._did,
            "debug": self._debug,
        }
        return ret

    def __str__(self) -> str:
        """Returns string representation.

        Returns:
            The string representation of the domain.
        """
        return self.get_id()

    def __repr__(self) -> str:
        """Returns representation of this object.

        Returns:
            The object representation string.
        """
        return f"{self.__class__.__name__}('{self.get_id()}', {self.get_did()})"
