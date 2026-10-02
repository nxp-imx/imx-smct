#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause

"""Unit tests for ValidationEntry class."""

import logging

import pytest

from smct.configuration.configuration_provider import ConfigurationProvider
from smct.model.chip_model_provider import ChipModelProvider
from smct.resources.resource_database_provider import ResourceDatabaseProvider
from smct.validation.validation_entry import ValidationEntry


@pytest.fixture(autouse=True)
def clear_providers() -> None:
    """Reset singleton providers around each test."""
    ConfigurationProvider.clear_configuration()
    ResourceDatabaseProvider.clear_database()
    ChipModelProvider.clear_model()


class TestValidationEntry:
    """Tests for ValidationEntry."""

    def test_get_level_returns_ctor_value(self) -> None:
        """get_level returns the level passed to the constructor."""
        entry = ValidationEntry(logging.ERROR, "src", "msg", "VID-1")
        assert entry.get_level() == logging.ERROR

    def test_get_source_returns_ctor_value(self) -> None:
        """get_source returns the source passed to the constructor."""
        entry = ValidationEntry(logging.WARNING, "my_source", "msg")
        assert entry.get_source() == "my_source"

    def test_get_error_message_returns_ctor_value(self) -> None:
        """get_error_message returns the error_message passed to the constructor."""
        entry = ValidationEntry(logging.INFO, "src", "the error message")
        assert entry.get_error_message() == "the error message"

    def test_get_validation_id_returns_id_when_set(self) -> None:
        """get_validation_id returns the id string when provided."""
        entry = ValidationEntry(logging.ERROR, "src", "msg", "VID-42")
        assert entry.get_validation_id() == "VID-42"

    def test_get_validation_id_returns_string_none_when_omitted(self) -> None:
        """get_validation_id returns the string 'None' when validation_id is omitted."""
        entry = ValidationEntry(logging.ERROR, "src", "msg")
        assert entry.get_validation_id() == "None"

    def test_get_validation_id_returns_string_none_when_none_passed(self) -> None:
        """get_validation_id returns the string 'None' when validation_id is None."""
        entry = ValidationEntry(logging.ERROR, "src", "msg", None)
        assert entry.get_validation_id() == "None"

    def test_get_validation_id_returns_string_none_when_empty_string_passed(self) -> None:
        """get_validation_id returns the string 'None' when validation_id is an empty string."""
        entry = ValidationEntry(logging.ERROR, "src", "msg", "")
        assert entry.get_validation_id() == "None"

    def test_get_json_returns_message_dict(self) -> None:
        """get_json returns dict with 'message' key containing the error message."""
        entry = ValidationEntry(logging.ERROR, "src", "my error message", "VID-1")
        result = entry.get_json()
        assert result == {"message": "my error message"}

    def test_get_json_message_key_only(self) -> None:
        """get_json dict contains exactly one key: 'message'."""
        entry = ValidationEntry(logging.DEBUG, "src", "debug msg")
        result = entry.get_json()
        assert list(result.keys()) == ["message"]

    def test_all_logging_levels_accepted(self) -> None:
        """ValidationEntry accepts all standard logging level integers."""
        for level in (logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL):
            entry = ValidationEntry(level, "src", "msg")
            assert entry.get_level() == level
