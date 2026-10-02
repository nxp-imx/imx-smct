#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Unit tests for smct.generation.gen_lmm GeneratorLMM and its module-level helpers."""

# pylint: disable=protected-access

import os
from pathlib import Path
from typing import Dict, Iterator, List
from unittest.mock import Mock

import pytest

from smct.configuration.confdata import ConfigurationData
from smct.generation.gen_lmm import (
    _get_lm_start_stop_index,
    _group_start_stops,
    _print_msel,
    GeneratorLMM,
)
from smct.generation.generator import GenStructInit
from smct.owners.owner_lm import LM, MSEL, StartStop
from smct.resources.res_api import ApiResource
from smct.resources.resource_base import AtomicResource
from tests import test_utils


def _generate_and_read(conf: ConfigurationData, generator: GeneratorLMM, directory: Path) -> str:
    """Generate config_lmm.h and return its content."""
    generator.generate(conf, str(directory))
    file_path = os.path.join(str(directory), "config_lmm.h")
    with open(file_path, "r", encoding="utf-8") as fh:
        return fh.read()


def _make_lm(lm_id: str, did: int, name: str) -> LM:
    """Create a minimal LM with no RPC and default safety settings."""
    return LM(lm_id, did, name, None, None, None, None, None, False)


@pytest.fixture(autouse=True)
def _owner_class_attrs() -> Iterator[None]:
    """Seed Channel/LM class-level type dicts needed by the LM constructor."""
    with test_utils.restore_owner_class_attrs():
        yield


class TestGeneratorLMM:
    """Tests for GeneratorLMM."""

    def test_generate_empty_config_produces_lmm_header(self, tmp_path: Path) -> None:
        """Test that empty config still generates the LMM header file."""
        directory = tmp_path
        generator = GeneratorLMM()
        conf = ConfigurationData()

        content = _generate_and_read(conf, generator, directory)

        assert '#include "config_user.h"' in content

    def test_generate_empty_config_produces_sm_num_lm_zero(self, tmp_path: Path) -> None:
        """Test that empty config produces SM_NUM_LM with value 0."""
        directory = tmp_path
        generator = GeneratorLMM()
        conf = ConfigurationData()

        content = _generate_and_read(conf, generator, directory)

        assert "SM_NUM_LM" in content
        assert "SM_NUM_LM  0" in content

    def test_generate_empty_config_produces_start_stop_macros(self, tmp_path: Path) -> None:
        """Test that empty config produces start/stop count macros."""
        directory = tmp_path
        generator = GeneratorLMM()
        conf = ConfigurationData()

        content = _generate_and_read(conf, generator, directory)

        assert "SM_LM_NUM_START  0" in content
        assert "SM_LM_NUM_STOP  0" in content

    def test_generate_empty_config_produces_fault_data_macro(self, tmp_path: Path) -> None:
        """Test that empty config produces SM_LM_FAULT_DATA macro."""
        directory = tmp_path
        generator = GeneratorLMM()
        conf = ConfigurationData()

        content = _generate_and_read(conf, generator, directory)

        assert "SM_LM_FAULT_DATA" in content

    def test_generate_with_single_lm_produces_lm0_config(self, tmp_path: Path) -> None:
        """Test that a single LM produces SM_LM0_CONFIG macro."""
        test_utils.set_up()
        directory = tmp_path
        generator = GeneratorLMM()
        conf = ConfigurationData()
        lm = _make_lm("lm0", 0, "TestLM")
        conf.add_lm(lm)

        content = _generate_and_read(conf, generator, directory)

        assert "SM_LM0_CONFIG" in content
        assert '"TestLM"' in content

    def test_generate_with_two_lms_produces_lm0_and_lm1_configs(self, tmp_path: Path) -> None:
        """Test that two LMs produce SM_LM0_CONFIG and SM_LM1_CONFIG macros."""
        test_utils.set_up()
        directory = tmp_path
        generator = GeneratorLMM()
        conf = ConfigurationData()
        conf.add_lm(_make_lm("lm0", 0, "First"))
        conf.add_lm(_make_lm("lm1", 1, "Second"))

        content = _generate_and_read(conf, generator, directory)

        assert "SM_LM0_CONFIG" in content
        assert "SM_LM1_CONFIG" in content

    def test_generate_with_lm_produces_sm_lm_config_data_list(self, tmp_path: Path) -> None:
        """Test that LMs produce SM_LM_CONFIG_DATA listing LM0."""
        test_utils.set_up()
        directory = tmp_path
        generator = GeneratorLMM()
        conf = ConfigurationData()
        conf.add_lm(_make_lm("lm0", 0, "MyLM"))

        content = _generate_and_read(conf, generator, directory)

        assert "SM_LM_CONFIG_DATA" in content
        assert "SM_LM0_CONFIG" in content

    def test_generate_config_name_truncated_in_sm_lm_cfg_name(self, tmp_path: Path) -> None:
        """Test that config name longer than 15 chars is truncated in macro."""
        test_utils.set_up()
        directory = tmp_path
        generator = GeneratorLMM()
        conf = ConfigurationData()
        conf.set_config_name("VeryLongConfigurationName")

        content = _generate_and_read(conf, generator, directory)

        assert "SM_LM_CFG_NAME" in content
        assert '"VeryLongConfigu"' in content

    def test_str_returns_lmm_generator(self) -> None:
        """Test string representation of the generator."""
        generator = GeneratorLMM()
        assert str(generator) == "LMM generator"

    def test_get_generator_info_returns_lmm_name(self) -> None:
        """Test that generator info declares the 'LMM' name."""
        generator = GeneratorLMM()
        info = generator._get_generator_info()
        assert info["name"] == "LMM"
        assert "config_user.h" in info.get("incl", [])

    def test_generate_with_lm_having_rtime_includes_rtime_field(self, tmp_path: Path) -> None:
        """Test that an LM with rtime set produces the rtime struct field."""
        test_utils.set_up()
        directory = tmp_path
        generator = GeneratorLMM()
        conf = ConfigurationData()
        lm = LM("lm0", 0, "LM0", None, 100, None, None, None, False)
        conf.add_lm(lm)

        content = _generate_and_read(conf, generator, directory)

        assert "rtime" in content
        assert "100U" in content

    def test_generate_with_lm_having_group_includes_group_field(self, tmp_path: Path) -> None:
        """Test that an LM with group set produces the group struct field."""
        test_utils.set_up()
        directory = tmp_path
        generator = GeneratorLMM()
        conf = ConfigurationData()
        lm = LM("lm0", 0, "LM0", None, None, None, 5, None, False)
        conf.add_lm(lm)

        content = _generate_and_read(conf, generator, directory)

        assert "group" in content
        assert "5U" in content

    def test_generate_with_lm_having_starts_includes_start_field_and_list(self, tmp_path: Path) -> None:
        """Test that an LM with starts produces start index and SM_LM_START_DATA."""
        test_utils.set_up()

        directory = tmp_path
        generator = GeneratorLMM()
        conf = ConfigurationData()
        lm = LM("lm0", 0, "LM0", None, None, None, None, None, False)
        # Add a start resource via msel
        msel = lm.get_msel(0)
        mock_res: Mock = Mock(spec=ApiResource)
        mock_res.get_name.return_value = "CPU_M33P"
        mock_res.get_start_stop_type.return_value = "LMM_SS_CPU_WAIT"
        mock_res.get_api_id.return_value = "DEV_SM_CPU_M33P"
        msel.add_start_stop(True, False, mock_res, "1")
        conf.add_lm(lm)

        content = _generate_and_read(conf, generator, directory)

        assert "start" in content
        assert "SM_LM_START_DATA" in content
        # Assert the specific start entry contents: ss type and resource ID
        assert "LMM_SS_CPU_WAIT" in content
        assert "DEV_SM_CPU_M33P" in content


class TestGroupStartStops:
    """Unit tests for the _group_start_stops module-level function."""

    def _make_start_stop_in_msel(self, lm: LM, msel_index: int) -> StartStop:
        """Create a StartStop in the given LM's MSEL."""
        msel = lm.get_msel(msel_index)
        mock_res: Mock = Mock(spec=AtomicResource)
        mock_res.get_name.return_value = f"RES_{lm.get_id()}_{msel_index}"
        msel.add_start_stop(True, False, mock_res, "1")
        starts = msel.get_all_start_stops(True)
        assert len(starts) > 0
        ss = starts[0]
        assert ss is not None
        return ss

    def test_group_start_stops_empty_input_returns_empty_dict(self) -> None:
        """Test that empty input produces an empty dict."""
        conf = ConfigurationData()
        result = _group_start_stops(conf, [], True)
        assert not result

    def test_group_start_stops_single_lm_single_ss_produces_mapping(self) -> None:
        """Test that a single start-stop maps to its LM ID."""
        conf = ConfigurationData()
        lm = _make_lm("lm0", 0, "LM0")
        conf.add_lm(lm)
        ss = self._make_start_stop_in_msel(lm, 0)

        result = _group_start_stops(conf, [ss], True)

        assert 0 in result
        assert ss in result[0]

    def test_group_start_stops_two_lms_separated_by_id(self) -> None:
        """Test that start-stops from different LMs are grouped by LM ID."""
        conf = ConfigurationData()
        lm0 = _make_lm("lm0", 0, "LM0")
        lm1 = _make_lm("lm1", 1, "LM1")
        conf.add_lm(lm0)
        conf.add_lm(lm1)
        ss0 = self._make_start_stop_in_msel(lm0, 0)
        ss1 = self._make_start_stop_in_msel(lm1, 0)

        result = _group_start_stops(conf, [ss0, ss1], True)

        assert 0 in result
        assert 1 in result
        assert ss0 in result[0]
        assert ss1 in result[1]


class TestGetLmStartStopIndex:
    """Unit tests for the _get_lm_start_stop_index module-level function."""

    def test_empty_dict_returns_zero(self) -> None:
        """Test that empty ss_all dict returns 0 for any index."""
        result = _get_lm_start_stop_index({}, 0)
        assert result == 0

    def test_single_lm_at_index_zero_returns_zero(self) -> None:
        """Test that the first LM always starts at index 0."""
        ss_all: Dict[int, List[StartStop]] = {0: [Mock(), Mock()]}
        result = _get_lm_start_stop_index(ss_all, 0)
        assert result == 0

    def test_second_lm_offset_accounts_for_first_lm_entries(self) -> None:
        """Test that LM1 index equals the count of LM0's start-stops."""
        ss_all: Dict[int, List[StartStop]] = {0: [Mock(), Mock(), Mock()]}
        result = _get_lm_start_stop_index(ss_all, 1)
        assert result == 3

    def test_third_lm_offset_accounts_for_first_two_lms(self) -> None:
        """Test that LM2 index equals count of LM0 plus LM1 entries."""
        ss_all: Dict[int, List[StartStop]] = {0: [Mock(), Mock()], 1: [Mock()]}
        result = _get_lm_start_stop_index(ss_all, 2)
        assert result == 3

    def test_gap_in_lm_ids_skips_missing_entries(self) -> None:
        """Test that a gap in LM IDs contributes zero to the offset."""
        ss_all: Dict[int, List[StartStop]] = {0: [Mock()], 2: [Mock(), Mock()]}
        # LM ID 1 is absent — contributes 0
        result = _get_lm_start_stop_index(ss_all, 2)
        assert result == 1


class TestPrintMsel:
    """Unit tests for the _print_msel module-level function."""

    def test_print_msel_sets_boot_field_when_boot_is_not_none(self) -> None:
        """Test that boot value is stored in struct when MSEL has a boot value."""
        lm = _make_lm("lm0", 0, "LM0")
        msel = MSEL(lm, 0, 3, None)
        struct = GenStructInit("TEST_MSEL", None)

        _print_msel(struct, msel)

        assert struct["boot[0]"] == 3

    def test_print_msel_sets_boot_skip_field_when_skip_is_not_none(self) -> None:
        """Test that bootSkip value is stored in struct when MSEL has a skip value."""
        lm = _make_lm("lm0", 0, "LM0")
        msel = MSEL(lm, 2, None, True)
        struct = GenStructInit("TEST_MSEL", None)

        _print_msel(struct, msel)

        assert struct["bootSkip[2]"] is True

    def test_print_msel_sets_both_boot_and_skip(self) -> None:
        """Test that both boot and bootSkip are set when both values are present."""
        lm = _make_lm("lm0", 0, "LM0")
        msel = MSEL(lm, 1, 5, False)
        struct = GenStructInit("TEST_MSEL", None)

        _print_msel(struct, msel)

        assert struct["boot[1]"] == 5
        assert struct["bootSkip[1]"] is False

    def test_print_msel_no_boot_no_skip_does_not_add_entries(self) -> None:
        """Test that no entries are added when boot and skip are None."""
        lm = _make_lm("lm0", 0, "LM0")
        msel = MSEL(lm, 0, None, None)
        struct = GenStructInit("TEST_MSEL", None)

        _print_msel(struct, msel)

        assert len(struct) == 0
