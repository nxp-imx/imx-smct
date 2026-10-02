#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause

"""Unit tests for ConfigurationData"""

import json
import logging
from typing import Any, Dict
from unittest.mock import patch

import pytest

from smct.configuration.confdata import ConfigurationData
from smct.exceptions.cfg_tool_exception import CfgToolException
from smct.owners.owner_agent import ScmiAgent
from smct.owners.owner_lm import LM
from smct.product_info import ProductInfo
from tests import test_utils


@pytest.fixture(name="minimal_config_json")
def _minimal_config_json() -> Dict[str, Any]:
    """Return a minimal valid user_configuration.json structure."""
    return {
        "SMCT_version": list(ProductInfo.get_smct_version()),
        "SM_FW_compatibility_version": ProductInfo.get_sm_fw_compatible_version(),
        "Config": {
            "name": "test",
            "doxygen_name": "test",
            "description": "test",
            "device": "MIMX95",
            "board": "mcimx95evk",
            "build_tool": "gcc",
            "board_configs": [],
            "board_configs_custom": [],
            "mak_variables": [],
            "common_defines": [],
        },
        "LMs": [],
        "DOMs": [],
    }


def test_no_warning_logged_when_versions_match(tmp_path: Any, minimal_config_json: Dict[str, Any], caplog: pytest.LogCaptureFixture) -> None:
    """No warning message when JSON version matches current tool version."""
    file_path = tmp_path / "user_configuration.json"
    file_path.write_text(json.dumps(minimal_config_json), encoding="utf-8")

    conf = ConfigurationData()
    with caplog.at_level(logging.WARNING), patch("smct.configuration.confdata.validate_json"), patch("smct.configuration.confdata.ResourceParser"):
        conf.load_configuration(str(tmp_path))
    assert not any("Configuration was created with SMCT version" in record.message for record in caplog.records)


def test_warning_logged_when_versions_mismatch(tmp_path: Any, minimal_config_json: Dict[str, Any], caplog: pytest.LogCaptureFixture) -> None:
    """Warning logged when JSON version differs from current tool version."""
    minimal_config_json["SMCT_version"] = [1, 0, 0]
    file_path = tmp_path / "user_configuration.json"
    file_path.write_text(json.dumps(minimal_config_json), encoding="utf-8")

    conf = ConfigurationData()
    with caplog.at_level(logging.WARNING), patch("smct.configuration.confdata.validate_json"), patch("smct.configuration.confdata.ResourceParser"):
        conf.load_configuration(str(tmp_path))
    assert any("Configuration was created with SMCT version" in record.message for record in caplog.records)


def test_get_agent_seenv_id_zero_based() -> None:
    """Test that get_agent_seenv_id() returns a zero-based index for S-EENV agents."""
    # Arrange
    test_utils.set_up()
    conf = ConfigurationData()

    seenv_lm = LM("seenv_lm_id", 1, "SeenvLM", "scmi", None, "seenv", None, None, True)
    agent0 = ScmiAgent("agent0_id", seenv_lm, "Agent0", True)
    agent1 = ScmiAgent("agent1_id", seenv_lm, "Agent1", True)
    seenv_lm.add_agent(agent0)
    seenv_lm.add_agent(agent1)
    conf.add_lm(seenv_lm)

    # Assert - first agent is index 0, second is index 1 (zero-based)
    assert conf.get_agent_seenv_id(agent0) == 0
    assert conf.get_agent_seenv_id(agent1) == 1


def test_get_agent_seenv_id_is_global_across_multiple_seenv_lms() -> None:
    """SEENV agent IDs stay global and zero-based across multiple SEENV LMs."""
    # Arrange
    test_utils.set_up()
    conf = ConfigurationData()

    _first_seenv_lm, first_agent0, first_agent1, _second_seenv_lm, second_agent0 = test_utils.build_two_seenv_lms(conf)

    # Assert - IDs are global across the flattened SEENV-agent list
    assert conf.get_all_seenv_agents() == [first_agent0, first_agent1, second_agent0]
    assert conf.get_agent_seenv_id(first_agent0) == 0
    assert conf.get_agent_seenv_id(first_agent1) == 1
    assert conf.get_agent_seenv_id(second_agent0) == 2


def test_add_dom_raises_on_did_above_max() -> None:
    """add_dom() raises CfgToolException when did is above the maximum valid index."""
    test_utils.set_up()
    conf = ConfigurationData()
    lm = LM("lm_id", 16, "TestLM", None, None, None, None, None, False)
    with pytest.raises(CfgToolException, match="did=16"):
        conf.add_dom(lm)


def test_add_dom_raises_on_negative_did() -> None:
    """add_dom() raises CfgToolException instead of silently corrupting the last domain slot."""
    test_utils.set_up()
    conf = ConfigurationData()
    lm = LM("lm_id", -1, "TestLM", None, None, None, None, None, False)
    with pytest.raises(CfgToolException, match="did=-1"):
        conf.add_dom(lm)
