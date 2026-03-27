#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause

"""Module with base validation entry formatter"""

from smct.validation.validation_entry import ValidationEntry


class ValidationEntryFormatterBase:
    """Base validation entry formatter"""

    def process_entry(self, entry: ValidationEntry) -> None:
        """Processes given entry for the specific reporting

        Args:
            entry: The validation entry to process
        """
