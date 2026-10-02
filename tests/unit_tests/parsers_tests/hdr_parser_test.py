#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Unit tests for smct.parsers.hdr_parser SM FW header parsing."""

# pylint: disable=protected-access

import os
from typing import List
from unittest.mock import Mock, mock_open, patch

import pytest

from smct.configuration.configuration_provider import ConfigurationProvider
from smct.model.chip_model_provider import ChipModelProvider
from smct.parsers.hdr_parser import ApiResourceParser, HeaderParser
from smct.resources.resource_database_provider import ResourceDatabaseProvider


@pytest.fixture(autouse=True)
def reset_singletons() -> None:
    """Reset singleton providers and header parser patterns."""
    ConfigurationProvider.clear_configuration()
    ResourceDatabaseProvider.clear_database()
    ChipModelProvider.clear_model()
    HeaderParser._patterns = {}


class TestHeaderParser:
    """Tests for generic header parsing."""

    def test_add_pattern_stores_compiled_pattern_with_template_copy(self) -> None:
        """Registered header patterns are compiled and templates are copied."""
        template = {"name": None, "type": "API", "cat": "DEV", "api": "PD"}
        parser = HeaderParser()

        parser.add_pattern(r"#define\s+DEV_SM_(PD_\w+)\s+\S", template)
        template["api"] = "CLK"

        assert len(HeaderParser._patterns) == 1
        stored_template = next(iter(HeaderParser._patterns.values()))
        assert stored_template["api"] == "PD"

    def test_parse_file_creates_resource_for_matching_define(self) -> None:
        """A matching define line is converted to an atomic resource and stored."""
        parser = HeaderParser()
        parser.add_pattern(r"#define\s+DEV_SM_(PD_\w+)\s+\S", {"name": None, "type": "API", "cat": "DEV", "api": "PD"})

        with (
            patch("smct.parsers.hdr_parser.os.path.isfile", return_value=True),
            patch("builtins.open", mock_open(read_data="#define DEV_SM_PD_TEST 1\n#define IGNORED 2\n")),
        ):
            parser._parse_file("dev_sm_test.h")

        resources = ResourceDatabaseProvider.get_database().find_atomic_resource_by("name", "PD_TEST")
        assert len(resources) == 1
        assert resources[0].get_api_id() == "DEV_SM_PD_TEST"

    def test_parse_dir_or_file_recurses_only_matching_headers(self) -> None:
        """Directory parsing visits matching files in nested directories."""
        parser = HeaderParser()

        def is_file(path: str) -> bool:
            return path in {os.path.join("root", "dev_sm_root.h"), os.path.join("root", "nested", "dev_sm_nested.h")}

        def is_dir(path: str) -> bool:
            return path in {"root", os.path.join("root", "nested")}

        def list_dir(path: str) -> list[str]:
            return ["dev_sm_root.h", "readme.txt", "nested"] if path == "root" else ["dev_sm_nested.h"]

        with patch.object(HeaderParser, "_parse_file", autospec=True) as parse_file:
            with (
                patch("smct.parsers.hdr_parser.os.path.isfile", side_effect=is_file),
                patch("smct.parsers.hdr_parser.os.path.isdir", side_effect=is_dir),
                patch("smct.parsers.hdr_parser.os.listdir", side_effect=list_dir),
            ):
                result = parser.parse_dir_or_file("root", r"dev_sm_.*\.h")

        assert result is True
        parsed_paths = {os.path.basename(call.args[1]) for call in parse_file.call_args_list}
        assert parsed_paths == {"dev_sm_root.h", "dev_sm_nested.h"}

    def test_parse_dir_or_file_excludes_backup_files(self) -> None:
        """Anchored pattern excludes editor backup files (.bak, .orig)."""
        parser = HeaderParser()

        def is_file(path: str) -> bool:
            return path in {
                os.path.join("sm", "dev_sm_root.h"),
                os.path.join("sm", "dev_sm_root.h.bak"),
                os.path.join("sm", "dev_sm_root.h.orig"),
            }

        def is_dir(path: str) -> bool:
            return path == "sm"

        def list_dir(path: str) -> List[str]:
            return ["dev_sm_root.h", "dev_sm_root.h.bak", "dev_sm_root.h.orig"]

        with patch.object(HeaderParser, "_parse_file", autospec=True) as parse_file:
            with (
                patch("smct.parsers.hdr_parser.os.path.isfile", side_effect=is_file),
                patch("smct.parsers.hdr_parser.os.path.isdir", side_effect=is_dir),
                patch("smct.parsers.hdr_parser.os.listdir", side_effect=list_dir),
            ):
                result = parser.parse_dir_or_file("sm", r"dev_sm_.*\.h$")

        assert result is True
        parsed_paths = [call.args[1] for call in parse_file.call_args_list]
        assert parsed_paths == [os.path.join("sm", "dev_sm_root.h")]


class TestApiResourceParser:
    """Tests for API resource parser wiring."""

    def test_parse_device_returns_false_for_missing_device_path(self) -> None:
        """Invalid device directories are reported as parse failures."""
        parser = ApiResourceParser()

        assert parser.parse_device("root", "missing") is False

    def test_parse_board_registers_board_patterns_and_parses_directory(self) -> None:
        """Board parsing wires header patterns and delegates to HeaderParser."""
        header_parser = Mock(spec=HeaderParser)
        header_parser.parse_dir_or_file.return_value = True

        with patch("smct.parsers.hdr_parser.HeaderParser", return_value=header_parser), patch("smct.parsers.hdr_parser.os.path.exists", return_value=True):
            result = ApiResourceParser().parse_board("root", "board")

        assert result is True
        assert header_parser.add_pattern.call_count > 5
        first_pattern = header_parser.add_pattern.call_args_list[0].args[0]
        assert "BRD_SM_PD" in first_pattern
        header_parser.parse_dir_or_file.assert_called_once()
        assert header_parser.parse_dir_or_file.call_args.args[1] == r"brd_sm_.*\.h$"

    def test_parse_device_registers_device_patterns_and_parses_directory(self) -> None:
        """Device parsing wires header patterns and delegates to HeaderParser."""
        header_parser = Mock(spec=HeaderParser)
        header_parser.parse_dir_or_file.return_value = True

        with patch("smct.parsers.hdr_parser.HeaderParser", return_value=header_parser), patch("smct.parsers.hdr_parser.os.path.exists", return_value=True):
            result = ApiResourceParser().parse_device("root", "device")

        assert result is True
        assert header_parser.add_pattern.call_count > 5
        first_pattern = header_parser.add_pattern.call_args_list[0].args[0]
        assert "DEV_SM_" in first_pattern and "PD_" in first_pattern
        header_parser.parse_dir_or_file.assert_called_once()
        assert header_parser.parse_dir_or_file.call_args.args[1] == r"dev_sm_.*\.h$"
