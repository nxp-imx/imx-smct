#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
# pylint: disable=missing-module-docstring

import os
from pathlib import Path

from smct.configuration.confdata import ConfigurationData
from smct.generation.gen_mb_mu import GeneratorMBMU
from smct.owners.owner_agent import MailboxMu, ScmiAgent, ScmiChannel, SmtChannel
from smct.owners.owner_lm import LM
from tests import test_utils


def _generate_and_read(conf: ConfigurationData, generator: GeneratorMBMU, directory: Path) -> str:
    generator.generate(conf, str(directory))
    file_name = os.path.join(str(directory), "config_mb_mu.h")
    return test_utils.read_generated_file(file_name)


def test_mb_mu_structures_empty(tmp_path: Path) -> None:
    """Test MB MU generation with empty configuration data"""
    directory = tmp_path
    GeneratorMBMU().generate(ConfigurationData(), str(directory))
    assert not os.path.exists(os.path.join(str(directory), "config_mb_mu.h"))


def test_mb_mu_structures_single(tmp_path: Path) -> None:
    """Test MB MU generation with a single MU mailbox configuration"""
    # Arrange
    directory = tmp_path
    generator = GeneratorMBMU()
    conf, _lm, agent = test_utils.build_conf_with_lm_and_agent()
    mu_num = 0
    agent.add_mailbox(MailboxMu(mu_num, None, None, None))

    # Act
    content = _generate_and_read(conf, generator, directory)

    # Assert — header inclusions
    assert '#include "config_user.h"' in content
    assert '#include "mb_mu_config.h"' in content
    assert "#define SM_NUM_MB_MU  1U\n" in content
    # Assert — array and instance defines
    assert f"#define SM_MB_MU_CONFIG_DATA \\\n    SM_MB_MU{mu_num}_CONFIG\n\n" in content
    assert f"#define SM_MB_MU0_CONFIG \\\n    {{ \\\n        .mu = {mu_num}U, \\\n    }}\n\n" in content


def test_mb_mu_structures_multiple(tmp_path: Path) -> None:
    """Test MB MU generation with multiple MU mailboxes and different configurations"""
    # Arrange
    directory = tmp_path
    generator = GeneratorMBMU()
    conf = ConfigurationData()
    test_utils.set_up()

    # Create LM2 (AP)
    lm = LM("LM2", 2, "AP", None, None, None, None, None, True)
    conf.add_lm(lm)

    # Create AP-S agent with MU1
    agent_s = ScmiAgent("SCMI_AGENT0", lm, "AP-S", True)
    lm.add_agent(agent_s)
    mb1 = MailboxMu(1, None, None, None)
    agent_s.add_mailbox(mb1)

    # Create SCMI and SMT channels for AP-S agent
    scmi_channel_1 = ScmiChannel(agent_s, "a2p", None, None, "1")
    scmi_channel_2 = ScmiChannel(agent_s, "p2a", None, None, "1")
    smt_channel_1 = SmtChannel(0, None)  # doorbell 0, channel instance 0
    smt_channel_2 = SmtChannel(1, None)  # doorbell 1, channel instance 1
    smt_channel_1.set_mailbox(mb1)
    smt_channel_2.set_mailbox(mb1)
    scmi_channel_1.set_xport_channel(smt_channel_1)
    scmi_channel_2.set_xport_channel(smt_channel_2)
    smt_channel_1.set_rpc_channel(scmi_channel_1)
    smt_channel_2.set_rpc_channel(scmi_channel_2)

    # Add channels to agent
    agent_s.add_channel(scmi_channel_1)
    agent_s.add_channel(scmi_channel_2)

    # Create AP-NS agent with MU3
    agent_ns = ScmiAgent("SCMI_AGENT1", lm, "AP-NS", False)
    lm.add_agent(agent_ns)
    mb3 = MailboxMu(3, None, None, None)
    agent_ns.add_mailbox(mb3)

    # Create SCMI and SMT channels for AP-NS agent
    scmi_channel_3 = ScmiChannel(agent_ns, "a2p", None, None, "1")
    scmi_channel_4 = ScmiChannel(agent_ns, "p2a", None, None, "1")
    smt_channel_3 = SmtChannel(0, None)  # doorbell 0, channel instance 2
    smt_channel_4 = SmtChannel(1, None)  # doorbell 1, channel instance 3
    smt_channel_3.set_mailbox(mb3)
    smt_channel_4.set_mailbox(mb3)
    scmi_channel_3.set_xport_channel(smt_channel_3)
    scmi_channel_4.set_xport_channel(smt_channel_4)
    smt_channel_3.set_rpc_channel(scmi_channel_3)
    smt_channel_4.set_rpc_channel(scmi_channel_4)

    # Add channels to agent
    agent_ns.add_channel(scmi_channel_3)
    agent_ns.add_channel(scmi_channel_4)

    # Act
    content = _generate_and_read(conf, generator, directory)

    # Assert - Expected configuration for MB_MU1
    expected_mb1_config = (
        "#define SM_MB_MU1_CONFIG \\\n"
        "    { \\\n"
        "        .mu = 1U, \\\n"
        "        .xportType[0] = SM_XPORT_SMT, \\\n"
        "        .xportChannel[0] = 0U, \\\n"
        "        .xportType[1] = SM_XPORT_SMT, \\\n"
        "        .xportChannel[1] = 1U, \\\n"
        "    }\n"
    )
    # Expected configuration for MB_MU3
    expected_mb3_config = (
        "#define SM_MB_MU3_CONFIG \\\n"
        "    { \\\n"
        "        .mu = 3U, \\\n"
        "        .xportType[0] = SM_XPORT_SMT, \\\n"
        "        .xportChannel[0] = 2U, \\\n"
        "        .xportType[1] = SM_XPORT_SMT, \\\n"
        "        .xportChannel[1] = 3U, \\\n"
        "    }\n"
    )
    expected_mb_count = "#define SM_NUM_MB_MU  2U\n"
    expected_config_array = "#define SM_MB_MU_CONFIG_DATA \\\n" + "    SM_MB_MU1_CONFIG, \\\n" + "    SM_MB_MU3_CONFIG\n"

    assert expected_mb1_config in content
    assert expected_mb3_config in content
    assert expected_mb_count in content
    assert expected_config_array in content
    assert "LM2 MB_MU Config (AP)" in content
    assert "Config for MB_MU1 instance (uses MU1, used by AP-S)" in content
    assert "Config for MB_MU3 instance (uses MU3, used by AP-NS)" in content
