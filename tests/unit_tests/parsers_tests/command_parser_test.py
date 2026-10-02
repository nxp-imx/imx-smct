#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Unit tests for smct.parsers.command_parser command dispatch and preprocessing."""

# pylint: disable=protected-access

import re
from unittest.mock import Mock

import pytest

from smct.configuration.configuration_provider import ConfigurationProvider
from smct.model.chip_model_provider import ChipModelProvider
from smct.parsers.cfg_parser import CfgFileParser
from smct.parsers.command_parser import CfgCommandParser, CfgPreprocessor, CommandParser
from smct.resources.res_api import ApiResource
from smct.resources.resource_database_provider import ResourceDatabaseProvider


@pytest.fixture(autouse=True)
def reset_singletons() -> None:
    """Reset singleton providers used by parsers."""
    ConfigurationProvider.clear_configuration()
    ResourceDatabaseProvider.clear_database()
    ChipModelProvider.clear_model()


class TestCommandParser:
    """Tests for the base command parser."""

    def test_parse_command_auto_create_res_returns_true(self) -> None:
        """Base auto-create hook allows line processing to continue."""
        result = CommandParser.parse_command_auto_create_res(Mock(spec=re.Match), ["LMM_1"], Mock(spec=CfgFileParser))

        assert result is True

    def test_pass_through_handlers_do_not_mutate_atoms(self) -> None:
        """Base pass-through handlers leave parsed atoms unchanged."""
        atoms = ["MAKE", "soc=MIMX95"]

        CommandParser.parse_command_make(Mock(spec=re.Match), atoms, Mock(spec=CfgFileParser))

        assert atoms == ["MAKE", "soc=MIMX95"]


class TestCfgCommandParser:
    """Tests for CFG command parser behavior."""

    def test_parse_command_auto_create_res_adds_lmm_resource(self) -> None:
        """Auto-created LMM resources are registered in the resource database."""
        match = re.match(r"\b((LMM)_\d+)\b", "LMM_3")
        assert match is not None

        result = CfgCommandParser.parse_command_auto_create_res(match, ["LMM_3", "test=1"], Mock(spec=CfgFileParser))

        resources = ResourceDatabaseProvider.get_database().find_atomic_resource_by("name", "LMM_3")
        assert result is True
        assert len(resources) == 1
        assert isinstance(resources[0], ApiResource)
        assert resources[0].get_api_id() == "3"

    def test_parse_command_auto_create_res_does_not_duplicate_existing_resource(self) -> None:
        """Existing automatic API resources are reused instead of duplicated."""
        match = re.match(r"\b((BASE)_\d+)\b", "BASE_2")
        assert match is not None

        CfgCommandParser.parse_command_auto_create_res(match, ["BASE_2"], Mock(spec=CfgFileParser))
        CfgCommandParser.parse_command_auto_create_res(match, ["BASE_2"], Mock(spec=CfgFileParser))

        assert len(ResourceDatabaseProvider.get_database().find_atomic_resource_by("name", "BASE_2")) == 1


class TestCfgPreprocessor:
    """Tests for CFG preprocessor behavior."""

    def test_parse_command_lm_n_adds_automatic_lmm_resource(self) -> None:
        """LM preprocessing creates the corresponding LMM API resource."""
        match = re.match(r"\bLM(\d+)\b", "LM4")
        assert match is not None

        CfgPreprocessor.parse_command_lm_n(match, ["LM4"], Mock(spec=CfgFileParser))

        resources = ResourceDatabaseProvider.get_database().find_atomic_resource_by("name", "LMM_4")
        assert len(resources) == 1
        assert resources[0].get_api_id() == "4"

    def test_parse_command_scmi_agent_n_adds_automatic_base_resource(self) -> None:
        """SCMI agent preprocessing creates the corresponding BASE API resource."""
        match = re.match(r"\bSCMI_AGENT(\d*)\b", "SCMI_AGENT7")
        assert match is not None

        CfgPreprocessor.parse_command_scmi_agent_n(match, ["SCMI_AGENT7"], Mock(spec=CfgFileParser))

        resources = ResourceDatabaseProvider.get_database().find_atomic_resource_by("name", "BASE_AGENT_7")
        assert len(resources) == 1
        assert resources[0].get_api_id() == "DEV_SM_BASE_AGENT_7"


class TestCommandDispatch:
    """Tests for command dispatch from CfgFileParser to CommandParser."""

    def test_parse_line_dispatches_first_atom_to_registered_handler(self) -> None:
        """CfgFileParser tokenizes a line and dispatches it to the matching command hook."""
        file_parser = CfgFileParser()
        command_parser = Mock(spec=CommandParser)
        command_parser.parse_command_lm_n.return_value = None
        file_parser.set_command_parser(command_parser)

        file_parser._parse_line("LM7 name=Linux", "unit.cfg", 12)

        command_parser.parse_command_lm_n.assert_called_once()
        match, atoms, parser = command_parser.parse_command_lm_n.call_args.args
        assert match.group(1) == "7"
        assert atoms == ["LM7", "name=Linux"]
        assert parser is file_parser
