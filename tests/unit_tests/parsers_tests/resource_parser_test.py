#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Unit tests for smct.parsers.resource_parser resource database parsing."""

# pylint: disable=protected-access

import json
import os
from typing import Iterator
from unittest.mock import mock_open, patch

import pytest

from smct.configuration.configuration_provider import ConfigurationProvider
from smct.model.chip_model_provider import ChipModelProvider
from smct.model.model_trdc import TrdcModel
from smct.parsers.resource_parser import ResourceParser
from smct.resources.resource_database_provider import ResourceDatabaseProvider
from tests import test_utils


@pytest.fixture(autouse=True)
def reset_singletons() -> None:
    """Reset singleton providers and ResourceParser class state."""

    ConfigurationProvider.clear_configuration()
    ResourceDatabaseProvider.clear_database()
    ChipModelProvider.clear_model()
    ResourceParser.soc_directory = None


@pytest.fixture(autouse=True)
def restore_dfmt_registers() -> Iterator[None]:
    """Save and restore TrdcModel DFMT class-level register dicts around each test."""
    with test_utils.restore_dfmt_registers():
        yield


class TestResourceParser:
    """Tests for resource database parser helpers."""

    def test_construction_uses_default_sm_model_directory_when_soc_directory_unset(self) -> None:
        """Default construction points at the repository sm_model directory."""
        with patch("smct.parsers.resource_parser.os.path.exists", return_value=False):
            parser = ResourceParser("MIMX95")

        assert parser._resources_path.endswith("sm_model")

    def test_construction_uses_relative_soc_directory_sm_model_child(self) -> None:
        """Relative soc_directory values are treated as roots containing sm_model."""
        ResourceParser.soc_directory = "custom_root"

        with patch("smct.parsers.resource_parser.os.path.exists", return_value=False):
            parser = ResourceParser("MIMX95")

        assert parser._resources_path == os.path.join("custom_root", "sm_model")

    def test_construction_uses_absolute_soc_directory_directly(self) -> None:
        """Absolute soc_directory values point directly to resource files."""
        absolute_dir = os.path.abspath(os.path.join(os.sep, "absolute", "sm_model"))
        ResourceParser.soc_directory = absolute_dir

        with patch("smct.parsers.resource_parser.os.path.exists", return_value=False):
            parser = ResourceParser("MIMX95")

        assert parser._resources_path == absolute_dir

    def test_construction_loads_soc_json_and_falls_back_to_simu_device(self) -> None:
        """Unknown devices fall back to the simu entry from soc.json."""
        soc_json = {"simu": {"soc_model": "soc_simu.json", "sm_model": "sm_simu.json"}}

        with (
            patch("smct.parsers.resource_parser.os.path.exists", return_value=True),
            patch("builtins.open", mock_open(read_data=json.dumps(soc_json))),
            patch("smct.parsers.resource_parser.json.load", return_value=soc_json),
            patch("smct.parsers.resource_parser.validate_json"),
        ):
            parser = ResourceParser("UNKNOWN")

        assert parser._soc_model == "soc_simu.json"
        assert parser._sm_model == "sm_simu.json"

    def test_parse_dfmt_register_helpers_populate_trdc_model_registers(self) -> None:
        """DFMT helper methods copy bitfield offsets and widths to TrdcModel."""
        parser = ResourceParser.__new__(ResourceParser)

        parser._parse_dfmt0_register([{"name": "DID", "offset": 0, "width": 4}])
        parser._parse_dfmt1_register([{"name": "SID", "offset": 8, "width": 6}])

        assert TrdcModel.DFMT0_register == {"DID": {"offset": 0, "width": 4}}
        assert TrdcModel.DFMT1_register == {"SID": {"offset": 8, "width": 6}}
