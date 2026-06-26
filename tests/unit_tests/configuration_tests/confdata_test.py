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
from smct.product_info import ProductInfo


@pytest.fixture
def minimal_config_json() -> Dict[str, Any]:
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
