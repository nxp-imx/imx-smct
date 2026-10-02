#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Unit tests for smct.generation.gen_bctrl GeneratorBCTRL."""

# pylint: disable=protected-access

import os
from pathlib import Path

from smct.configuration.confdata import ConfigurationData
from smct.generation.gen_bctrl import GeneratorBCTRL
from smct.model.chip_model_provider import ChipModelProvider
from smct.owners.owner_lm import LM
from smct.resources.res_api import ApiResource
from smct.resources.res_bctrl import BctrlResourceIpgDebug
from tests import test_utils


def _generate_and_read(conf: ConfigurationData, generator: GeneratorBCTRL, directory: Path) -> str:
    """Generate config_bctrl.h and return its content."""
    generator.generate(conf, str(directory))
    file_path = os.path.join(str(directory), "config_bctrl.h")
    with open(file_path, "r", encoding="utf-8") as fh:
        return fh.read()


class TestGeneratorBCTRL:
    """Tests for GeneratorBCTRL."""

    def test_generate_empty_config_no_bctrl_produces_header_with_include(self, tmp_path: Path) -> None:
        """Test that generation with no BCTRLs still produces a valid header."""
        directory = tmp_path
        generator = GeneratorBCTRL()
        conf = ConfigurationData()

        content = _generate_and_read(conf, generator, directory)

        assert '#include "config_user.h"' in content

    def test_generate_with_bctrl_model_produces_bctrl_config_macro(self, tmp_path: Path) -> None:
        """Test that a model BCTRL produces SM_BCTRL_A_CONFIG macro."""
        directory = tmp_path
        generator = GeneratorBCTRL()
        conf = ConfigurationData()
        ChipModelProvider.get_model().get_bctrl("A")

        content = _generate_and_read(conf, generator, directory)

        assert "SM_BCTRL_A_CONFIG" in content

    def test_generate_with_bctrl_model_produces_section_heading(self, tmp_path: Path) -> None:
        """Test that a BCTRL model produces a section heading for BCTRL B."""
        directory = tmp_path
        generator = GeneratorBCTRL()
        conf = ConfigurationData()
        ChipModelProvider.get_model().get_bctrl("B")

        content = _generate_and_read(conf, generator, directory)

        assert "BCTRL B Config" in content

    def test_generate_with_multiple_bctrls_produces_multiple_configs(self, tmp_path: Path) -> None:
        """Test that multiple BCTRLs each produce their own config macro."""
        directory = tmp_path
        generator = GeneratorBCTRL()
        conf = ConfigurationData()
        ChipModelProvider.get_model().get_bctrl("A")
        ChipModelProvider.get_model().get_bctrl("B")

        content = _generate_and_read(conf, generator, directory)

        assert "SM_BCTRL_A_CONFIG" in content
        assert "SM_BCTRL_B_CONFIG" in content

    def test_generate_bctrl_config_contains_sm_cfg_end(self, tmp_path: Path) -> None:
        """Test that BCTRL config macro includes SM_CFG_END."""
        directory = tmp_path
        generator = GeneratorBCTRL()
        conf = ConfigurationData()
        ChipModelProvider.get_model().get_bctrl("C")

        content = _generate_and_read(conf, generator, directory)

        assert "SM_CFG_END" in content

    def test_generate_bctrl_config_contains_empty_list_comment(self, tmp_path: Path) -> None:
        """Test that a BCTRL with no assignments produces an empty-list comment."""
        directory = tmp_path
        generator = GeneratorBCTRL()
        conf = ConfigurationData()
        ChipModelProvider.get_model().get_bctrl("D")

        content = _generate_and_read(conf, generator, directory)

        assert "empty list" in content

    def test_str_returns_bctrl_generator(self) -> None:
        """Test string representation of the generator."""
        generator = GeneratorBCTRL()
        assert str(generator) == "BCTRL generator"

    def test_get_generator_info_returns_bctrl_name_and_include(self) -> None:
        """Test that generator info declares 'BCTRL' name and config_user.h include."""
        generator = GeneratorBCTRL()
        info = generator._get_generator_info()
        assert info["name"] == "BCTRL"
        assert "config_user.h" in info.get("incl", [])

    def test_get_doxygen_file_name_returns_empty_string(self) -> None:
        """Test that doxygen file name is empty string (uses addtogroup)."""
        generator = GeneratorBCTRL()
        assert generator._get_doxygen_file_name() == ""

    def test_generate_empty_config_with_no_model_bctrl_no_macros(self, tmp_path: Path) -> None:
        """Test that no BCTRL macros appear when model has no BCTRLs."""
        directory = tmp_path
        generator = GeneratorBCTRL()
        conf = ConfigurationData()

        content = _generate_and_read(conf, generator, directory)

        assert "SM_BCTRL_" not in content

    def test_generate_with_cpu_assignment_produces_sm_cfg_w1(self, tmp_path: Path) -> None:
        """Test that a BCTRL IPG_DEBUG assignment with a CPU produces a write macro."""

        test_utils.set_up()
        directory = tmp_path
        generator = GeneratorBCTRL()
        conf = ConfigurationData()

        # Create BCTRL A model with a CPU offset
        bctrl_model = ChipModelProvider.get_model().get_bctrl("A")
        assert bctrl_model is not None
        bctrl_model.add_register_ipg_debug("CPU_M33P", 0, 0x100)

        # Create an LM with a CPU resource
        lm = LM("lm0", 0, "TestLM", None, None, None, None, None, False)
        cpu_raw = {"api": "CPU", "cat": "DEV", "name": "CPU_M33P", "type": "API"}
        cpu_res = ApiResource(cpu_raw)
        lm.assign_resource(cpu_res, [], ignore_api_check=True)

        # Assign IPG_DEBUG resource to the LM
        ipg_raw = {
            "api": "BCTRL",
            "name": "IPG_DEBUG_CPU_M33P",
            "type": "BCTRL",
            "bctrl": "A",
            "regn": 0,
            "mask": "0x1",
        }
        ipg_res = BctrlResourceIpgDebug(ipg_raw)
        lm.assign_resource(ipg_res, [])
        conf.add_lm(lm)

        content = _generate_and_read(conf, generator, directory)

        # SM_BCTRL_A_CONFIG is the DCD macro; with mask=0x1 at offset 0x100 (regn=0)
        # the generator writes SM_CFG_W1(0x00000100U) with value 0x00000001U
        assert "SM_BCTRL_A_CONFIG" in content
        assert "SM_CFG_W1(0x00000100U)" in content
