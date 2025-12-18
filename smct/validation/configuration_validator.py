#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Module related to user configuration validation"""
from typing import List

from smct.configuration.confdata import ConfigurationData
from smct.validation.formatters.validation_entry_formatter_base import ValidationEntryFormatterBase
from smct.validation.validation_entry import ValidationEntry
from smct.validation.validator_base import ValidatorBase
from smct.validation.validators.logical_machines_validator import LogicalMachinesValidator
from smct.validation.validators.mailboxes_validator import MailboxesValidator
from smct.validation.validators.scmi_validator import ScmiValidator
from smct.validation.validators.version_validator import VersionValidator


class ConfigurationValidator:
    """Validator of configuration"""

    def __init__(self, conf: ConfigurationData) -> None:
        """Initialize the configuration validator.

        Args:
            conf: The configuration data to validate.
        """
        self._conf: ConfigurationData = conf
        self._validators: List[ValidatorBase] = [LogicalMachinesValidator(), ScmiValidator(), VersionValidator(), MailboxesValidator()]
        self._validation_entries: List[ValidationEntry] = []

    def validate(self) -> None:
        """Validates the configuration and stores the entries reported by each validator.

        Returns:
            None
        """
        for validator in self._validators:
            for entry in validator.validate(self._conf):
                self._validation_entries.append(entry)

    def process_entries(self, formatter: ValidationEntryFormatterBase) -> None:
        """Processes all reported problem entries by given formatter.

        Args:
            formatter: The formatter to use for processing validation entries.

        Returns:
            None
        """
        for entry in self._validation_entries:
            formatter.process_entry(entry)
