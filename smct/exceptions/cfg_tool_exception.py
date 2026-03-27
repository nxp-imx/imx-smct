#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Module with Configuration tool exceptions"""


class CfgToolException(Exception):
    """Config tool base exception"""

    def __init__(self, message: str) -> None:
        """Initialize CfgToolException.

        Args:
            message: The exception message. If empty, defaults to "Unknown Exception".
        """
        if not message:
            message = "Unknown Exception"
        message = "SM CfgTool: " + message
        super().__init__(message)
