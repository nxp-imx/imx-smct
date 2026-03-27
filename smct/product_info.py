#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Module with product info related stuff"""

from typing import Tuple

from smct._version import __version__


class ProductInfo:
    """Class containing information about the product"""

    _smct_version = __version__
    _sm_fw_compatibility_version = 2

    @classmethod
    def get_smct_version(cls) -> Tuple[int, int, int]:
        """Returns the SMCT version.

        Returns:
            Tuple[int, int, int]: The SMCT version as a tuple of three integers.
        """
        version = cls._smct_version.split(".")
        return (int(version[0]), int(version[1]), int(version[2]))

    @classmethod
    def get_smct_version_string(cls) -> str:
        """Returns the SMCT version in string format.

        Returns:
            str: The SMCT version formatted as a string.
        """
        return cls._smct_version

    @classmethod
    def get_sm_fw_compatible_version(cls) -> int:
        """Returns the SM FW compatible version.

        Returns:
            int: The SM FW compatible version.
        """
        return cls._sm_fw_compatibility_version
