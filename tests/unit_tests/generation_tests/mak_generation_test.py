#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause

"""Unit tests for Makefile generation"""

import os.path
from pathlib import Path

from smct.configuration.confdata import ConfigurationData
from smct.generation.gen_mak import GeneratorMakeFile
from smct.owners.owner_agent import MailboxLoopback, MailboxMu, ScmiAgent, ScmiChannel
from smct.owners.owner_lm import LM
from tests import test_utils


def test_board_device_build(tmp_path: Path) -> None:
    """Tests that config.mak will contain board define, and device and build makefile includes"""
    directory = tmp_path
    generator = GeneratorMakeFile()
    conf = ConfigurationData()
    test_utils.set_up()
    build = "lorem"
    device = "ipsum"
    board = "dolor"
    conf.set_build_tool(build)
    conf.set_device(device, board)
    # Test
    generator.generate(conf, str(directory))
    file_name = os.path.join(str(directory), "config.mak")
    content = ""
    with open(file_name, "r", encoding="utf-8") as file:
        content = file.read()
    assert f"BOARD ?= {board}" in content
    assert f"include ./devices/{device}/sm/Makefile" in content
    assert f"include ./sm/makefiles/{build}.mak" in content
    # No loopback or MU mailbox were added to the config so there should not be any include for them
    assert "include ./sm/rpc/mb_mu/Makefile" not in content
    assert "include ./sm/rpc/mb_loopback/Makefile" not in content


def test_mu(tmp_path: Path) -> None:
    """Tests that config.mak will contain only mu makefile include"""
    directory = tmp_path
    generator = GeneratorMakeFile()
    conf = ConfigurationData()
    test_utils.set_up()
    lm = LM("id", 0, "name", None, None, None, None, None, True)
    conf.add_lm(lm)
    agent = ScmiAgent("agent0", lm, "agent0", True, lm.get_safe(), lm.get_did())
    lm.add_agent(agent)
    mailbox = MailboxMu(7, 1, None, None)
    agent.add_mailbox(mailbox)
    channel = ScmiChannel(agent, "a2p", None, None, None)
    mailbox.set_doorbell_channel(42, channel)
    agent.add_channel(channel)
    # Test
    generator.generate(conf, str(directory))
    file_name = os.path.join(str(directory), "config.mak")
    content = ""
    with open(file_name, "r", encoding="utf-8") as file:
        content = file.read()

    assert "include ./sm/rpc/mb_mu/Makefile" in content
    assert "include ./sm/rpc/mb_loopback/Makefile" not in content


def test_loopback(tmp_path: Path) -> None:
    """Tests that config.mak will contain only loopback makefile include"""
    directory = tmp_path
    generator = GeneratorMakeFile()
    conf = ConfigurationData()
    test_utils.set_up()
    lm = LM("id", 0, "name", None, None, None, None, None, True)
    conf.add_lm(lm)
    agent = ScmiAgent("agent0", lm, "agent0", True, lm.get_safe(), lm.get_did())
    lm.add_agent(agent)
    mailbox = MailboxLoopback(None, None)
    agent.add_mailbox(mailbox)
    channel = ScmiChannel(agent, "a2p", None, None, None)
    mailbox.set_doorbell_channel(42, channel)
    agent.add_channel(channel)
    # Test
    generator.generate(conf, str(directory))
    file_name = os.path.join(str(directory), "config.mak")
    content = ""
    with open(file_name, "r", encoding="utf-8") as file:
        content = file.read()

    assert "include ./sm/rpc/mb_loopback/Makefile" in content
    assert "include ./sm/rpc/mb_mu/Makefile" not in content


def test_mu_loopback(tmp_path: Path) -> None:
    """Tests that config.mak will contain both mu and loopback makefile includes"""
    directory = tmp_path
    generator = GeneratorMakeFile()
    conf = ConfigurationData()
    test_utils.set_up()
    lm = LM("id", 0, "name", None, None, None, None, None, True)
    conf.add_lm(lm)
    agent1 = ScmiAgent("agent1", lm, "agent1", True, lm.get_safe(), lm.get_did())
    lm.add_agent(agent1)
    agent2 = ScmiAgent("agent2", lm, "agent2", True, lm.get_safe(), lm.get_did())
    lm.add_agent(agent2)
    channel1 = ScmiChannel(agent1, "a2p", None, None, None)
    channel2 = ScmiChannel(agent2, "a2p", None, None, None)
    mailbox1 = MailboxLoopback(None, None)
    mailbox1.set_doorbell_channel(42, channel1)
    mailbox2 = MailboxMu(7, 1, None, None)
    mailbox2.set_doorbell_channel(42, channel2)
    agent1.add_mailbox(mailbox1)
    agent2.add_mailbox(mailbox2)
    agent1.add_channel(channel1)
    agent2.add_channel(channel2)
    # Test
    generator.generate(conf, str(directory))
    file_name = os.path.join(str(directory), "config.mak")
    content = ""
    with open(file_name, "r", encoding="utf-8") as file:
        content = file.read()

    assert "include ./sm/rpc/mb_loopback/Makefile" in content
    assert "include ./sm/rpc/mb_mu/Makefile" in content
