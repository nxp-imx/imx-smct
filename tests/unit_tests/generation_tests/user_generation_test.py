#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Unit tests for smct.generation.gen_user GeneratorUser."""

# pylint: disable=protected-access

import os
import tempfile
from pathlib import Path

from smct.configuration.confdata import ConfigurationData
from smct.generation.gen_user import GeneratorUser
from smct.model.chip_model_provider import ChipModelProvider


def _generate_and_read(conf: ConfigurationData, generator: GeneratorUser, directory: Path) -> str:
    """Generate config_user.h and return its content."""
    generator.generate(conf, str(directory))
    file_path = os.path.join(str(directory), "config_user.h")
    with open(file_path, "r", encoding="utf-8") as fh:
        return fh.read()


class TestGeneratorUser:
    """Tests for GeneratorUser."""

    def test_generate_with_no_mixes_produces_config_user_header(self, tmp_path: Path) -> None:
        """Test that generation with empty model still produces config_user.h."""
        generator = GeneratorUser()
        conf = ConfigurationData()

        content = _generate_and_read(conf, generator, tmp_path)

        assert '#include "config.h"' in content

    def test_generate_with_no_mixes_produces_no_mix_macros(self, tmp_path: Path) -> None:
        """Test that generation without mixes does not emit any SM_<MIX>_CONFIG macros."""
        generator = GeneratorUser()
        conf = ConfigurationData()

        content = _generate_and_read(conf, generator, tmp_path)

        assert "SM_" not in content

    def test_generate_with_single_mix_produces_sm_mix_config(self, tmp_path: Path) -> None:
        """Test that a single mix produces the SM_<MIX>_CONFIG macro."""
        generator = GeneratorUser()
        conf = ConfigurationData()
        ChipModelProvider.get_model().add_mix("testmix")

        content = _generate_and_read(conf, generator, tmp_path)

        assert "SM_TESTMIX_CONFIG" in content

    def test_generate_mix_name_is_uppercased(self, tmp_path: Path) -> None:
        """Test that lowercase mix names are uppercased in macros."""
        generator = GeneratorUser()
        conf = ConfigurationData()
        ChipModelProvider.get_model().add_mix("lowermix")

        content = _generate_and_read(conf, generator, tmp_path)

        assert "SM_LOWERMIX_CONFIG" in content

    def test_generate_with_multiple_mixes_produces_all_macros(self, tmp_path: Path) -> None:
        """Test that multiple mixes each produce a config macro."""
        generator = GeneratorUser()
        conf = ConfigurationData()
        ChipModelProvider.get_model().add_mix("mix_a")
        ChipModelProvider.get_model().add_mix("mix_b")

        content = _generate_and_read(conf, generator, tmp_path)

        assert "SM_MIX_A_CONFIG" in content
        assert "SM_MIX_B_CONFIG" in content

    def test_generate_includes_sm_cfg_end_in_mix_macro(self, tmp_path: Path) -> None:
        """Test that SM_CFG_END appears inside each mix macro."""
        generator = GeneratorUser()
        conf = ConfigurationData()
        ChipModelProvider.get_model().add_mix("demo")

        content = _generate_and_read(conf, generator, tmp_path)

        assert "SM_CFG_END" in content

    def test_can_file_open_returns_false_for_existing_file(self) -> None:
        """Test that can_file_open returns False when file already exists."""
        generator = GeneratorUser()
        with tempfile.NamedTemporaryFile() as existing_file:
            assert generator.can_file_open(existing_file.name, False) is False

    def test_can_file_open_returns_true_for_nonexistent_path(self) -> None:
        """Test that can_file_open returns True when file does not exist."""
        generator = GeneratorUser()
        nonexistent = os.path.join(tempfile.gettempdir(), "smct_test_does_not_exist_xyz.h")
        assert generator.can_file_open(nonexistent, False) is True

    def test_generate_skips_existing_file_when_can_file_open_false(self, tmp_path: Path) -> None:
        """Test that generate() skips writing when can_file_open returns False."""
        generator = GeneratorUser()
        conf = ConfigurationData()
        output_path = os.path.join(str(tmp_path), "config_user.h")
        with open(output_path, "w", encoding="utf-8") as fh:
            fh.write("# pre-existing")

        generator.generate(conf, str(tmp_path))

        with open(output_path, "r", encoding="utf-8") as fh:
            content = fh.read()
        assert "# pre-existing" in content

    def test_str_returns_user_generator(self) -> None:
        """Test string representation of the generator."""
        generator = GeneratorUser()
        assert str(generator) == "USER generator"

    def test_get_generator_info_returns_name_and_include(self) -> None:
        """Test that generator info declares 'user' name and config.h include."""
        generator = GeneratorUser()
        info = generator._get_generator_info()
        assert info["name"] == "user"
        assert "config.h" in info.get("incl", [])

    def test_get_doxygen_file_name_returns_empty_string(self) -> None:
        """Test that the doxygen file name is empty (uses group instead)."""
        generator = GeneratorUser()
        assert generator._get_doxygen_file_name() == ""

    def test_generate_heading_per_mix(self, tmp_path: Path) -> None:
        """Test that a heading section is generated for each mix."""
        generator = GeneratorUser()
        conf = ConfigurationData()
        ChipModelProvider.get_model().add_mix("CAMIX")

        content = _generate_and_read(conf, generator, tmp_path)

        assert "CAMIX Config" in content
