#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Module with resource database provider"""
from smct.resources.resdb import ResourceDb


class ResourceDatabaseProvider:
    """Provider of the resource database singleton"""

    _singleton: ResourceDb = ResourceDb()

    @classmethod
    def get_database(cls) -> ResourceDb:
        """Returns singleton of the resource database object

        Returns:
            ResourceDb: The singleton resource database instance
        """
        return cls._singleton

    @classmethod
    def clear_database(cls) -> None:
        """Clears the resource database singleton by creating new one

        Returns:
            None
        """
        cls._singleton = ResourceDb()
