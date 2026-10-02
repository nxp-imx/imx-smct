#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause

"""Unit tests for ConfigurationValidator class."""

# pylint: disable=protected-access

import logging
from typing import List
from unittest.mock import MagicMock, Mock

import pytest

from smct.configuration.confdata import ConfigurationData
from smct.configuration.configuration_provider import ConfigurationProvider
from smct.model.chip_model_provider import ChipModelProvider
from smct.resources.resource_database_provider import ResourceDatabaseProvider
from smct.validation.configuration_validator import ConfigurationValidator
from smct.validation.formatters.validation_entry_formatter_base import ValidationEntryFormatterBase
from smct.validation.validation_entry import ValidationEntry
from smct.validation.validator_base import ValidatorBase
from smct.validation.validators.logical_machines_validator import LogicalMachinesValidator
from smct.validation.validators.mailboxes_validator import MailboxesValidator
from smct.validation.validators.resources_validator import ResourcesValidator
from smct.validation.validators.scmi_validator import ScmiValidator
from smct.validation.validators.version_validator import VersionValidator


@pytest.fixture(autouse=True)
def clear_providers() -> None:
    """Reset singleton providers around each test."""
    ConfigurationProvider.clear_configuration()
    ResourceDatabaseProvider.clear_database()
    ChipModelProvider.clear_model()


def _make_fake_validator(entries: List[ValidationEntry]) -> ValidatorBase:
    """Return a mock validator that returns the given entries when validate is called."""
    fake: ValidatorBase = MagicMock(spec=ValidatorBase)
    fake.validate.return_value = entries  # type: ignore[attr-defined]
    return fake


class TestConfigurationValidator:
    """Tests for ConfigurationValidator."""

    def test_init_wires_five_validators(self) -> None:
        """__init__ populates _validators with exactly 5 validator instances."""
        mock_conf = Mock(spec=ConfigurationData)
        cv = ConfigurationValidator(mock_conf)
        assert len(cv._validators) == 5

    def test_init_validators_correct_types(self) -> None:
        """__init__ wires exactly the expected validator types (one of each)."""
        mock_conf = Mock(spec=ConfigurationData)
        cv = ConfigurationValidator(mock_conf)
        types = [type(v) for v in cv._validators]
        assert LogicalMachinesValidator in types
        assert ScmiValidator in types
        assert VersionValidator in types
        assert MailboxesValidator in types
        assert ResourcesValidator in types

    def test_init_validation_entries_empty(self) -> None:
        """_validation_entries starts as an empty list before validate() is called."""
        mock_conf = Mock(spec=ConfigurationData)
        cv = ConfigurationValidator(mock_conf)
        assert not cv._validation_entries

    def test_validate_aggregates_entries_from_all_validators(self) -> None:
        """validate() collects all entries returned by each validator."""
        mock_conf = Mock(spec=ConfigurationData)
        cv = ConfigurationValidator(mock_conf)

        entry1 = ValidationEntry(logging.ERROR, "src1", "err1")
        entry2 = ValidationEntry(logging.WARNING, "src2", "warn1")
        entry3 = ValidationEntry(logging.ERROR, "src3", "err2")

        cv._validators = [
            _make_fake_validator([entry1, entry2]),
            _make_fake_validator([entry3]),
        ]
        cv.validate()

        assert len(cv._validation_entries) == 3
        assert entry1 in cv._validation_entries
        assert entry2 in cv._validation_entries
        assert entry3 in cv._validation_entries

    def test_validate_with_empty_validators_list(self) -> None:
        """validate() with no validators leaves _validation_entries empty."""
        mock_conf = Mock(spec=ConfigurationData)
        cv = ConfigurationValidator(mock_conf)
        cv._validators = []
        cv.validate()
        assert not cv._validation_entries

    def test_validate_with_validators_returning_no_entries(self) -> None:
        """validate() where all validators return [] leaves _validation_entries empty."""
        mock_conf = Mock(spec=ConfigurationData)
        cv = ConfigurationValidator(mock_conf)
        cv._validators = [
            _make_fake_validator([]),
            _make_fake_validator([]),
        ]
        cv.validate()
        assert not cv._validation_entries

    def test_validate_preserves_order(self) -> None:
        """validate() appends entries in the order validators are iterated."""
        mock_conf = Mock(spec=ConfigurationData)
        cv = ConfigurationValidator(mock_conf)

        entry_a = ValidationEntry(logging.INFO, "a", "first")
        entry_b = ValidationEntry(logging.INFO, "b", "second")

        cv._validators = [
            _make_fake_validator([entry_a]),
            _make_fake_validator([entry_b]),
        ]
        cv.validate()

        assert cv._validation_entries[0] is entry_a
        assert cv._validation_entries[1] is entry_b

    def test_validate_passes_conf_to_each_validator(self) -> None:
        """validate() calls validator.validate(conf) with the stored configuration."""
        mock_conf = Mock(spec=ConfigurationData)
        cv = ConfigurationValidator(mock_conf)

        fake1 = _make_fake_validator([])
        fake2 = _make_fake_validator([])
        cv._validators = [fake1, fake2]
        cv.validate()

        fake1.validate.assert_called_once_with(mock_conf)  # type: ignore[attr-defined]
        fake2.validate.assert_called_once_with(mock_conf)  # type: ignore[attr-defined]

    def test_process_entries_calls_formatter_for_each_entry(self) -> None:
        """process_entries calls formatter.process_entry once per aggregated entry."""
        mock_conf = Mock(spec=ConfigurationData)
        cv = ConfigurationValidator(mock_conf)

        entry1 = ValidationEntry(logging.ERROR, "src1", "err1")
        entry2 = ValidationEntry(logging.WARNING, "src2", "warn1")
        cv._validators = [_make_fake_validator([entry1, entry2])]
        cv.validate()

        mock_formatter = Mock(spec=ValidationEntryFormatterBase)
        cv.process_entries(mock_formatter)

        assert mock_formatter.process_entry.call_count == 2
        calls = [call[0][0] for call in mock_formatter.process_entry.call_args_list]
        assert entry1 in calls
        assert entry2 in calls

    def test_process_entries_calls_formatter_in_order(self) -> None:
        """process_entries calls formatter.process_entry in entry-list order."""
        mock_conf = Mock(spec=ConfigurationData)
        cv = ConfigurationValidator(mock_conf)

        entry1 = ValidationEntry(logging.ERROR, "src1", "first")
        entry2 = ValidationEntry(logging.ERROR, "src2", "second")
        cv._validators = [_make_fake_validator([entry1, entry2])]
        cv.validate()

        mock_formatter = Mock(spec=ValidationEntryFormatterBase)
        cv.process_entries(mock_formatter)

        ordered_calls = [call[0][0] for call in mock_formatter.process_entry.call_args_list]
        assert ordered_calls[0] is entry1
        assert ordered_calls[1] is entry2

    def test_process_entries_with_no_entries_does_not_call_formatter(self) -> None:
        """process_entries with no entries does not call formatter.process_entry."""
        mock_conf = Mock(spec=ConfigurationData)
        cv = ConfigurationValidator(mock_conf)
        cv._validators = [_make_fake_validator([])]
        cv.validate()

        mock_formatter = Mock(spec=ValidationEntryFormatterBase)
        cv.process_entries(mock_formatter)

        mock_formatter.process_entry.assert_not_called()
