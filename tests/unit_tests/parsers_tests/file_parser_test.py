#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Unit tests for smct.parsers.file_parser generic regex file parser."""

# pylint: disable=protected-access

from unittest.mock import mock_open, patch

import pytest

from smct.configuration.configuration_provider import ConfigurationProvider
from smct.model.chip_model_provider import ChipModelProvider
from smct.parsers.file_parser import FileParser
from smct.resources.resource_database_provider import ResourceDatabaseProvider


@pytest.fixture(autouse=True)
def reset_singletons() -> None:
    """Reset singleton providers used by parsers."""
    ConfigurationProvider.clear_configuration()
    ResourceDatabaseProvider.clear_database()
    ChipModelProvider.clear_model()


class TestFileParser:
    """Tests for the generic file parser."""

    def test_construction_initializes_empty_patterns_and_results(self) -> None:
        """A new parser has no registered patterns or previous matches."""
        parser = FileParser()

        assert not parser._patterns
        assert not parser.get_results()

    def test_add_regex_registers_pattern_for_later_parsing(self) -> None:
        """Patterns added through the public API are stored in order."""
        parser = FileParser()

        parser.add_regex(r"VALUE_(\w+)")
        parser.add_regex(r"OTHER_(\w+)")

        assert parser._patterns == [r"VALUE_(\w+)", r"OTHER_(\w+)"]

    def test_parse_collects_all_matches_for_registered_pattern(self) -> None:
        """Parsing finds repeated occurrences of each registered regex."""
        parser = FileParser()
        parser.add_regex(r"VALUE_(\w+)")

        with patch("smct.parsers.file_parser.os.path.exists", return_value=True), patch("builtins.open", mock_open(read_data="VALUE_one\nVALUE_two\n")):
            parser.parse("input.txt")

        matches = parser.get_results()[r"VALUE_(\w+)"]
        assert [match.group(1) for match in matches] == ["one", "two"]

    def test_parse_missing_file_leaves_results_empty(self) -> None:
        """Missing files are ignored without creating result entries."""
        parser = FileParser()
        parser.add_regex(r"VALUE_(\w+)")

        parser.parse("missing.txt")

        assert not parser.get_results()

    def test_parse_can_ignore_comment_lines_with_regex(self) -> None:
        """Line-aware regexes can select non-comment configuration lines only."""
        parser = FileParser()
        parser.add_regex(r"(?m)^(?!#)\s*(VALUE_\w+)")

        with patch("smct.parsers.file_parser.os.path.exists", return_value=True), patch("builtins.open", mock_open(read_data="# VALUE_comment\nVALUE_real\n")):
            parser.parse("input.cfg")

        matches = parser.get_results()[r"(?m)^(?!#)\s*(VALUE_\w+)"]
        assert [match.group(1) for match in matches] == ["VALUE_real"]
