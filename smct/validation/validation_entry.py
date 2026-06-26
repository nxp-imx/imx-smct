#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause

"""Module related to validation entry."""

from builtins import str
from typing import Any, Dict


class ValidationEntry:
    """Entry from validation process. Further processing is required for user to see the reported problems."""

    def __init__(self, level: int, source: str, error_message: str, validation_id: str | None = None) -> None:
        """Initialize ValidationEntry.

        Args:
            level: The level of this entry
            source: The source of this entry
            error_message: The error message of this entry
            validation_id: The validation ID of this entry, optional
        """
        self._level: int = level
        self._source: str = source
        self._error_message: str = error_message
        self._validation_id: str | None = validation_id

    def get_level(self) -> int:
        """Returns the level of this entry.

        Returns:
            The level of this entry
        """
        return self._level

    def get_source(self) -> str:
        """Returns the source of this entry.

        Returns:
            The source of this entry
        """
        return self._source

    def get_error_message(self) -> str:
        """Returns error message of this entry.

        Returns:
            The error message of this entry
        """
        return self._error_message

    def get_validation_id(self) -> str:
        """Returns validation ID of this entry.

        Returns:
            The validation ID of this entry
        """
        if not self._validation_id:
            return "None"
        return self._validation_id

    def get_json(self) -> Dict[str, Any]:
        """Returns JSON dictionary with values of this entry.

        Returns:
            JSON dictionary with values of this entry
        """
        result: Dict[str, Any] = {}
        result["message"] = self._error_message
        return result
