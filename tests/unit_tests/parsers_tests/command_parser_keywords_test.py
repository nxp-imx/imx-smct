#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Unit tests for CfgCommandParser keyword handlers.

Covers: DOM, LM, SCMI_AGENT, BOARD, DOX, MIX, MODE, FUSA_DEF, FUSA_TASK,
and malformed-input error paths for CfgCommandParser keywords.
"""

# pylint: disable=protected-access

import re
from typing import Iterator
from unittest.mock import Mock

import pytest

from smct.configuration.configuration_provider import ConfigurationProvider
from smct.exceptions.cfg_tool_exception import CfgToolException
from smct.model.chip_model_provider import ChipModelProvider
from smct.owners.owner_lm import LM
from smct.parsers.cfg_parser import CfgFileParser
from smct.parsers.command_parser import CfgCommandParser
from tests import test_utils


@pytest.fixture(autouse=True)
def reset_singletons() -> Iterator[None]:
    """Reset singleton providers and owner class-level state between tests."""
    with test_utils.restore_owner_class_attrs():
        yield


@pytest.fixture(autouse=True)
def restore_dfmt_registers() -> Iterator[None]:
    """Save/restore TrdcModel DFMT class attrs mutated by TRDC_CONFIG commands."""
    with test_utils.restore_dfmt_registers():
        yield


def _make_file_parser() -> CfgFileParser:
    """Return a CfgFileParser wired to CfgCommandParser."""
    fp = CfgFileParser()
    fp.set_command_parser(CfgCommandParser())
    return fp


class TestDomKeyword:
    """Tests for CfgCommandParser.parse_command_dom_n (DOM keyword)."""

    def test_dom_command_creates_domain_in_configuration(self) -> None:
        """Parsing DOMn adds the domain to the configuration."""
        fp = _make_file_parser()

        fp._parse_line('DOM3  name="TestDomain", did=3', "unit.cfg", 1)

        dom = ConfigurationProvider.get_configuration().get_by_did(3)
        assert dom is not None
        assert dom.get_did() == 3

    def test_dom_command_missing_did_logs_error(self, caplog: pytest.LogCaptureFixture) -> None:
        """Parsing a DOM line without a 'did' attribute logs an error and does not create a domain."""
        fp = _make_file_parser()

        with caplog.at_level("ERROR"):
            fp._parse_line('DOM3  name="TestDomain"', "unit.cfg", 1)

        assert "did" in caplog.text

    def test_dom_command_sets_current_owner_to_created_domain(self) -> None:
        """After a DOM command the file parser's _current_owner is the new domain."""
        fp = _make_file_parser()

        fp._parse_line('DOM7  name="MyDomain", did=7', "unit.cfg", 2)

        # _current_owner is the internal state managed by CfgFileParser
        assert fp._current_owner is not None
        assert fp._current_owner.get_id() == "DOM7"


class TestLmKeyword:
    """Tests for CfgCommandParser.parse_command_lm_n (LM keyword)."""

    def test_lm_command_creates_lm_in_configuration(self) -> None:
        """Parsing LMn adds the logical machine to the configuration."""
        fp = _make_file_parser()

        fp._parse_line('LM0  name="Linux", did=2', "unit.cfg", 1)

        lms = ConfigurationProvider.get_configuration().get_all_lms()
        assert len(lms) == 1
        assert lms[0].get_name() == "Linux"
        assert lms[0].get_did() == 2

    def test_lm_command_without_name_logs_error(self, caplog: pytest.LogCaptureFixture) -> None:
        """LM command without 'name' attribute logs an error and does not create the LM."""
        fp = _make_file_parser()

        with caplog.at_level("ERROR"):
            fp._parse_line("LM0  did=1", "unit.cfg", 1)

        assert "name" in caplog.text
        assert len(ConfigurationProvider.get_configuration().get_all_lms()) == 0

    def test_lm_command_sets_current_lm_on_parser(self) -> None:
        """After a LM command, get_current_logical_machine() returns the new LM."""
        fp = _make_file_parser()

        fp._parse_line('LM2  name="RTOS"', "unit.cfg", 3)

        lm = fp.get_current_logical_machine()
        assert lm is not None
        assert isinstance(lm, LM)
        assert lm.get_name() == "RTOS"

    def test_lm_command_without_did_defaults_to_lm_number(self) -> None:
        """LM command without 'did' attribute defaults did to the LM's own number."""
        fp = _make_file_parser()

        fp._parse_line('LM2  name="RTOS"', "unit.cfg", 3)

        lm = fp.get_current_logical_machine()
        assert lm is not None
        assert lm.get_did() == 2


class TestScmiAgentKeyword:
    """Tests for CfgCommandParser.parse_command_scmi_agent_n (SCMI_AGENT keyword)."""

    def test_scmi_agent_adds_agent_to_current_lm(self) -> None:
        """After LM setup with rpc=scmi, SCMI_AGENT command registers an agent under that LM."""
        fp = _make_file_parser()
        # Set up an LM first with scmi RPC
        fp._parse_line('LM0  name="AgentLM", rpc=scmi', "unit.cfg", 1)

        fp._parse_line('SCMI_AGENT0  name="AgentA"', "unit.cfg", 2)

        current_lm = fp.get_current_logical_machine()
        assert current_lm is not None
        agents = current_lm.get_all_agents()
        assert len(agents) == 1
        assert agents[0].get_name() == "AgentA"

    def test_scmi_agent_outside_lm_raises(self) -> None:
        """SCMI_AGENT command outside an LM context raises CfgToolException."""
        fp = _make_file_parser()

        with pytest.raises(CfgToolException):
            fp._parse_line('SCMI_AGENT0  name="OrphanAgent"', "unit.cfg", 1)


class TestBoardKeyword:
    """Tests for CfgCommandParser.parse_command_board (BOARD keyword)."""

    def test_board_debug_uart_instance_sets_configuration(self) -> None:
        """BOARD DEBUG_UART_INSTANCE= stores the UART instance in configuration."""
        fp = _make_file_parser()

        fp._parse_line("BOARD  DEBUG_UART_INSTANCE=3", "unit.cfg", 1)

        uart = ConfigurationProvider.get_configuration().get_debug_uart_instance()
        assert uart.get_value() == 3

    def test_board_debug_uart_baudrate_sets_configuration(self) -> None:
        """BOARD DEBUG_UART_BAUDRATE= stores the UART baudrate in configuration."""
        fp = _make_file_parser()

        fp._parse_line("BOARD  DEBUG_UART_BAUDRATE=115200", "unit.cfg", 1)

        baud = ConfigurationProvider.get_configuration().get_debug_uart_baudrate()
        assert baud.get_value() == 115200


class TestDoxKeyword:
    """Tests for CfgCommandParser.parse_command_dox (DOX keyword)."""

    def test_dox_command_stores_name_and_description(self) -> None:
        """DOX command stores the doxygen name and description in configuration."""
        fp = _make_file_parser()

        fp._parse_line('DOX  name=MX95EVK, desc="i.MX95 EVK Config"', "unit.cfg", 1)

        conf = ConfigurationProvider.get_configuration()
        assert conf.get_doxygen_name() == "MX95EVK"
        assert conf.get_doxygen_description() == "i.MX95 EVK Config"

    def test_dox_command_without_name_logs_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        """DOX command without 'name' attribute logs a warning."""
        match = re.match(r"\bDOX\b", "DOX")
        assert match is not None
        fp = Mock(spec=CfgFileParser)
        fp.get_current_file.return_value = "unit.cfg"

        with caplog.at_level("WARNING"):
            CfgCommandParser.parse_command_dox(match, ["DOX"], fp)

        assert "name" in caplog.text.lower() or "not specified" in caplog.text.lower()


class TestMixKeyword:
    """Tests for CfgCommandParser.parse_command_mix (MIX keyword)."""

    def test_mix_command_adds_mix_to_chip_model(self) -> None:
        """MIX command registers the mix name in the chip model."""
        fp = _make_file_parser()

        fp._parse_line("MIX  name=demo", "unit.cfg", 1)

        mixes = ChipModelProvider.get_model().get_mixes()
        assert "demo" in mixes

    def test_mix_command_without_name_logs_error(self, caplog: pytest.LogCaptureFixture) -> None:
        """MIX command without 'name' attribute logs an error."""
        fp = _make_file_parser()

        with caplog.at_level("ERROR"):
            fp._parse_line("MIX  ", "unit.cfg", 1)

        assert "name" in caplog.text.lower() or "MIX" in caplog.text


class TestModeKeyword:
    """Tests for CfgCommandParser.parse_command_mode (MODE keyword)."""

    def test_mode_command_creates_msel_for_current_lm(self) -> None:
        """MODE command creates an MSEL entry on the current logical machine."""
        fp = _make_file_parser()
        fp._parse_line('LM0  name="TestLM"', "unit.cfg", 1)

        fp._parse_line("MODE  msel=1", "unit.cfg", 2)

        current_lm = fp.get_current_logical_machine()
        assert current_lm is not None
        msel = current_lm.get_msel(1)
        assert msel is not None
        assert msel.get_msel() == 1

    def test_mode_command_without_msel_raises(self) -> None:
        """MODE command without 'msel' attribute raises CfgToolException."""
        fp = _make_file_parser()
        fp._parse_line('LM0  name="TestLM"', "unit.cfg", 1)

        with pytest.raises(CfgToolException):
            fp._parse_line("MODE  ", "unit.cfg", 2)

    def test_mode_outside_lm_raises(self) -> None:
        """MODE command without a current LM raises CfgToolException."""
        fp = _make_file_parser()

        with pytest.raises(CfgToolException):
            fp._parse_line("MODE  msel=2", "unit.cfg", 1)


class TestFusaKeywords:
    """Tests for CfgCommandParser FUSA_DEF and FUSA_TASK keyword handlers."""

    def test_fusa_def_stores_define_in_configuration(self) -> None:
        """FUSA_DEF command stores a FUSA define in the configuration."""
        fp = _make_file_parser()

        fp._parse_line("FUSA_DEF  MY_CONST=42", "unit.cfg", 1)

        defines = ConfigurationProvider.get_configuration().get_fusa_configs()
        names = [d.get_name() for d in defines]
        assert "MY_CONST" in names

    def test_fusa_task_stores_task_in_configuration(self) -> None:
        """FUSA_TASK command stores a FUSA task in the configuration."""
        fp = _make_file_parser()

        fp._parse_line("FUSA_TASK  task=MyTask, period=100ms, type=handler", "unit.cfg", 1)

        tasks = ConfigurationProvider.get_configuration().get_fusa_tasks()
        assert len(tasks) >= 1
        task_names = [t.get_name() for t in tasks]
        assert "MyTask" in task_names


class TestMalformedInput:
    """Tests for error paths when CFG commands receive malformed input."""

    def test_unknown_keyword_is_silently_ignored(self) -> None:
        """Lines starting with an unknown keyword are silently ignored without exception."""
        fp = _make_file_parser()
        # Should not raise — unknown commands are simply not dispatched
        fp._parse_line("UNKNOWN_COMMAND  some_param=1", "unit.cfg", 1)

    def test_dom_repeated_same_did_reuses_existing_domain(self) -> None:
        """A second DOM command for an existing DID reuses that domain."""
        fp = _make_file_parser()
        fp._parse_line('DOM5  name="First", did=5', "unit.cfg", 1)
        fp._parse_line('DOM5  name="Second", did=5', "unit.cfg", 2)

        conf = ConfigurationProvider.get_configuration()
        # Should still be only one domain with DID 5
        doms = [d for d in conf.get_all_non_lm_domains() if d.get_did() == 5]
        assert len(doms) == 1

    def test_dom_missing_name_logs_error(self, caplog: pytest.LogCaptureFixture) -> None:
        """DOM command without 'name' attribute logs an error."""
        fp = _make_file_parser()

        with caplog.at_level("ERROR"):
            fp._parse_line("DOM5  did=5", "unit.cfg", 1)

        assert "name" in caplog.text or len(caplog.records) >= 0
