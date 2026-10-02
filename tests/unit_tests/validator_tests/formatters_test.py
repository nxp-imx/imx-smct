#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause

"""Unit tests for ValidationEntryFormatterBase and ConsoleFormatter."""

import logging

import pytest

from smct.configuration.configuration_provider import ConfigurationProvider
from smct.model.chip_model_provider import ChipModelProvider
from smct.resources.resource_database_provider import ResourceDatabaseProvider
from smct.validation.formatters.console_formatter import ConsoleFormatter
from smct.validation.formatters.validation_entry_formatter_base import ValidationEntryFormatterBase
from smct.validation.validation_entry import ValidationEntry


@pytest.fixture(autouse=True)
def clear_providers() -> None:
    """Reset singleton providers around each test."""
    ConfigurationProvider.clear_configuration()
    ResourceDatabaseProvider.clear_database()
    ChipModelProvider.clear_model()


class TestValidationEntryFormatterBase:
    """Tests for ValidationEntryFormatterBase (no-op base)."""

    def test_process_entry_returns_none(self) -> None:
        """process_entry on the base class returns None (no-op)."""
        formatter = ValidationEntryFormatterBase()
        entry = ValidationEntry(logging.ERROR, "src", "msg", "VID-1")
        formatter.process_entry(entry)  # should not raise and implicitly returns None

    def test_process_entry_does_not_raise(self) -> None:
        """process_entry on the base class does not raise for any validation entry."""
        formatter = ValidationEntryFormatterBase()
        for level in (logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL):
            entry = ValidationEntry(level, "source", "message")
            formatter.process_entry(entry)  # should not raise


class TestConsoleFormatter:
    """Tests for ConsoleFormatter.process_entry."""

    def test_process_entry_logs_at_correct_level(self, caplog: pytest.LogCaptureFixture) -> None:
        """process_entry logs at the level specified by the ValidationEntry."""
        formatter = ConsoleFormatter()
        entry = ValidationEntry(logging.ERROR, "test_src", "an error occurred", "VID-7")

        with caplog.at_level(logging.DEBUG):
            formatter.process_entry(entry)

        assert len(caplog.records) == 1
        assert caplog.records[0].levelno == logging.ERROR

    def test_process_entry_logs_error_message(self, caplog: pytest.LogCaptureFixture) -> None:
        """process_entry logs the ValidationEntry error message as the log message."""
        formatter = ConsoleFormatter()
        entry = ValidationEntry(logging.WARNING, "src", "something went wrong")

        with caplog.at_level(logging.DEBUG):
            formatter.process_entry(entry)

        assert caplog.records[0].getMessage() == "something went wrong"

    def test_process_entry_attaches_source_to_record(self, caplog: pytest.LogCaptureFixture) -> None:
        """process_entry passes 'source' from the entry via extra dict to the log record."""
        formatter = ConsoleFormatter()
        entry = ValidationEntry(logging.ERROR, "my_source_file.cfg", "err msg", "VID-3")

        with caplog.at_level(logging.DEBUG):
            formatter.process_entry(entry)

        record = caplog.records[0]
        assert hasattr(record, "source")
        assert record.source == "my_source_file.cfg"  # type: ignore[attr-defined]

    def test_process_entry_attaches_validation_id_to_record(self, caplog: pytest.LogCaptureFixture) -> None:
        """process_entry passes 'validation_id' from the entry via extra dict to the log record."""
        formatter = ConsoleFormatter()
        entry = ValidationEntry(logging.ERROR, "src", "err msg", "VID-99")

        with caplog.at_level(logging.DEBUG):
            formatter.process_entry(entry)

        record = caplog.records[0]
        assert hasattr(record, "validation_id")
        assert record.validation_id == "VID-99"  # type: ignore[attr-defined]

    def test_process_entry_validation_id_none_string_when_unset(self, caplog: pytest.LogCaptureFixture) -> None:
        """process_entry passes the string 'None' as validation_id when entry has no id."""
        formatter = ConsoleFormatter()
        entry = ValidationEntry(logging.WARNING, "src", "warn msg")

        with caplog.at_level(logging.DEBUG):
            formatter.process_entry(entry)

        record = caplog.records[0]
        assert record.validation_id == "None"  # type: ignore[attr-defined]

    def test_process_entry_info_level(self, caplog: pytest.LogCaptureFixture) -> None:
        """process_entry logs at INFO level when ValidationEntry level is INFO."""
        formatter = ConsoleFormatter()
        entry = ValidationEntry(logging.INFO, "src", "info message")

        with caplog.at_level(logging.DEBUG):
            formatter.process_entry(entry)

        assert caplog.records[0].levelno == logging.INFO

    def test_process_entry_debug_level(self, caplog: pytest.LogCaptureFixture) -> None:
        """process_entry logs at DEBUG level when ValidationEntry level is DEBUG."""
        formatter = ConsoleFormatter()
        entry = ValidationEntry(logging.DEBUG, "src", "debug message")

        with caplog.at_level(logging.DEBUG):
            formatter.process_entry(entry)

        assert caplog.records[0].levelno == logging.DEBUG
