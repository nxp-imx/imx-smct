#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause

"""Unit tests for JsonFormatter and JsonMemoryHandler."""

# pylint: disable=protected-access

import json
import logging
import os
import pathlib

import pytest

from smct.configuration.configuration_provider import ConfigurationProvider
from smct.model.chip_model_provider import ChipModelProvider
from smct.resources.resource_database_provider import ResourceDatabaseProvider
from smct.validation.formatters.json_formatter import JsonFormatter, JsonMemoryHandler


@pytest.fixture(autouse=True)
def clear_providers() -> None:
    """Reset singleton providers around each test."""
    ConfigurationProvider.clear_configuration()
    ResourceDatabaseProvider.clear_database()
    ChipModelProvider.clear_model()


def _make_record(level: int, message: str) -> logging.LogRecord:
    """Create a minimal LogRecord at the given level with the given message."""
    record = logging.LogRecord(
        name="test_logger",
        level=level,
        pathname="test_file.py",
        lineno=42,
        msg=message,
        args=(),
        exc_info=None,
        func="test_function",
    )
    return record


class TestJsonFormatter:
    """Tests for JsonFormatter.format_logs and JsonFormatter._format_log."""

    def test_format_logs_returns_valid_json(self) -> None:
        """format_logs returns a string that parses as valid JSON."""
        formatter = JsonFormatter()
        records = [_make_record(logging.ERROR, "an error")]
        result = formatter.format_logs(records)
        parsed = json.loads(result)
        assert isinstance(parsed, dict)

    def test_format_logs_has_all_five_level_keys(self) -> None:
        """format_logs JSON output contains keys for all five log levels."""
        formatter = JsonFormatter()
        result = formatter.format_logs([])
        parsed = json.loads(result)
        assert set(parsed.keys()) == {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}

    def test_format_logs_routes_record_to_correct_level_key(self) -> None:
        """format_logs places each record under its levelname key."""
        formatter = JsonFormatter()
        records = [
            _make_record(logging.DEBUG, "debug msg"),
            _make_record(logging.INFO, "info msg"),
            _make_record(logging.WARNING, "warning msg"),
            _make_record(logging.ERROR, "error msg"),
            _make_record(logging.CRITICAL, "critical msg"),
        ]
        parsed = json.loads(formatter.format_logs(records))
        assert len(parsed["DEBUG"]) == 1
        assert len(parsed["INFO"]) == 1
        assert len(parsed["WARNING"]) == 1
        assert len(parsed["ERROR"]) == 1
        assert len(parsed["CRITICAL"]) == 1

    def test_format_logs_multiple_records_same_level(self) -> None:
        """format_logs accumulates multiple records under the same level key."""
        formatter = JsonFormatter()
        records = [
            _make_record(logging.ERROR, "first error"),
            _make_record(logging.ERROR, "second error"),
        ]
        parsed = json.loads(formatter.format_logs(records))
        assert len(parsed["ERROR"]) == 2
        messages = [r["description"] for r in parsed["ERROR"]]
        assert "first error" in messages
        assert "second error" in messages

    def test_format_logs_empty_list_gives_empty_level_lists(self) -> None:
        """format_logs with an empty records list gives empty lists for all level keys."""
        formatter = JsonFormatter()
        parsed = json.loads(formatter.format_logs([]))
        for level_key in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
            assert parsed[level_key] == []

    def test_format_log_with_validation_id_and_source(self) -> None:
        """_format_log uses record.validation_id and record.source when present."""
        formatter = JsonFormatter()
        record = _make_record(logging.ERROR, "msg")
        record.validation_id = "VID-5"  # type: ignore[attr-defined]
        record.source = "the_source"  # type: ignore[attr-defined]
        result = formatter._format_log(record)
        assert result["validation_id"] == "VID-5"
        assert result["source"] == "the_source"

    def test_format_log_without_validation_id_defaults_to_none_string(self) -> None:
        """_format_log uses 'None' string when record has no validation_id attribute."""
        formatter = JsonFormatter()
        record = _make_record(logging.ERROR, "msg")
        result = formatter._format_log(record)
        assert result["validation_id"] == "None"

    def test_format_log_without_source_defaults_to_unknown_source(self) -> None:
        """_format_log uses 'unknown source' string when record has no source attribute."""
        formatter = JsonFormatter()
        record = _make_record(logging.ERROR, "msg")
        result = formatter._format_log(record)
        assert result["source"] == "unknown source"

    def test_format_log_contains_filename_line_function_keys(self) -> None:
        """_format_log output contains 'filename', 'line', and 'function' keys."""
        formatter = JsonFormatter()
        record = _make_record(logging.INFO, "info msg")
        result = formatter._format_log(record)
        assert "filename" in result
        assert "line" in result
        assert "function" in result

    def test_format_log_line_is_lineno(self) -> None:
        """_format_log 'line' value equals record.lineno."""
        formatter = JsonFormatter()
        record = _make_record(logging.INFO, "msg")
        result = formatter._format_log(record)
        assert result["line"] == record.lineno

    def test_format_log_description_is_message(self) -> None:
        """_format_log 'description' equals record.getMessage()."""
        formatter = JsonFormatter()
        record = _make_record(logging.WARNING, "the log message")
        result = formatter._format_log(record)
        assert result["description"] == "the log message"


class TestJsonMemoryHandler:
    """Tests for JsonMemoryHandler."""

    def test_should_flush_always_returns_false(self, tmp_path: pathlib.Path) -> None:
        """shouldFlush returns False for any log record."""
        handler = JsonMemoryHandler(JsonFormatter(), str(tmp_path), "w")
        for level in (logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL):
            record = _make_record(level, "some msg")
            assert handler.shouldFlush(record) is False

    def test_flush_creates_error_log_json(self, tmp_path: pathlib.Path) -> None:
        """flush() writes error_log.json in the given output folder."""
        handler = JsonMemoryHandler(JsonFormatter(), str(tmp_path), "w")
        record = _make_record(logging.ERROR, "test error")
        handler.buffer.append(record)
        handler.flush()
        log_file = tmp_path / "error_log.json"
        assert log_file.exists()

    def test_flush_writes_valid_json(self, tmp_path: pathlib.Path) -> None:
        """flush() writes valid JSON to error_log.json."""
        handler = JsonMemoryHandler(JsonFormatter(), str(tmp_path), "w")
        record = _make_record(logging.ERROR, "structured error")
        handler.buffer.append(record)
        handler.flush()
        log_file = tmp_path / "error_log.json"
        with open(log_file, encoding="utf-8") as f:
            parsed = json.load(f)
        assert isinstance(parsed, dict)
        assert "ERROR" in parsed

    def test_flush_json_contains_expected_structure(self, tmp_path: pathlib.Path) -> None:
        """flush() JSON output has all five level keys with the buffered records routed correctly."""
        handler = JsonMemoryHandler(JsonFormatter(), str(tmp_path), "w")
        record_err = _make_record(logging.ERROR, "error entry")
        record_info = _make_record(logging.INFO, "info entry")
        handler.buffer.extend([record_err, record_info])
        handler.flush()
        with open(tmp_path / "error_log.json", encoding="utf-8") as f:
            parsed = json.load(f)
        assert len(parsed["ERROR"]) == 1
        assert len(parsed["INFO"]) == 1
        assert parsed["ERROR"][0]["description"] == "error entry"
        assert parsed["INFO"][0]["description"] == "info entry"

    def test_flush_creates_output_directory_if_missing(self, tmp_path: pathlib.Path) -> None:
        """flush() creates a non-existent nested output directory before writing."""
        nested_dir = tmp_path / "deeply" / "nested" / "logs"
        assert not nested_dir.exists()
        handler = JsonMemoryHandler(JsonFormatter(), str(nested_dir), "w")
        record = _make_record(logging.WARNING, "warning msg")
        handler.buffer.append(record)
        handler.flush()
        log_file = nested_dir / "error_log.json"
        assert log_file.exists()

    def test_flush_with_empty_buffer(self, tmp_path: pathlib.Path) -> None:
        """flush() with no buffered records writes JSON with empty level lists."""
        handler = JsonMemoryHandler(JsonFormatter(), str(tmp_path), "w")
        handler.flush()
        log_file = tmp_path / "error_log.json"
        assert log_file.exists()
        with open(log_file, encoding="utf-8") as f:
            parsed = json.load(f)
        for level_key in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
            assert parsed[level_key] == []

    def test_log_file_path_uses_output_folder(self, tmp_path: pathlib.Path) -> None:
        """The handler's log_file attribute is output_folder/error_log.json."""
        handler = JsonMemoryHandler(JsonFormatter(), str(tmp_path), "w")
        expected = os.path.join(str(tmp_path), "error_log.json")
        assert handler.log_file == expected
