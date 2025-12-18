#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Module related to formatting validation entries into console."""
import logging

from smct.validation.formatters.validation_entry_formatter_base import ValidationEntryFormatterBase
from smct.validation.validation_entry import ValidationEntry

logger = logging.getLogger()


class ConsoleFormatter(ValidationEntryFormatterBase):
    """Formatter implementation that logs the entries into error output."""

    def process_entry(self, entry: ValidationEntry) -> None:
        """Processes the given validation entry to log into the error output.

        Args:
            entry: The validation entry to be processed and logged.
        """
        logger.log(entry.get_level(), entry.get_error_message(), extra={"source": entry.get_source(), "validation_id": entry.get_validation_id()})
