#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Unit tests for smct.generation.gen_test GeneratorTest."""

# pylint: disable=protected-access

import logging
import os
from pathlib import Path
from unittest.mock import Mock

import pytest

from smct.configuration.confdata import ConfigurationData
from smct.generation.gen_test import GeneratorTest
from smct.owners.owner_agent import MailboxMu, ScmiAgent, ScmiChannel, SmtChannel
from smct.owners.owner_base import AssignedResource
from smct.owners.owner_lm import LM
from smct.resources.res_api import ApiResource
from smct.resources.resource_base import AtomicResource
from smct.utils import FormatedInt
from tests import test_utils


def _generate_and_read(conf: ConfigurationData, generator: GeneratorTest, directory: Path) -> str:
    """Generate config_test.h and return its content."""
    generator.generate(conf, str(directory))
    file_path = os.path.join(str(directory), "config_test.h")
    with open(file_path, "r", encoding="utf-8") as fh:
        return fh.read()


def _make_lm(lm_id: str, did: int, name: str) -> LM:
    """Create a minimal LM with no RPC and default settings."""
    return LM(lm_id, did, name, None, None, None, None, None, False)


class TestGeneratorTest:
    """Tests for GeneratorTest."""

    def test_generate_empty_config_produces_test_header_with_include(self, tmp_path: Path) -> None:
        """Test that empty config produces the config_test.h with include."""
        directory = tmp_path
        generator = GeneratorTest()
        conf = ConfigurationData()

        content = _generate_and_read(conf, generator, directory)

        assert '#include "config_user.h"' in content

    def test_generate_empty_config_produces_sm_num_test_chn_zero(self, tmp_path: Path) -> None:
        """Test that empty config produces SM_NUM_TEST_CHN with value 0."""
        directory = tmp_path
        generator = GeneratorTest()
        conf = ConfigurationData()

        content = _generate_and_read(conf, generator, directory)

        assert "SM_NUM_TEST_CHN  0U" in content

    def test_generate_empty_config_produces_sm_scmi_num_test_zero(self, tmp_path: Path) -> None:
        """Test that empty config produces SM_SCMI_NUM_TEST with value 0."""
        directory = tmp_path
        generator = GeneratorTest()
        conf = ConfigurationData()

        content = _generate_and_read(conf, generator, directory)

        assert "SM_SCMI_NUM_TEST  0U" in content

    def test_generate_empty_config_produces_sm_test_chn_config_data(self, tmp_path: Path) -> None:
        """Test that empty config produces SM_TEST_CHN_CONFIG_DATA macro."""
        directory = tmp_path
        generator = GeneratorTest()
        conf = ConfigurationData()

        content = _generate_and_read(conf, generator, directory)

        assert "SM_TEST_CHN_CONFIG_DATA" in content

    def test_generate_empty_config_produces_sm_scmi_test_config_data(self, tmp_path: Path) -> None:
        """Test that empty config produces SM_SCMI_TEST_CONFIG_DATA macro."""
        directory = tmp_path
        generator = GeneratorTest()
        conf = ConfigurationData()

        content = _generate_and_read(conf, generator, directory)

        assert "SM_SCMI_TEST_CONFIG_DATA" in content

    def test_generate_empty_config_no_default_channel_macro(self, tmp_path: Path) -> None:
        """Test that with no SCMI channels SM_TEST_DEFAULT_CHN is not produced."""
        directory = tmp_path
        generator = GeneratorTest()
        conf = ConfigurationData()

        content = _generate_and_read(conf, generator, directory)

        assert "SM_TEST_DEFAULT_CHN" not in content

    def test_generate_with_lm_no_agents_produces_lm_heading(self, tmp_path: Path) -> None:
        """Test that a single LM with no agents produces its heading."""
        test_utils.set_up()
        directory = tmp_path
        generator = GeneratorTest()
        conf = ConfigurationData()
        conf.add_lm(_make_lm("lm0", 0, "BaseLM"))

        content = _generate_and_read(conf, generator, directory)

        assert "LM0 Test Config" in content

    def test_str_returns_test_generator(self) -> None:
        """Test string representation of the generator."""
        generator = GeneratorTest()
        assert str(generator) == "TEST generator"

    def test_get_generator_info_returns_test_name_and_include(self) -> None:
        """Test that generator info declares 'test' name and config_user.h include."""
        generator = GeneratorTest()
        info = generator._get_generator_info()
        assert info["name"] == "test"
        assert "config_user.h" in info.get("incl", [])

    def test_get_doxygen_file_name_returns_empty_string(self) -> None:
        """Test that doxygen file name is an empty string."""
        generator = GeneratorTest()
        assert generator._get_doxygen_file_name() == ""

    def test_generate_empty_config_produces_test_channel_config_heading(self, tmp_path: Path) -> None:
        """Test that the 'Test Channel Config' section heading is produced."""
        directory = tmp_path
        generator = GeneratorTest()
        conf = ConfigurationData()

        content = _generate_and_read(conf, generator, directory)

        assert "Test Channel Config" in content

    def test_generate_empty_config_produces_test_config_heading(self, tmp_path: Path) -> None:
        """Test that the 'Test Config' section heading is produced."""
        directory = tmp_path
        generator = GeneratorTest()
        conf = ConfigurationData()

        content = _generate_and_read(conf, generator, directory)

        assert "Test Config" in content

    def test_generate_with_smt_channel_mu_mailbox_no_test_increments_mailbox_counter(self, tmp_path: Path) -> None:
        """Test SmtChannel with MailboxMu(test=None, sma!=None) covers counter/sma paths."""
        test_utils.set_up()
        directory = tmp_path
        generator = GeneratorTest()
        conf = ConfigurationData()
        lm = LM("lm0", 0, "TestLM", "scmi", None, None, None, None, False)
        lm.get_msel(0)
        conf.add_lm(lm)

        agent = ScmiAgent("agent0", lm, "Agent0", False)
        lm.add_agent(agent)

        mailbox = MailboxMu(1, None, FormatedInt(0x12345), None)
        agent.add_mailbox(mailbox)

        smt_ch = SmtChannel(0, None)
        smt_ch.set_mailbox(mailbox)

        scmi_ch = ScmiChannel(agent, "a2p", None, None, None)
        scmi_ch.set_xport_channel(smt_ch)
        agent.add_channel(scmi_ch)

        content = _generate_and_read(conf, generator, directory)

        assert "SM_TEST_CHN0_CONFIG" in content

    def test_generate_with_smt_channel_mu_mailbox_with_test_uses_test_value(self, tmp_path: Path) -> None:
        """Test SmtChannel with MailboxMu(test=5) sets mailbox_counter to that value."""
        test_utils.set_up()
        directory = tmp_path
        generator = GeneratorTest()
        conf = ConfigurationData()
        lm = LM("lm0", 0, "TestLM", "scmi", None, None, None, None, False)
        lm.get_msel(0)
        conf.add_lm(lm)

        agent = ScmiAgent("agent0", lm, "Agent0", False)
        lm.add_agent(agent)

        mailbox = MailboxMu(1, 5, None, None)
        agent.add_mailbox(mailbox)

        smt_ch = SmtChannel(0, None)
        smt_ch.set_mailbox(mailbox)

        scmi_ch = ScmiChannel(agent, "a2p", None, None, None)
        scmi_ch.set_xport_channel(smt_ch)
        agent.add_channel(scmi_ch)

        content = _generate_and_read(conf, generator, directory)

        assert "SM_TEST_CHN0_CONFIG" in content
        assert "5U" in content  # mbInst = 5

    def test_generate_with_scmi_lm_dup_agent_skips_dup_in_test_collection(self, tmp_path: Path) -> None:
        """Test that a dup agent is skipped when collecting test resources (line 93)."""
        test_utils.set_up()
        directory = tmp_path
        generator = GeneratorTest()
        conf = ConfigurationData()
        lm = LM("lm0", 0, "TestLM", "scmi", None, None, None, None, False)
        lm.get_msel(0)
        conf.add_lm(lm)

        agent_src = ScmiAgent("agent0", lm, "Agent0", False)
        lm.add_agent(agent_src)

        agent_dup = ScmiAgent("agent1", lm, "Agent1", False)
        agent_dup.duplicate(agent_src, 0)
        lm.add_agent(agent_dup)

        content = _generate_and_read(conf, generator, directory)

        assert "SM_SCMI_NUM_TEST  0U" in content

    def test_get_all_tests_with_test_start_stop_logs_error_when_no_a2p_channel(self, caplog: pytest.LogCaptureFixture, tmp_path: Path) -> None:
        """Test _get_all_tests logs error when test resource exists but no a2p channel set."""
        test_utils.set_up()
        directory = tmp_path
        generator = GeneratorTest()
        conf = ConfigurationData()
        lm = LM("lm0", 0, "TestLM", "scmi", None, None, None, None, False)
        msel = lm.get_msel(0)
        conf.add_lm(lm)

        mock_res = Mock(spec=AtomicResource)
        mock_res.get_name.return_value = "CPU_A55_0"
        msel.add_start_stop(True, True, mock_res, "1")

        with caplog.at_level(logging.ERROR):
            generator.generate(conf, str(directory))

        assert "is ignored" in caplog.text

    def test_get_all_tests_msel_start_stop_with_a2p_set_builds_struct(self, tmp_path: Path) -> None:
        """Test lines 77-86: start_stop test resource produces a test struct when a2p is set."""
        test_utils.set_up()
        directory = tmp_path
        generator = GeneratorTest()
        conf = ConfigurationData()

        # LM0: has an a2p channel, no test start_stops
        lm0 = LM("lm0", 0, "LM0", "scmi", None, None, None, None, False)
        lm0.get_msel(0)
        conf.add_lm(lm0)
        agent0 = ScmiAgent("agent0", lm0, "Agent0", False)
        lm0.add_agent(agent0)
        scmi_ch0 = ScmiChannel(agent0, "a2p", None, None, None)
        agent0.add_channel(scmi_ch0)

        # LM1: has msel with test_start_stop, a2p already set from LM0 processing
        lm1 = LM("lm1", 1, "LM1", "scmi", None, None, None, None, False)
        msel1 = lm1.get_msel(0)
        conf.add_lm(lm1)

        mock_res = Mock(spec=AtomicResource)
        mock_res.get_name.return_value = "CPU_A55_0"
        msel1.add_start_stop(True, True, mock_res, "1")

        content = _generate_and_read(conf, generator, directory)

        assert "SM_SCMI_NUM_TEST" in content
        assert "SM_SCMI_TEST_CONFIG_DATA" in content

    def test_get_all_tests_agent_resource_with_no_a2p_logs_error(self, caplog: pytest.LogCaptureFixture, tmp_path: Path) -> None:
        """Test lines 103-107: agent resource test flag with no a2p logs error and returns []."""

        test_utils.set_up()
        directory = tmp_path
        generator = GeneratorTest()
        conf = ConfigurationData()
        lm = LM("lm0", 0, "TestLM", "scmi", None, None, None, None, False)
        lm.get_msel(0)
        conf.add_lm(lm)

        agent = ScmiAgent("agent0", lm, "Agent0", False)
        lm.add_agent(agent)

        # Inject an AssignedResource for a CPU ApiResource with test=True
        api_res = ApiResource({"name": "CPU_A55_0", "type": "api", "api": "cpu", "cat": "DEV"})
        assr = AssignedResource(agent, api_res)
        assr.set_params({"test": True})
        agent._resources.append(assr)  # type: ignore[attr-defined]

        with caplog.at_level(logging.ERROR):
            generator.generate(conf, str(directory))

        assert "no SCMI A2P protocol channel" in caplog.text
