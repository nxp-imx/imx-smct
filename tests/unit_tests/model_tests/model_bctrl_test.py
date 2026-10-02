#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Unit tests for smct.model.model_bctrl BctrlModel."""

import pytest

from smct.configuration.configuration_provider import ConfigurationProvider
from smct.exceptions.cfg_tool_exception import CfgToolException
from smct.model.chip_model_provider import ChipModelProvider
from smct.model.model_bctrl import BctrlModel
from smct.resources.resource_database_provider import ResourceDatabaseProvider


@pytest.fixture(autouse=True)
def clear_providers() -> None:
    """Reset singleton providers around each test."""
    ConfigurationProvider.clear_configuration()
    ResourceDatabaseProvider.clear_database()
    ChipModelProvider.clear_model()


class TestBctrlModel:
    """Tests for BctrlModel."""

    def test_construction_default_name(self) -> None:
        """BctrlModel with no explicit name defaults to 'BCTRL_<letter>'."""
        bctrl = BctrlModel("A")

        assert bctrl.get_letter_id() == "A"
        assert bctrl.get_name() == "BCTRL_A"

    def test_construction_explicit_name(self) -> None:
        """BctrlModel stores the provided name verbatim."""
        bctrl = BctrlModel("B", "MY_BCTRL")

        assert bctrl.get_name() == "MY_BCTRL"
        assert bctrl.get_letter_id() == "B"

    def test_construction_multi_char_id_raises(self) -> None:
        """BctrlModel raises CfgToolException for multi-character id_letter."""
        with pytest.raises(CfgToolException):
            BctrlModel("AB")

    def test_add_register_ipg_debug_and_get_offsets(self) -> None:
        """add_register_ipg_debug stores offsets, get_cpu_offsets_ipg_debug retrieves them."""
        bctrl = BctrlModel("A", "BCTRL_A")

        bctrl.add_register_ipg_debug("CPU_M33P", 0, 0x100)
        bctrl.add_register_ipg_debug("CPU_M33P", 1, 0x104)

        offsets = bctrl.get_cpu_offsets_ipg_debug("CPU_M33P")
        assert offsets is not None
        assert offsets[0] == 0x100
        assert offsets[1] == 0x104

    def test_add_register_ipg_debug_gaps_filled_with_none(self) -> None:
        """add_register_ipg_debug fills intermediate slots with None."""
        bctrl = BctrlModel("A", "BCTRL_A")

        bctrl.add_register_ipg_debug("CPU_M7P", 2, 0x200)

        offsets = bctrl.get_cpu_offsets_ipg_debug("CPU_M7P")
        assert offsets is not None
        assert len(offsets) == 3
        assert offsets[0] is None
        assert offsets[1] is None
        assert offsets[2] == 0x200

    def test_get_cpu_offsets_ipg_debug_unknown_cpu_returns_none(self) -> None:
        """get_cpu_offsets_ipg_debug returns None for a CPU not yet registered."""
        bctrl = BctrlModel("A", "BCTRL_A")

        result = bctrl.get_cpu_offsets_ipg_debug("CPU_UNKNOWN")

        assert result is None

    def test_add_register_multiple_cpus(self) -> None:
        """add_register_ipg_debug handles two different CPUs independently."""
        bctrl = BctrlModel("A", "BCTRL_A")

        bctrl.add_register_ipg_debug("CPU_M33P", 0, 0x10)
        bctrl.add_register_ipg_debug("CPU_M7P", 0, 0x20)

        assert bctrl.get_cpu_offsets_ipg_debug("CPU_M33P") == [0x10]
        assert bctrl.get_cpu_offsets_ipg_debug("CPU_M7P") == [0x20]

    def test_lt_returns_true_when_less(self) -> None:
        """BctrlModel.__lt__ returns True when self letter < other letter."""
        bctrl_a = BctrlModel("A", "BCTRL_A")
        bctrl_b = BctrlModel("B", "BCTRL_B")

        assert bctrl_a < bctrl_b
        assert (bctrl_b < bctrl_a) is False

    def test_gt_returns_true_when_greater(self) -> None:
        """BctrlModel.__gt__ returns True when self letter > other letter."""
        bctrl_a = BctrlModel("A", "BCTRL_A")
        bctrl_b = BctrlModel("B", "BCTRL_B")

        assert bctrl_b > bctrl_a
        assert (bctrl_a > bctrl_b) is False

    def test_lt_with_non_bctrl_returns_false(self) -> None:
        """BctrlModel.__lt__ returns False when compared against a non-BctrlModel."""
        bctrl = BctrlModel("A", "BCTRL_A")

        assert (bctrl < "not a bctrl") is False

    def test_gt_with_non_bctrl_returns_false(self) -> None:
        """BctrlModel.__gt__ returns False when compared against a non-BctrlModel."""
        bctrl = BctrlModel("Z", "BCTRL_Z")

        assert (bctrl > 42) is False

    def test_get_raw_json_shape(self) -> None:
        """get_raw_json returns dict with required top-level keys."""
        bctrl = BctrlModel("A", "BCTRL_A")
        bctrl.add_register_ipg_debug("CPU_M33P", 0, 0x100)

        raw = bctrl.get_raw_json()

        assert isinstance(raw, dict)
        assert "bctrl" in raw  # type: ignore[operator]
        assert "name" in raw  # type: ignore[operator]
        assert "regs" in raw  # type: ignore[operator]

    def test_get_raw_json_values(self) -> None:
        """get_raw_json contains the correct id letter and name."""
        bctrl = BctrlModel("A", "BCTRL_A")

        raw = bctrl.get_raw_json()

        assert raw["bctrl"] == "A"  # type: ignore[index]
        assert raw["name"] == "BCTRL_A"  # type: ignore[index]

    def test_get_raw_json_ipg_debug_list(self) -> None:
        """get_raw_json contains IPG_DEBUG entries for added CPUs."""
        bctrl = BctrlModel("A", "BCTRL_A")
        bctrl.add_register_ipg_debug("CPU_M33P", 0, 0x100)

        raw = bctrl.get_raw_json()
        ipg_debug = raw["regs"]["IPG_DEBUG"]  # type: ignore[index]

        assert len(ipg_debug) == 1
        assert ipg_debug[0]["cpu"] == "CPU_M33P"
