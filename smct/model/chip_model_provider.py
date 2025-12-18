#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Module with chip model provider"""
from smct.model.model_chip import ChipModelImx9


class ChipModelProvider:
    """Provider of the chip model singleton"""

    _singleton: ChipModelImx9 = ChipModelImx9()

    @classmethod
    def get_model(cls) -> ChipModelImx9:
        """Returns singleton of the resource database object.

        Returns:
            ChipModelImx9: The singleton instance of the chip model.
        """
        return cls._singleton

    @classmethod
    def clear_model(cls) -> None:
        """Clears the resource database singleton by creating new one.

        Returns:
            None
        """
        cls._singleton = ChipModelImx9()
