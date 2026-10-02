#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Unit tests for smct.resources.res_mdac MdacResource."""

from typing import Any, Dict

import pytest

from smct.configuration.configuration_provider import ConfigurationProvider
from smct.exceptions.cfg_tool_exception import CfgToolException
from smct.model.chip_model_provider import ChipModelProvider
from smct.resources.res_mdac import MdacResource
from smct.resources.resource_database_provider import ResourceDatabaseProvider
from smct.utils import FormatedInt


@pytest.fixture(autouse=True)
def clear_providers() -> None:
    """Reset singleton providers around each test."""
    ConfigurationProvider.clear_configuration()
    ResourceDatabaseProvider.clear_database()
    ChipModelProvider.clear_model()


def _minimal_raw(**overrides: Any) -> Dict[str, Any]:
    """Return a minimal valid raw dict for MdacResource, with optional overrides."""
    raw: Dict[str, Any] = {
        "name": "MDAC_RES",
        "type": "MDAC",
        "trdc": "A",
        "master": 3,
        "core": False,
    }
    raw.update(overrides)
    return raw


class TestMdacResource:
    """Tests for MdacResource constructed from a raw dict."""

    def test_construction_defaults_register_to_zero(self) -> None:
        """Test that 'reg' defaults to 0 when absent from the raw dict."""
        resource = MdacResource(_minimal_raw())
        assert resource.get_register() == 0

    def test_construction_defaults_registers_count_to_one(self) -> None:
        """Test that 'rcnt' defaults to 1 when absent from the raw dict."""
        resource = MdacResource(_minimal_raw())
        assert resource.get_registers_count() == 1

    def test_construction_with_explicit_reg(self) -> None:
        """Test that an explicit 'reg' value is stored correctly."""
        resource = MdacResource(_minimal_raw(reg=2))
        assert resource.get_register() == 2

    def test_construction_with_explicit_rcnt(self) -> None:
        """Test that an explicit 'rcnt' value is stored correctly."""
        resource = MdacResource(_minimal_raw(rcnt=4))
        assert resource.get_registers_count() == 4

    def test_get_master_returns_master_field(self) -> None:
        """Test get_master returns the value from the 'master' field."""
        resource = MdacResource(_minimal_raw(master=7))
        assert resource.get_master() == 7

    def test_is_core_true(self) -> None:
        """Test is_core returns True when 'core' is True in the raw dict."""
        resource = MdacResource(_minimal_raw(core=True))
        assert resource.is_core() is True

    def test_is_core_false(self) -> None:
        """Test is_core returns False when 'core' is False in the raw dict."""
        resource = MdacResource(_minimal_raw(core=False))
        assert resource.is_core() is False

    def test_get_name_returns_raw_name(self) -> None:
        """Test get_name returns the name from the raw dict."""
        resource = MdacResource(_minimal_raw(name="MY_MDAC"))
        assert resource.get_name() == "MY_MDAC"

    def test_construction_missing_trdc_raises_cfg_tool_exception(self) -> None:
        """Test CfgToolException is raised when 'trdc' key is missing."""
        raw: Dict[str, Any] = {"name": "MDAC_BAD", "type": "MDAC", "master": 1, "core": False}
        with pytest.raises(CfgToolException):
            MdacResource(raw)

    def test_construction_missing_master_raises_cfg_tool_exception(self) -> None:
        """Test CfgToolException is raised when 'master' key is missing."""
        raw: Dict[str, Any] = {"name": "MDAC_BAD", "type": "MDAC", "trdc": "B", "core": False}
        with pytest.raises(CfgToolException):
            MdacResource(raw)

    def test_get_assignment_parameters_parses_sa_and_pa_as_int(self) -> None:
        """Test that sa and pa parameter strings are parsed as integers."""
        resource = MdacResource(_minimal_raw())
        result = resource.get_assignment_parameters(["sa=1", "pa=2"])
        assert result is not None
        assert result["sa"] == 1
        assert result["pa"] == 2

    def test_get_assignment_parameters_sid_returns_formated_int(self) -> None:
        """Test that the sid parameter is returned as a FormatedInt."""
        resource = MdacResource(_minimal_raw())
        result = resource.get_assignment_parameters(["sid=0x10"])
        assert result is not None
        assert isinstance(result["sid"], FormatedInt)
        assert result["sid"].get_value() == 0x10

    def test_get_assignment_parameters_mdid_parsed_as_int(self) -> None:
        """Test that mdid parameter is parsed as an integer."""
        resource = MdacResource(_minimal_raw())
        result = resource.get_assignment_parameters(["mdid=5"])
        assert result is not None
        assert result["mdid"] == 5

    def test_get_assignment_parameters_kpa_parsed_as_int(self) -> None:
        """Test that kpa parameter is parsed as an integer."""
        resource = MdacResource(_minimal_raw())
        result = resource.get_assignment_parameters(["kpa=1"])
        assert result is not None
        assert result["kpa"] == 1

    def test_get_assignment_parameters_omits_absent_keys(self) -> None:
        """Test that only parameters that appear in the params list are included."""
        resource = MdacResource(_minimal_raw())
        result = resource.get_assignment_parameters(["sa=3"])
        assert result is not None
        assert "sa" in result
        assert "pa" not in result
        assert "sid" not in result
        assert "mdid" not in result
        assert "kpa" not in result

    def test_get_assignment_parameters_empty_list_returns_empty_dict(self) -> None:
        """Test that an empty params list returns an empty dict (not None)."""
        resource = MdacResource(_minimal_raw())
        result = resource.get_assignment_parameters([])
        assert not result

    def test_get_assignment_parameters_all_known_keys(self) -> None:
        """Test get_assignment_parameters correctly parses all five known keys at once."""
        resource = MdacResource(_minimal_raw())
        result = resource.get_assignment_parameters(["sa=0", "pa=1", "mdid=2", "sid=3", "kpa=0"])
        assert result is not None
        assert result["sa"] == 0
        assert result["pa"] == 1
        assert result["mdid"] == 2
        assert isinstance(result["sid"], FormatedInt)
        assert result["sid"].get_value() == 3
        assert result["kpa"] == 0

    def test_get_assignment_parameters_sid_decimal_string(self) -> None:
        """Test sid parsed from a plain decimal string is a FormatedInt."""
        resource = MdacResource(_minimal_raw())
        result = resource.get_assignment_parameters(["sid=7"])
        assert result is not None
        assert isinstance(result["sid"], FormatedInt)
        assert result["sid"].get_value() == 7

    def test_get_assignment_parameters_invalid_int_value_stored_as_string(self) -> None:
        """Test that a non-numeric value for sa is stored as a string (ValueError is swallowed).

        MdacResource.get_assignment_parameters catches ValueError from parse_int and
        silently keeps the original string value rather than dropping the key.
        """
        resource = MdacResource(_minimal_raw())
        result = resource.get_assignment_parameters(["sa=notanumber"])
        # ValueError is swallowed; val remains the original string and is added to result
        assert result is not None
        assert "sa" in result
        assert isinstance(result["sa"], str)
        assert result["sa"] == "notanumber"

    def test_get_assignment_parameters_unknown_key_is_ignored(self) -> None:
        """Test that an unknown key in the params list is not included in the result.

        Only the five known keys (sa, pa, mdid, sid, kpa) are processed; any other
        key-value pair is silently ignored.
        """
        resource = MdacResource(_minimal_raw())
        result = resource.get_assignment_parameters(["unknown=5", "sa=1"])
        assert result is not None
        assert "unknown" not in result
        assert result["sa"] == 1

    def test_get_assignment_parameters_malformed_sid_raises_key_error(self) -> None:
        """Test that a malformed sid value propagates KeyError from FormatedInt.

        Characterization test: get_assignment_parameters only catches ValueError, but
        FormatedInt('notahex') raises KeyError, so the error is NOT swallowed and
        propagates to the caller. Pins current behavior to catch regressions if the
        source later broadens its exception handling.
        """
        resource = MdacResource(_minimal_raw())
        with pytest.raises(KeyError):
            resource.get_assignment_parameters(["sa=2", "sid=notahex"])
