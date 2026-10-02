#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Unit tests for smct.generation.gen_dox GeneratorDoxygen."""

# pylint: disable=protected-access

import os
from pathlib import Path

from smct.configuration.confdata import ConfigurationData
from smct.generation.gen_dox import GeneratorDoxygen
from smct.generation.generator import GeneratorBase


def _generate_and_read(conf: ConfigurationData, generator: GeneratorDoxygen, directory: Path) -> str:
    """Generate dox file and return its content."""
    generator.generate(conf, str(directory))
    file_path = os.path.join(str(directory), "config.dox")
    with open(file_path, "r", encoding="utf-8") as fh:
        return fh.read()


class TestGeneratorDoxygen:
    """Tests for GeneratorDoxygen."""

    def test_generate_produces_defgroup_with_dox_name(self, tmp_path: Path) -> None:
        """Test that generation produces @defgroup with the configured dox name."""
        directory = tmp_path
        generator = GeneratorDoxygen()
        conf = ConfigurationData()
        conf.set_doxygen_name_descr("MY_CONFIG", "My test description")

        content = _generate_and_read(conf, generator, directory)

        assert "@defgroup" in content
        assert "CONFIG_MY_CONFIG" in content

    def test_generate_replaces_spaces_in_dox_name_with_underscores(self, tmp_path: Path) -> None:
        """Test that spaces in doxygen name are replaced with underscores."""
        directory = tmp_path
        generator = GeneratorDoxygen()
        conf = ConfigurationData()
        conf.set_doxygen_name_descr("test config", "Some description")

        content = _generate_and_read(conf, generator, directory)

        assert "CONFIG_TEST_CONFIG" in content

    def test_generate_includes_dox_description(self, tmp_path: Path) -> None:
        """Test that generated file includes doxygen description."""
        directory = tmp_path
        generator = GeneratorDoxygen()
        conf = ConfigurationData()
        conf.set_doxygen_name_descr("CHIP", "i.MX95 EVK config")

        content = _generate_and_read(conf, generator, directory)

        assert "i.MX95 EVK config" in content

    def test_generate_opens_defgroup_and_closes_it(self, tmp_path: Path) -> None:
        """Test that the doxygen block is opened with '/*!' and closed with '*/'."""
        directory = tmp_path
        generator = GeneratorDoxygen()
        conf = ConfigurationData()
        conf.set_doxygen_name_descr("TEST", "Testing")

        content = _generate_and_read(conf, generator, directory)

        assert "/*!" in content
        assert "*/" in content
        # Assert body-specific content: @defgroup and @brief are generated in _print_doxygen,
        # not in the base header — if these are absent the doxygen body broke
        assert "@defgroup CONFIG_TEST" in content
        assert "@brief Module for Testing" in content

    def test_generate_empty_dox_name_still_produces_file(self, tmp_path: Path) -> None:
        """Test that empty dox name still produces a valid file."""
        directory = tmp_path
        generator = GeneratorDoxygen()
        conf = ConfigurationData()

        content = _generate_and_read(conf, generator, directory)

        assert "@defgroup" in content

    def test_output_file_name_is_config_dox(self) -> None:
        """Test that the output file name is 'config.dox'."""
        generator = GeneratorDoxygen()
        assert generator._get_output_file_name() == "config.dox"

    def test_header_protection_macro_returns_none(self) -> None:
        """Test that dox files have no header protection macro."""

        generator = GeneratorDoxygen()
        base: GeneratorBase = generator
        assert base._get_header_protection_macro() is None

    def test_get_doxygen_group_name_returns_sm_config(self) -> None:
        """Test that the doxygen group name is 'SM_CONFIG'."""
        generator = GeneratorDoxygen()
        assert generator._get_doxygen_group_name() == "SM_CONFIG"

    def test_str_returns_dox_generator(self) -> None:
        """Test string representation of the generator."""
        generator = GeneratorDoxygen()
        assert str(generator) == "DOX generator"

    def test_get_generator_info_returns_name_dox(self) -> None:
        """Test that generator info contains the 'dox' name key."""
        generator = GeneratorDoxygen()
        info = generator._get_generator_info()
        assert info["name"] == "dox"

    def test_should_defines_comment_not_be_generated(self) -> None:
        """Test that defines comment is not generated for doxygen files."""
        generator = GeneratorDoxygen()
        assert generator._should_defines_comment_be_generated() is False

    def test_generate_does_not_produce_ifdef_guard(self, tmp_path: Path) -> None:
        """Test that dox file has no #ifndef include guard."""
        directory = tmp_path
        generator = GeneratorDoxygen()
        conf = ConfigurationData()
        conf.set_doxygen_name_descr("TESTCFG", "desc")

        content = _generate_and_read(conf, generator, directory)

        assert "#ifndef" not in content
        assert "#endif" not in content

    def test_generate_uses_brief_in_dox_block(self, tmp_path: Path) -> None:
        """Test that @brief appears inside the doxygen content."""
        directory = tmp_path
        generator = GeneratorDoxygen()
        conf = ConfigurationData()
        conf.set_doxygen_name_descr("CFG", "brief text")

        content = _generate_and_read(conf, generator, directory)

        assert "@brief" in content
        assert "brief text" in content
