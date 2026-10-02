#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Unit tests for smct.parsers.cfg_resource_provider resource factory dispatch."""

from typing import Iterator

import pytest

from smct.configuration.configuration_provider import ConfigurationProvider
from smct.model.chip_model_provider import ChipModelProvider
from smct.model.model_trdc import TrdcModel
from smct.parsers.cfg_resource_provider import CfgResourceProvider
from smct.resources.res_bctrl import BctrlResourceIpgDebug
from smct.resources.res_mbc import MbcResource, MbcResourceWriteType
from smct.resources.res_mdac import MdacResource
from smct.resources.res_mrc import MrcResource
from smct.resources.resource_database_provider import ResourceDatabaseProvider


@pytest.fixture(autouse=True)
def reset_singletons() -> None:
    """Reset singleton providers used by parser factories."""
    ConfigurationProvider.clear_configuration()
    ResourceDatabaseProvider.clear_database()
    ChipModelProvider.clear_model()


@pytest.fixture(autouse=True)
def restore_mrc_configurations() -> Iterator[None]:
    """Save and restore TrdcModel.mrc_configurations around each test."""
    original = getattr(TrdcModel, "mrc_configurations", None)
    yield
    if original is None:
        if hasattr(TrdcModel, "mrc_configurations"):
            delattr(TrdcModel, "mrc_configurations")
    else:
        TrdcModel.mrc_configurations = original


class TestCfgResourceProvider:
    """Tests for CFG resource factory dispatch."""

    def test_atomic_resource_from_cfg_name_returns_none_for_unknown_prefix(self) -> None:
        """Names outside known CFG resource prefixes are not auto-created."""
        result = CfgResourceProvider.atomic_resource_from_cfg_name("UNKNOWN_1", "OUTER", [])

        assert result is None

    def test_atomic_resource_from_cfg_name_creates_mdac_range_resource(self) -> None:
        """MDAC range syntax creates an MdacResource with correct register span."""
        result = CfgResourceProvider.atomic_resource_from_cfg_name("MDAC_N0C=1-3", "PERIPH", [])

        assert isinstance(result, MdacResource)
        assert result.get_name() == "MDAC_PERIPH"
        assert result.get_master() == 0
        assert result.is_core() == 1
        assert result.get_register() == 1
        assert result.get_registers_count() == 3

    def test_atomic_resource_from_cfg_name_creates_mbc_block_range_resource(self) -> None:
        """MBC block-range syntax creates an MbcResource with a matching block range."""
        result = CfgResourceProvider.atomic_resource_from_cfg_name("MBC_D0=2.4-7", "SRAM", [])

        assert isinstance(result, MbcResource)
        assert result.get_name() == "MBC_SRAM"
        assert result.get_index() == 0
        assert result.get_mem() == 2
        assert result.get_write_type() == MbcResourceWriteType.RANGE
        assert list(result.get_block_range()) == [4, 5, 6, 7]

    def test_atomic_resource_from_cfg_name_creates_mrc_resource(self) -> None:
        """MRC syntax creates an MrcResource with TRDC and MRC indices."""
        TrdcModel.mrc_configurations = {}  # fixture restores original after test

        result = CfgResourceProvider.atomic_resource_from_cfg_name("MRC_W2=0", "DDR", ["nrgns=4"])

        assert isinstance(result, MrcResource)
        assert result.get_name() == "MRC_DDR"
        assert result.get_trdc_id() == "W"
        assert result.get_index() == 2

    def test_atomic_resource_from_cfg_name_creates_bctrl_ipg_debug_resource(self) -> None:
        """BCTRL IPG debug syntax creates the correct BCTRL resource type."""
        result = CfgResourceProvider.atomic_resource_from_cfg_name("BCTRL_A_IPG_DEBUG_2=0x10", "CPU", [])

        assert isinstance(result, BctrlResourceIpgDebug)
        assert result.get_name() == "BCTRL_A_IPG_DEBUG_2_CPU"
        assert result.get_bctrl_id() == "A"
        assert result.get_ipg_debug_registers_count() == 1
        assert result.get_ipg_debug_mask().get_value() == 0x10
