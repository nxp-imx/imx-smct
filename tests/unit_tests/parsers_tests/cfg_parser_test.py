#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Unit tests for smct.parsers.cfg_parser CFG file parser wiring."""

import os
from unittest.mock import Mock, patch

import pytest

from smct.configuration.configuration_provider import ConfigurationProvider
from smct.model.chip_model_provider import ChipModelProvider
from smct.parsers.cfg_parser import CfgFileParser
from smct.parsers.hdr_parser import ApiResourceParser
from smct.resources.resource_database_provider import ResourceDatabaseProvider


@pytest.fixture(autouse=True)
def reset_singletons() -> None:
    """Reset singleton providers used by parsers."""
    ConfigurationProvider.clear_configuration()
    ResourceDatabaseProvider.clear_database()
    ChipModelProvider.clear_model()


class TestCfgFileParser:
    """Tests for top-level CFG file parser wiring."""

    def test_construction_initializes_empty_state(self) -> None:
        """A new CFG parser starts without current file, owner, headers, or includes."""
        parser = CfgFileParser()

        assert parser.get_current_file() is None
        assert parser.get_current_line() is None
        assert parser.get_current_logical_machine() is None
        assert parser.get_current_agent() is None
        assert parser.get_header_parser() is None
        assert parser.get_root_directory() is None
        assert not parser.get_include_list()

    def test_enable_board_parser_stores_parser_and_root_directory(self) -> None:
        """Board parser wiring is exposed through getters used by MAKE parsing."""
        parser = CfgFileParser()
        header_parser = Mock(spec=ApiResourceParser)

        parser.enable_board_parser(header_parser, "root_dir")

        assert parser.get_header_parser() is header_parser
        assert parser.get_root_directory() == "root_dir"

    def test_add_static_resources_registers_sys_and_fusa_automatic_resources(self) -> None:
        """Static API resources are added to the resource database."""
        CfgFileParser.add_static_resources()

        database = ResourceDatabaseProvider.get_database()
        assert len(database.find_atomic_resource_by("name", "SYS")) == 1
        assert len(database.find_atomic_resource_by("name", "FUSA")) == 1

    def test_parse_device_builds_device_cfg_path(self) -> None:
        """Device parsing delegates to parse_file with the standard device CFG path."""
        parser = CfgFileParser()

        with patch.object(parser, "parse_file") as parse_file:
            parser.parse_device("C:\\root", "MIMX95")

        parse_file.assert_called_once_with(os.path.join("C:\\root", "devices", "MIMX95", "configtool", "device.cfg"))
