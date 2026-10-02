#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause

"""Unit tests for GeneratorSCMI – focused on seenvId emission in config_scmi.h."""

import os
from pathlib import Path

from smct.configuration.confdata import ConfigurationData
from smct.generation.gen_scmi import GeneratorSCMI
from smct.owners.owner_agent import ScmiAgent
from smct.owners.owner_lm import LM
from tests import test_utils


def _generate_and_read(conf: ConfigurationData, generator: GeneratorSCMI, directory: Path) -> str:
    generator.generate(conf, str(directory))
    file_name = os.path.join(str(directory), "config_scmi.h")
    with open(file_name, "r", encoding="utf-8") as file:
        content = file.read()
    return content


def test_seenv_agent_emits_zero_based_seenv_id(tmp_path: Path) -> None:
    """S-EENV LM controls seenvId emission, while non-S-EENV LM omits it entirely."""
    # Arrange
    test_utils.set_up()
    directory = tmp_path
    generator = GeneratorSCMI()
    conf = ConfigurationData()

    # Seenv LM with one agent whose own safe field stays at the default non-SEENV value
    seenv_lm = LM("seenv_lm_id", 1, "SeenvLM", "scmi", None, "seenv", None, None, True)
    seenv_agent = ScmiAgent("seenv_agent_id", seenv_lm, "SeenvAgent", True)
    seenv_lm.add_agent(seenv_agent)

    # Non-seenv LM with one agent
    normal_lm = LM("normal_lm_id", 2, "NormalLM", "scmi", None, None, None, None, True)
    normal_agent = ScmiAgent("normal_agent_id", normal_lm, "NormalAgent", True)
    normal_lm.add_agent(normal_agent)

    conf.add_lm(seenv_lm)
    conf.add_lm(normal_lm)

    # Act
    content = _generate_and_read(conf, generator, directory)

    # Assert – SEENV LM still emits seenvId based on parent LM, not agent.safe
    assert ".seenvId = 0U" in content
    assert content.count(".seenvId") == 1

    # Assert – non-SEENV LM/agent emits no seenvId sentinel or extra field
    assert ".seenvId = (uint32_t)-1" not in content


def test_multiple_seenv_agents_emit_global_consecutive_seenv_ids(tmp_path: Path) -> None:
    """SEENV agents across LMs emit global zero-based seenvId values only for SEENV LMs."""
    # Arrange
    test_utils.set_up()
    directory = tmp_path
    generator = GeneratorSCMI()
    conf = ConfigurationData()

    _first_seenv_lm, _first_agent0, _first_agent1, _second_seenv_lm, _second_agent0 = test_utils.build_two_seenv_lms(conf)

    normal_lm = LM("normal_lm_id", 3, "NormalLM", "scmi", None, None, None, None, True)
    normal_agent = ScmiAgent("normal_agent_id", normal_lm, "NormalAgent", True)
    normal_lm.add_agent(normal_agent)

    conf.add_lm(normal_lm)

    # Act
    content = _generate_and_read(conf, generator, directory)

    # Assert - SEENV IDs are global and consecutive across all SEENV LMs
    assert ".seenvId = 0U" in content
    assert ".seenvId = 1U" in content
    assert ".seenvId = 2U" in content
    assert content.count(".seenvId") == 3

    # Assert - only agents under SEENV LMs emit seenvId fields
    assert ".seenvId = (uint32_t)-1" not in content
