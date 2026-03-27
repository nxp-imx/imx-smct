#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause

import os
from tempfile import TemporaryDirectory

import pytest

from smct.configuration.confdata import ConfigurationData
from smct.generation.gen_smt import GeneratorSMT
from smct.owners.owner_agent import MailboxLoopback, MailboxMu, ScmiAgent, ScmiChannel, SmtChannel
from smct.owners.owner_lm import LM
from tests import test_utils


def _generate_and_read(conf: ConfigurationData, generator: GeneratorSMT, directory: TemporaryDirectory) -> str:
    generator.generate(conf, directory.name)
    file_name = os.path.join(directory.name, "config_smt.h")
    content = ""
    with open(file_name, "r") as file:
        content = file.read()
    return content


def test_smt_structures_empty() -> None:
    """Test SMT generation with empty configuration data"""
    # Arrange
    directory = TemporaryDirectory()
    generator = GeneratorSMT()
    conf = ConfigurationData()

    # Act
    content = _generate_and_read(conf, generator, directory)
    file_name = os.path.join(directory.name, "config_smt.h")

    # Assert
    assert os.path.exists(file_name)
    assert '#include "config_user.h"' in content
    assert '#include "rpc_smt_config.h"' in content
    assert "#define SM_NUM_SMT_CHN  0U" in content


def test_smt_structures_single() -> None:
    """Test SMT generation with a single SMT channel configuration"""
    # Arrange
    directory = TemporaryDirectory()
    generator = GeneratorSMT()
    conf = ConfigurationData()
    test_utils.set_up()

    lm = LM("id", 0, "name", None, None, None, None, None, True)
    agent = ScmiAgent("id", lm, "name", True)
    scmi_channel = ScmiChannel(agent, "a2p", None, None, None)
    smt_channel = SmtChannel(0, "crc32")
    mailbox = MailboxLoopback(None, None)

    scmi_channel.set_xport_channel(smt_channel)
    smt_channel.set_rpc_channel(scmi_channel)
    smt_channel.set_mailbox(mailbox)
    agent.add_channel(scmi_channel)
    agent.add_mailbox(mailbox)
    lm.add_agent(agent)
    conf.add_lm(lm)

    # Act
    content = _generate_and_read(conf, generator, directory)

    # Assert
    config_instance = (
        "#define SM_SMT_CHN0_CONFIG \\\n"
        + "    { \\\n"
        + "        .rpcType = SM_RPC_SCMI, \\\n"
        + "        .rpcChannel = 0U, \\\n"
        + "        .mbType = SM_MB_LOOPBACK, \\\n"
        + "        .mbInst = 0U, \\\n"
        + "        .mbDoorbell = 0U, \\\n"
        + "        .crc = SM_SMT_CRC_CRC32, \\\n"
        + "    }\n"
    )

    config_data_array = "#define SM_SMT_CHN_CONFIG_DATA \\\n" + "    SM_SMT_CHN0_CONFIG\n"

    assert config_data_array in content
    assert config_instance in content


def test_smt_structures_multiple() -> None:
    """Test SMT generation with multiple SMT channels and different configurations"""
    # Arrange
    directory = TemporaryDirectory()
    generator = GeneratorSMT()
    conf = ConfigurationData()
    test_utils.set_up()

    # First LM with first agent
    lm1 = LM("id1", 0, "name1", None, None, None, None, None, True)
    agent1 = ScmiAgent("id1", lm1, "name1", True)
    scmi_channel1 = ScmiChannel(agent1, "a2p", None, None, None)
    smt_channel1 = SmtChannel(0, "crc32")
    mailbox1 = MailboxLoopback(None, None)

    scmi_channel1.set_xport_channel(smt_channel1)
    smt_channel1.set_rpc_channel(scmi_channel1)
    smt_channel1.set_mailbox(mailbox1)
    agent1.add_channel(scmi_channel1)
    agent1.add_mailbox(mailbox1)
    lm1.add_agent(agent1)

    # Second LM with second agent
    lm2 = LM("id2", 1, "name2", None, None, None, None, None, True)
    agent2 = ScmiAgent("id2", lm2, "name2", True)
    scmi_channel2 = ScmiChannel(agent2, "a2p", None, None, None)
    smt_channel2 = SmtChannel(1, "xor")
    mailbox2 = MailboxMu(0, None, None, None)

    scmi_channel2.set_xport_channel(smt_channel2)
    smt_channel2.set_rpc_channel(scmi_channel2)
    smt_channel2.set_mailbox(mailbox2)
    agent2.add_channel(scmi_channel2)
    agent2.add_mailbox(mailbox2)
    lm2.add_agent(agent2)

    # Third LM with third agent
    lm3 = LM("id3", 2, "name3", None, None, None, None, None, True)
    agent3 = ScmiAgent("id3", lm3, "name3", True)
    scmi_channel3 = ScmiChannel(agent3, "a2p", None, None, None)
    smt_channel3 = SmtChannel(2, "none")

    scmi_channel3.set_xport_channel(smt_channel3)
    smt_channel3.set_rpc_channel(scmi_channel3)
    agent3.add_channel(scmi_channel3)
    lm3.add_agent(agent3)

    conf.add_lm(lm1)
    conf.add_lm(lm2)
    conf.add_lm(lm3)

    # Act
    content = _generate_and_read(conf, generator, directory)

    # Assert
    config_instance1 = (
        "#define SM_SMT_CHN0_CONFIG \\\n"
        + "    { \\\n"
        + "        .rpcType = SM_RPC_SCMI, \\\n"
        + "        .rpcChannel = 0U, \\\n"
        + "        .mbType = SM_MB_LOOPBACK, \\\n"
        + "        .mbInst = 0U, \\\n"
        + "        .mbDoorbell = 0U, \\\n"
        + "        .crc = SM_SMT_CRC_CRC32, \\\n"
        + "    }\n"
    )

    config_instance2 = (
        "#define SM_SMT_CHN1_CONFIG \\\n"
        + "    { \\\n"
        + "        .rpcType = SM_RPC_SCMI, \\\n"
        + "        .rpcChannel = 1U, \\\n"
        + "        .mbType = SM_MB_MU, \\\n"
        + "        .mbInst = 0U, \\\n"
        + "        .mbDoorbell = 1U, \\\n"
        + "        .crc = SM_SMT_CRC_XOR, \\\n"
        + "    }\n"
    )

    config_instance3 = (
        "#define SM_SMT_CHN2_CONFIG \\\n"
        + "    { \\\n"
        + "        .rpcType = SM_RPC_SCMI, \\\n"
        + "        .rpcChannel = 2U, \\\n"
        + "        .mbDoorbell = 2U, \\\n"
        + "        .crc = SM_SMT_CRC_NONE, \\\n"
        + "    }\n"
    )

    config_data_array = "#define SM_SMT_CHN_CONFIG_DATA \\\n" + "    SM_SMT_CHN0_CONFIG, \\\n" + "    SM_SMT_CHN1_CONFIG, \\\n" + "    SM_SMT_CHN2_CONFIG\n"

    assert config_instance1 in content
    assert config_instance2 in content
    assert config_instance3 in content
    assert config_data_array in content
    assert "#define USES_MB_LOOPBACK" in content
    assert "#define USES_MB_MU" in content
    assert "#define USES_CRC_CRC32" in content
    assert "#define USES_CRC_XOR" in content
    assert "#define USES_CRC_NONE" in content
    assert "#define SM_NUM_SMT_CHN  3U" in content


@pytest.mark.parametrize(
    "crc_type,expected_define",
    [
        ("none", "SM_SMT_CRC_NONE"),
        ("xor", "SM_SMT_CRC_XOR"),
        ("crc32", "SM_SMT_CRC_CRC32"),
        ("j1850", "SM_SMT_CRC_J1850"),
    ],
)
def test_smt_structures_crc_types(crc_type: str, expected_define: str) -> None:
    """Test SMT with different CRC configurations"""
    # Arrange
    directory = TemporaryDirectory()
    generator = GeneratorSMT()
    conf = ConfigurationData()
    test_utils.set_up()

    lm = LM("id", 0, "name", None, None, None, None, None, True)
    agent = ScmiAgent("id", lm, "name", True)
    scmi_channel = ScmiChannel(agent, "a2p", None, None, None)
    smt_channel = SmtChannel(0, crc_type)

    scmi_channel.set_xport_channel(smt_channel)
    smt_channel.set_rpc_channel(scmi_channel)
    agent.add_channel(scmi_channel)
    lm.add_agent(agent)
    conf.add_lm(lm)

    # Act
    content = _generate_and_read(conf, generator, directory)

    # Assert
    config_instance = (
        "#define SM_SMT_CHN0_CONFIG \\\n"
        + "    { \\\n"
        + "        .rpcType = SM_RPC_SCMI, \\\n"
        + "        .rpcChannel = 0U, \\\n"
        + "        .mbDoorbell = 0U, \\\n"
        + f"        .crc = {expected_define}, \\\n"
        + "    }\n"
    )
    crc_define = f"#define USES_CRC_{crc_type.upper()}\n"

    assert config_instance in content
    assert crc_define in content


@pytest.mark.parametrize(
    "mailbox_type,expected_define,mb_type",
    [
        ("mu", "#define USES_MB_MU\n", "SM_MB_MU"),
        ("loopback", "#define USES_MB_LOOPBACK\n", "SM_MB_LOOPBACK"),
        ("none", None, None),
    ],
)
def test_smt_structures_mailbox_types(
    mailbox_type: str,
    expected_define: str,
    mb_type: str,
) -> None:
    """Test SMT with different mailbox configurations"""
    # Arrange
    directory = TemporaryDirectory()
    generator = GeneratorSMT()
    conf = ConfigurationData()
    test_utils.set_up()

    lm = LM("id", 0, "name", None, None, None, None, None, True)
    agent = ScmiAgent("id", lm, "name", True)
    scmi_channel = ScmiChannel(agent, "a2p", None, None, None)
    smt_channel = SmtChannel(0, "crc32")

    if mailbox_type == "mu":
        # Use MailboxMu with different parameters
        mailbox_mu = MailboxMu(1, None, None, None)
        smt_channel.set_mailbox(mailbox_mu)
        agent.add_mailbox(mailbox_mu)

    elif mailbox_type == "loopback":
        # Use MailboxLoopback with different parameters
        mailbox_loopback = MailboxLoopback(None, None)
        smt_channel.set_mailbox(mailbox_loopback)
        agent.add_mailbox(mailbox_loopback)

    scmi_channel.set_xport_channel(smt_channel)
    smt_channel.set_rpc_channel(scmi_channel)
    agent.add_channel(scmi_channel)
    lm.add_agent(agent)
    conf.add_lm(lm)

    # Act
    content = _generate_and_read(conf, generator, directory)

    # Assert
    if mb_type:
        expected_config = (
            "#define SM_SMT_CHN0_CONFIG \\\n"
            + "    { \\\n"
            + "        .rpcType = SM_RPC_SCMI, \\\n"
            + "        .rpcChannel = 0U, \\\n"
            + f"        .mbType = {mb_type}, \\\n"
            + "        .mbInst = 0U, \\\n"
            + "        .mbDoorbell = 0U, \\\n"
            + "        .crc = SM_SMT_CRC_CRC32, \\\n"
            + "    }\n"
        )
    else:
        expected_config = (
            "#define SM_SMT_CHN0_CONFIG \\\n"
            + "    { \\\n"
            + "        .rpcType = SM_RPC_SCMI, \\\n"
            + "        .rpcChannel = 0U, \\\n"
            + "        .mbDoorbell = 0U, \\\n"
            + "        .crc = SM_SMT_CRC_CRC32, \\\n"
            + "    }\n"
        )
    assert expected_config in content

    if expected_define:
        assert expected_define in content
    else:
        assert "#define USES_MB_MU\n" not in content
        assert "#define USES_MB_LOOPBACK\n" not in content
