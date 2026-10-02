#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Unit tests for smct.generation.generator.GeneratorBase via a minimal test subclass."""

# pylint: disable=protected-access

import os
from tempfile import TemporaryDirectory
from typing import Any, Dict, List

import pytest

from smct.configuration.confdata import ConfigurationData
from smct.exceptions.cfg_tool_exception import CfgToolException
from smct.generation.generator import GeneratorBase


class _MinimalGenerator(GeneratorBase):
    """Minimal concrete GeneratorBase subclass for testing."""

    def _get_generator_info(self) -> Dict[str, Any]:
        """Return minimal generator info."""
        return {"name": "TEST", "incl": ["config_user.h"]}

    def print_content(self) -> None:
        """Write a single define to the output file."""
        self._print("#define SM_TEST_MARKER  1U")


class _GeneratorWithNoIncludes(GeneratorBase):
    """GeneratorBase subclass that returns no includes."""

    def _get_generator_info(self) -> Dict[str, Any]:
        """Return info with no includes key."""
        return {"name": "NOINC"}

    def print_content(self) -> None:
        """Write nothing beyond the header/footer."""


class TestGeneratorBase:
    """Tests for GeneratorBase abstract base class via minimal subclasses."""

    def _make_conf(self) -> ConfigurationData:
        """Build a minimal ConfigurationData suitable for generation."""
        conf = ConfigurationData()
        conf.set_doxygen_name_descr("test config", "A test configuration")
        conf.set_config_name("TestConfig")
        return conf

    def test_get_generator_name_returns_name_from_info(self) -> None:
        """_get_generator_name() extracts the 'name' key from _get_generator_info()."""
        gen = _MinimalGenerator()

        assert gen._get_generator_name() == "TEST"

    def test_get_generator_includes_returns_incl_list(self) -> None:
        """_get_generator_includes() extracts the 'incl' list from _get_generator_info()."""
        gen = _MinimalGenerator()

        includes: List[str] = gen._get_generator_includes()

        assert "config_user.h" in includes

    def test_get_generator_includes_empty_when_no_incl_key(self) -> None:
        """_get_generator_includes() returns [] when 'incl' key is absent."""
        gen = _GeneratorWithNoIncludes()

        assert not gen._get_generator_includes()

    def test_get_configuration_raises_before_generate(self) -> None:
        """_get_configuration() raises CfgToolException before generate() is called."""
        gen = _MinimalGenerator()

        with pytest.raises(CfgToolException, match="No configuration was set"):
            gen._get_configuration()

    def test_get_open_file_is_none_before_generate(self) -> None:
        """get_open_file() returns None before generate() is called."""
        gen = _MinimalGenerator()

        assert gen.get_open_file() is None

    def test_generate_creates_header_file(self) -> None:
        """generate() creates the expected output file in the directory."""
        gen = _MinimalGenerator()
        conf = self._make_conf()

        with TemporaryDirectory() as tmpdir:
            gen.generate(conf, tmpdir)

            expected = os.path.join(tmpdir, "config_test.h")
            assert os.path.exists(expected)

    def test_generate_file_contains_header_protection_macro(self) -> None:
        """Generated file contains the header-guard #ifndef and #define."""
        gen = _MinimalGenerator()
        conf = self._make_conf()

        with TemporaryDirectory() as tmpdir:
            gen.generate(conf, tmpdir)
            with open(os.path.join(tmpdir, "config_test.h"), encoding="utf-8") as fh:
                content = fh.read()

        assert "#ifndef CONFIG_TEST_H" in content
        assert "#define CONFIG_TEST_H" in content

    def test_generate_file_contains_copyright(self) -> None:
        """Generated file contains the NXP copyright comment."""
        gen = _MinimalGenerator()
        conf = self._make_conf()

        with TemporaryDirectory() as tmpdir:
            gen.generate(conf, tmpdir)
            with open(os.path.join(tmpdir, "config_test.h"), encoding="utf-8") as fh:
                content = fh.read()

        assert "NXP" in content

    def test_generate_file_contains_include(self) -> None:
        """Generated file contains the #include directive from generator info."""
        gen = _MinimalGenerator()
        conf = self._make_conf()

        with TemporaryDirectory() as tmpdir:
            gen.generate(conf, tmpdir)
            with open(os.path.join(tmpdir, "config_test.h"), encoding="utf-8") as fh:
                content = fh.read()

        assert '#include "config_user.h"' in content

    def test_generate_file_contains_print_content_output(self) -> None:
        """Generated file contains the output produced by print_content()."""
        gen = _MinimalGenerator()
        conf = self._make_conf()

        with TemporaryDirectory() as tmpdir:
            gen.generate(conf, tmpdir)
            with open(os.path.join(tmpdir, "config_test.h"), encoding="utf-8") as fh:
                content = fh.read()

        assert "SM_TEST_MARKER" in content

    def test_generate_raises_when_output_dir_missing_and_force_false(self) -> None:
        """generate() raises CfgToolException when directory doesn't exist and force=False."""
        gen = _MinimalGenerator()
        conf = self._make_conf()

        with pytest.raises(CfgToolException, match="does not exist"):
            gen.generate(conf, "/nonexistent/path/that/cannot/exist", force=False)

    def test_generate_raises_file_exists_without_force(self) -> None:
        """generate() raises FileExistsError when file already exists and force=False."""
        gen = _MinimalGenerator()
        conf = self._make_conf()

        with TemporaryDirectory() as tmpdir:
            gen.generate(conf, tmpdir)

            with pytest.raises(FileExistsError):
                gen.generate(conf, tmpdir, force=False)

    def test_generate_overwrites_with_force_true(self) -> None:
        """generate() with force=True overwrites an existing file without error."""
        gen = _MinimalGenerator()
        conf = self._make_conf()

        with TemporaryDirectory() as tmpdir:
            gen.generate(conf, tmpdir)
            gen.generate(conf, tmpdir, force=True)  # must not raise

            expected = os.path.join(tmpdir, "config_test.h")
            assert os.path.exists(expected)

    def test_get_open_file_is_none_after_generate(self) -> None:
        """get_open_file() returns None after generate() completes."""
        gen = _MinimalGenerator()
        conf = self._make_conf()

        with TemporaryDirectory() as tmpdir:
            gen.generate(conf, tmpdir)

        assert gen.get_open_file() is None
