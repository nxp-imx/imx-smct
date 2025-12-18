#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Module with product info related stuff"""
from typing import Tuple


class ProductInfo:
    """Class containing information about the product"""

    _smct_version = (1, 0, 0)
    _sm_fw_compatibility_version = 2

    @classmethod
    def get_smct_version(cls) -> Tuple[int, int, int]:
        """Returns the SMCT version.

        Returns:
            Tuple[int, int, int]: The SMCT version as a tuple of three integers.
        """
        return cls._smct_version

    @classmethod
    def get_smct_version_string(cls) -> str:
        """Returns the SMCT version in string format.

        Returns:
            str: The SMCT version formatted as a string.
        """
        version = cls._smct_version
        return f"{version[0]}.{version[1]}.{version[2]}"

    @classmethod
    def get_sm_fw_compatible_version(cls) -> int:
        """Returns the SM FW compatible version.

        Returns:
            int: The SM FW compatible version.
        """
        return cls._sm_fw_compatibility_version
