#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause

"""Unit tests for ValidatorBase class."""

import logging
from typing import List
from unittest.mock import Mock

import pytest

from smct.configuration.confdata import ConfigurationData
from smct.configuration.configuration_provider import ConfigurationProvider
from smct.model.chip_model_provider import ChipModelProvider
from smct.resources.resource_database_provider import ResourceDatabaseProvider
from smct.validation.validation_entry import ValidationEntry
from smct.validation.validator_base import ValidatorBase


@pytest.fixture(autouse=True)
def clear_providers() -> None:
    """Reset singleton providers around each test."""
    ConfigurationProvider.clear_configuration()
    ResourceDatabaseProvider.clear_database()
    ChipModelProvider.clear_model()


class _OverridingValidator(ValidatorBase):
    """Minimal ValidatorBase subclass that returns a fixed entry."""

    def __init__(self, entries: List[ValidationEntry]) -> None:
        """Initialise with pre-built entries list."""
        self._entries = entries

    def validate(self, _: ConfigurationData) -> List[ValidationEntry]:
        """Return the fixed entries list."""
        return self._entries


class TestValidatorBase:
    """Tests for ValidatorBase."""

    def test_validate_base_returns_empty_list(self) -> None:
        """Calling validate on the bare base class returns an empty list."""
        validator = ValidatorBase()
        mock_conf = Mock(spec=ConfigurationData)
        result = validator.validate(mock_conf)
        assert not result

    def test_validate_base_result_is_list(self) -> None:
        """validate returns a list instance, not some other iterable."""
        validator = ValidatorBase()
        mock_conf = Mock(spec=ConfigurationData)
        result = validator.validate(mock_conf)
        assert isinstance(result, list)

    def test_subclass_override_is_honoured(self) -> None:
        """A subclass overriding validate returns its own entries, not []."""
        expected_entry = ValidationEntry(logging.ERROR, "src", "overridden")
        validator = _OverridingValidator([expected_entry])
        mock_conf = Mock(spec=ConfigurationData)
        result = validator.validate(mock_conf)
        assert result == [expected_entry]

    def test_subclass_override_with_empty_list(self) -> None:
        """A subclass that explicitly returns [] also works correctly."""
        validator = _OverridingValidator([])
        mock_conf = Mock(spec=ConfigurationData)
        result = validator.validate(mock_conf)
        assert not result

    def test_subclass_override_with_multiple_entries(self) -> None:
        """A subclass can return multiple ValidationEntry objects."""
        entries = [
            ValidationEntry(logging.WARNING, "src1", "w1"),
            ValidationEntry(logging.ERROR, "src2", "e1"),
        ]
        validator = _OverridingValidator(entries)
        mock_conf = Mock(spec=ConfigurationData)
        result = validator.validate(mock_conf)
        assert len(result) == 2
        assert result[0].get_error_message() == "w1"
        assert result[1].get_error_message() == "e1"
