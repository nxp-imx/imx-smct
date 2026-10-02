#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
# pylint: disable=missing-module-docstring

import os
from pathlib import Path

import pytest

from smct.configuration.confdata import ConfigurationData
from smct.generation.gen_mb_loopback import GeneratorMailboxLoopback
from smct.owners.owner_agent import MailboxLoopback
from tests import test_utils


def _generate_and_read(conf: ConfigurationData, generator: GeneratorMailboxLoopback, directory: Path) -> str:
    generator.generate(conf, str(directory))
    file_name = os.path.join(str(directory), "config_mb_loopback.h")
    return test_utils.read_generated_file(file_name)


def _assert_loopback_header_and_count(content: str, expected_count: str = "1U") -> None:
    """Assert standard loopback header includes and instance count."""
    assert '#include "config_user.h"' in content
    assert '#include "mb_loopback_config.h"' in content
    assert f"#define SM_NUM_MB_LOOPBACK  {expected_count}\n" in content


def test_mb_mailbox_structures_empty(tmp_path: Path) -> None:
    """Test mailbox loopback generation with empty configuration data"""
    directory = tmp_path
    GeneratorMailboxLoopback().generate(ConfigurationData(), str(directory))
    assert not os.path.exists(os.path.join(str(directory), "config_mb_mu.h"))


def test_mb_loopback_structures_single(tmp_path: Path) -> None:
    """Test mailbox loopback generation with a single loopback mailbox configuration"""
    # Arrange
    directory = tmp_path
    generator = GeneratorMailboxLoopback()
    conf, _lm, agent = test_utils.build_conf_with_lm_and_agent()
    agent.add_mailbox(MailboxLoopback(None, None))

    # Act
    content = _generate_and_read(conf, generator, directory)

    # Assert
    _assert_loopback_header_and_count(content)
    assert "#define SM_MB_LOOPBACK_CONFIG_DATA \\\n    SM_MB_LOOPBACK0_CONFIG\n\n" in content
    assert "#define SM_MB_LOOPBACK0_CONFIG \\\n    { \\\n    }\n" in content


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
def test_mb_loopback_structures_single_with_params(given_priority: str, expected_define: str, tmp_path: Path) -> None:
    """Test mailbox loopback with different priority configurations"""
    # Arrange
    directory = tmp_path
    generator = GeneratorMailboxLoopback()
    conf, _lm, agent = test_utils.build_conf_with_lm_and_agent()
    agent.add_mailbox(MailboxLoopback(test=1, priority=given_priority))

    # Act
    content = _generate_and_read(conf, generator, directory)

    # Assert
    _assert_loopback_header_and_count(content)
    assert "#define SM_MB_LOOPBACK_CONFIG_DATA \\\n    SM_MB_LOOPBACK0_CONFIG\n\n" in content
    assert f"#define SM_MB_LOOPBACK0_CONFIG \\\n    {{ \\\n        .priority = {expected_define}, \\\n    }}\n" in content
