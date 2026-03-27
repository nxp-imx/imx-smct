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
from smct.generation.gen_mb_loopback import GeneratorMailboxLoopback
from smct.owners.owner_agent import MailboxLoopback, ScmiAgent
from smct.owners.owner_lm import LM
from tests import test_utils


def _generate_and_read(conf: ConfigurationData, generator: GeneratorMailboxLoopback, directory: TemporaryDirectory) -> str:
    generator.generate(conf, directory.name)
    file_name = os.path.join(directory.name, "config_mb_loopback.h")
    content = ""
    with open(file_name, "r") as file:
        content = file.read()
    return content


def test_mb_mailbox_structures_empty() -> None:
    """Test mailbox loopback generation with empty configuration data"""
    # Arrange
    directory = TemporaryDirectory()
    generator = GeneratorMailboxLoopback()
    conf = ConfigurationData()

    # Act
    generator.generate(conf, directory.name)
    file_name = os.path.join(directory.name, "config_mb_mu.h")

    # Assert
    assert not os.path.exists(file_name)


def test_mb_mu_structures_single() -> None:
    """Test mailbox loopback generation with a single loopback mailbox configuration"""
    # Arrange
    directory = TemporaryDirectory()
    generator = GeneratorMailboxLoopback()
    conf = ConfigurationData()
    test_utils.set_up()

    lm = LM("id", 0, "name", None, None, None, None, None, True)
    conf.add_lm(lm)
    agent = ScmiAgent("id", lm, "name", True)
    lm.add_agent(agent)
    mb = MailboxLoopback(None, None)
    agent.add_mailbox(mb)

    # Act
    content = _generate_and_read(conf, generator, directory)

    # Assert
    config_data_array = "#define SM_MB_LOOPBACK_CONFIG_DATA \\\n" + "    SM_MB_LOOPBACK0_CONFIG\n" + "\n"
    config_instance = "#define SM_MB_LOOPBACK0_CONFIG \\\n" + "    { \\\n" + "    }\n"
    config_mb_count = "#define SM_NUM_MB_LOOPBACK  1U\n"
    assert '#include "config_user.h"' in content
    assert '#include "mb_loopback_config.h"' in content
    assert config_data_array in content
    assert config_instance in content
    assert config_mb_count in content


@pytest.mark.parametrize(
    "given_priority,expected_define",
    [
        ("critical", "IRQ_PRIO_NOPREEMPT_CRITICAL"),
        ("very_high", "IRQ_PRIO_NOPREEMPT_VERY_HIGH"),
        ("high", "IRQ_PRIO_NOPREEMPT_HIGH"),
        ("above_normal", "IRQ_PRIO_NOPREEMPT_ABOVE_NORMAL"),
        ("normal", "IRQ_PRIO_NOPREEMPT_NORMAL"),
        ("below_normal", "IRQ_PRIO_NOPREEMPT_BELOW_NORMAL"),
        ("low", "IRQ_PRIO_NOPREEMPT_LOW"),
        ("very_low", "IRQ_PRIO_NOPREEMPT_VERY_LOW"),
    ],
)
def test_mb_loopback_structures_single_with_params(given_priority: str, expected_define: str) -> None:
    """Test mailbox loopback with different priority configurations"""
    # Arrange
    directory = TemporaryDirectory()
    generator = GeneratorMailboxLoopback()
    conf = ConfigurationData()
    test_utils.set_up()

    lm = LM("id", 0, "name", None, None, None, None, None, True)
    conf.add_lm(lm)
    agent = ScmiAgent("id", lm, "name", True)
    lm.add_agent(agent)

    # Create loopback mailbox with test and priority parameters
    mb = MailboxLoopback(test=1, priority=given_priority)
    agent.add_mailbox(mb)

    # Act
    content = _generate_and_read(conf, generator, directory)

    # Assert
    config_data_array = "#define SM_MB_LOOPBACK_CONFIG_DATA \\\n" + "    SM_MB_LOOPBACK0_CONFIG\n" + "\n"
    config_instance = "#define SM_MB_LOOPBACK0_CONFIG \\\n" + "    { \\\n" + f"        .priority = {expected_define}, \\\n" + "    }\n"
    config_mb_count = "#define SM_NUM_MB_LOOPBACK  1U\n"

    assert config_data_array in content
    assert config_instance in content
    assert config_mb_count in content
