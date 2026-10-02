#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Unit tests for smct.resources.res_bctrl BctrlResource and BctrlResourceIpgDebug."""

from typing import Any, Dict

import pytest

from smct.configuration.configuration_provider import ConfigurationProvider
from smct.exceptions.cfg_tool_exception import CfgToolException
from smct.model.chip_model_provider import ChipModelProvider
from smct.resources.res_bctrl import BctrlResource, BctrlResourceIpgDebug
from smct.resources.resource_database_provider import ResourceDatabaseProvider
from smct.utils import FormatedInt


@pytest.fixture(autouse=True)
def clear_providers() -> None:
    """Reset singleton providers around each test."""
    ConfigurationProvider.clear_configuration()
    ResourceDatabaseProvider.clear_database()
    ChipModelProvider.clear_model()


class TestBctrlResource:
    """Tests for BctrlResource constructed from a raw dict."""

    def test_construction_stores_bctrl_id(self) -> None:
        """Test that BctrlResource stores the bctrl field as the BCTRL ID."""
        raw: Dict[str, Any] = {"name": "BCTRL_A_RES", "type": "BCTRL", "bctrl": "A"}
        resource = BctrlResource(raw)
        assert resource.get_bctrl_id() == "A"

    def test_get_name_returns_raw_name(self) -> None:
        """Test that get_name returns the name field from the raw dict."""
        raw: Dict[str, Any] = {"name": "MY_BCTRL", "type": "BCTRL", "bctrl": "B"}
        resource = BctrlResource(raw)
        assert resource.get_name() == "MY_BCTRL"

    def test_get_bctrl_id_different_values(self) -> None:
        """Test get_bctrl_id with multiple different bctrl ID strings."""
        for bctrl_id in ("A", "B", "C", "Z"):
            raw: Dict[str, Any] = {"name": f"RES_{bctrl_id}", "type": "BCTRL", "bctrl": bctrl_id}
            resource = BctrlResource(raw)
            assert resource.get_bctrl_id() == bctrl_id

    def test_construction_missing_bctrl_raises_cfg_tool_exception(self) -> None:
        """Test that BctrlResource raises CfgToolException when the 'bctrl' key is absent."""
        raw: Dict[str, Any] = {"name": "BAD_BCTRL", "type": "BCTRL"}
        with pytest.raises(CfgToolException):
            BctrlResource(raw)

    def test_raw_json_round_trips_correctly(self) -> None:
        """Test that get_raw_json returns a copy matching the original dict."""
        raw: Dict[str, Any] = {"name": "BCTRL_X", "type": "BCTRL", "bctrl": "X"}
        resource = BctrlResource(raw)
        assert resource.get_raw_json() == raw


class TestBctrlResourceIpgDebug:
    """Tests for BctrlResourceIpgDebug constructed from a raw dict."""

    def test_construction_stores_all_fields(self) -> None:
        """Test that all fields are stored correctly from the raw dict."""
        raw: Dict[str, Any] = {
            "name": "IPG_DEBUG_RES",
            "type": "BCTRL_IPG_DEBUG",
            "bctrl": "A",
            "regn": 2,
            "mask": "0xFF00",
        }
        resource = BctrlResourceIpgDebug(raw)
        assert resource.get_bctrl_id() == "A"
        assert resource.get_ipg_debug_registers_count() == 2
        assert isinstance(resource.get_ipg_debug_mask(), FormatedInt)
        assert resource.get_ipg_debug_mask().get_value() == 0xFF00

    def test_mask_as_integer_is_wrapped_in_formated_int(self) -> None:
        """Test that an integer mask is wrapped into a FormatedInt."""
        raw: Dict[str, Any] = {
            "name": "IPG_INT_MASK",
            "type": "BCTRL_IPG_DEBUG",
            "bctrl": "B",
            "regn": 1,
            "mask": 255,
        }
        resource = BctrlResourceIpgDebug(raw)
        assert resource.get_ipg_debug_mask().get_value() == 255

    def test_construction_missing_regn_raises_cfg_tool_exception(self) -> None:
        """Test that CfgToolException is raised when 'regn' key is missing."""
        raw: Dict[str, Any] = {"name": "IPG_NO_REGN", "type": "BCTRL_IPG_DEBUG", "bctrl": "A", "mask": "0xFF"}
        with pytest.raises(CfgToolException):
            BctrlResourceIpgDebug(raw)

    def test_construction_missing_mask_raises_cfg_tool_exception(self) -> None:
        """Test that CfgToolException is raised when 'mask' key is missing."""
        raw: Dict[str, Any] = {"name": "IPG_NO_MASK", "type": "BCTRL_IPG_DEBUG", "bctrl": "A", "regn": 1}
        with pytest.raises(CfgToolException):
            BctrlResourceIpgDebug(raw)

    def test_get_ipg_debug_registers_count_returns_regn_value(self) -> None:
        """Test get_ipg_debug_registers_count returns the exact value from 'regn'."""
        raw: Dict[str, Any] = {
            "name": "IPG_REG4",
            "type": "BCTRL_IPG_DEBUG",
            "bctrl": "C",
            "regn": 4,
            "mask": "0x0F",
        }
        resource = BctrlResourceIpgDebug(raw)
        assert resource.get_ipg_debug_registers_count() == 4

    def test_inherits_bctrl_resource_behavior(self) -> None:
        """Test that BctrlResourceIpgDebug is also a BctrlResource."""
        raw: Dict[str, Any] = {
            "name": "IPG_INHERIT",
            "type": "BCTRL_IPG_DEBUG",
            "bctrl": "D",
            "regn": 1,
            "mask": "0x01",
        }
        resource = BctrlResourceIpgDebug(raw)
        assert isinstance(resource, BctrlResource)
        assert resource.get_bctrl_id() == "D"
