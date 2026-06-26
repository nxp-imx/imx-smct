#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause

"""Module with base configuration validator."""

from typing import List

from smct.configuration.confdata import ConfigurationData
from smct.validation.validation_entry import ValidationEntry


class ValidatorBase:
    """Validator base class that must be extended by all validators."""

    def validate(self, _: ConfigurationData) -> List[ValidationEntry]:
        """Validates configuration and returns list of found problems.

        Args:
            _: Configuration data to validate

        Returns:
            List of validation entries representing found problems
        """
        return []
