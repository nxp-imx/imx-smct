#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Unit tests for smct.generation.config_generator.ConfigGenerator delegation."""

# pylint: disable=protected-access

from tempfile import TemporaryDirectory
from typing import cast, List
from unittest.mock import MagicMock, patch

from smct.configuration.confdata import ConfigurationData
from smct.generation.config_generator import ConfigGenerator

# All sub-generator class names as imported into smct.generation.config_generator
_SUB_GENERATOR_NAMES = [
    "smct.generation.config_generator.GeneratorSCMI",
    "smct.generation.config_generator.GeneratorSMT",
    "smct.generation.config_generator.GeneratorMBMU",
    "smct.generation.config_generator.GeneratorMailboxLoopback",
    "smct.generation.config_generator.GeneratorLMM",
    "smct.generation.config_generator.GeneratorBCTRL",
    "smct.generation.config_generator.GeneratorTRDC",
    "smct.generation.config_generator.GeneratorDoxygen",
    "smct.generation.config_generator.GeneratorMakeFile",
    "smct.generation.config_generator.GeneratorDev",
    "smct.generation.config_generator.GeneratorUser",
    "smct.generation.config_generator.GeneratorBoard",
    "smct.generation.config_generator.GeneratorTest",
    "smct.generation.config_generator.GeneratorFusa",
]


class TestConfigGenerator:
    """Tests for ConfigGenerator delegation to individual sub-generators."""

    def test_populate_false_creates_empty_generator_list(self) -> None:
        """ConfigGenerator(populate=False) has no generators."""
        gen = ConfigGenerator(populate=False)

        assert gen._gens == []

    def test_populate_true_creates_all_sub_generators(self) -> None:
        """ConfigGenerator(populate=True) creates all 14 sub-generators."""
        # Use patches so no real generation occurs during instantiation side-effects
        with patch.multiple(
            "smct.generation.config_generator",
            GeneratorSCMI=MagicMock(return_value=MagicMock()),
            GeneratorSMT=MagicMock(return_value=MagicMock()),
            GeneratorMBMU=MagicMock(return_value=MagicMock()),
            GeneratorMailboxLoopback=MagicMock(return_value=MagicMock()),
            GeneratorLMM=MagicMock(return_value=MagicMock()),
            GeneratorBCTRL=MagicMock(return_value=MagicMock()),
            GeneratorTRDC=MagicMock(return_value=MagicMock()),
            GeneratorDoxygen=MagicMock(return_value=MagicMock()),
            GeneratorMakeFile=MagicMock(return_value=MagicMock()),
            GeneratorDev=MagicMock(return_value=MagicMock()),
            GeneratorUser=MagicMock(return_value=MagicMock()),
            GeneratorBoard=MagicMock(return_value=MagicMock()),
            GeneratorTest=MagicMock(return_value=MagicMock()),
            GeneratorFusa=MagicMock(return_value=MagicMock()),
        ):
            gen = ConfigGenerator(populate=True)

        assert len(gen._gens) == 14

    def test_generate_calls_each_sub_generator(self) -> None:
        """generate() calls generate() on every sub-generator with conf and output_directory."""
        conf = ConfigurationData()

        with TemporaryDirectory() as tmpdir:
            # Build ConfigGenerator with a list of mocks
            gen = ConfigGenerator(populate=False)
            mock_generators = [MagicMock() for _ in range(3)]
            gen._gens = cast(List, mock_generators)

            gen.generate(conf, tmpdir)

        for mock_gen in mock_generators:
            mock_gen.generate.assert_called_once_with(conf, tmpdir, force=False)

    def test_generate_passes_force_flag_to_sub_generators(self) -> None:
        """generate(force=True) passes force=True to every sub-generator."""
        conf = ConfigurationData()

        with TemporaryDirectory() as tmpdir:
            gen = ConfigGenerator(populate=False)
            mock_gen = MagicMock()
            gen._gens = cast(List, [mock_gen])

            gen.generate(conf, tmpdir, force=True)

        mock_gen.generate.assert_called_once_with(conf, tmpdir, force=True)

    def test_generate_force_default_is_false(self) -> None:
        """generate() without explicit force defaults to force=False."""
        conf = ConfigurationData()

        with TemporaryDirectory() as tmpdir:
            gen = ConfigGenerator(populate=False)
            mock_gen = MagicMock()
            gen._gens = cast(List, [mock_gen])

            gen.generate(conf, tmpdir)

        mock_gen.generate.assert_called_once_with(conf, tmpdir, force=False)

    def test_generate_with_all_real_sub_generators_patched(self) -> None:
        """generate() with all real sub-generators patched calls each one once."""
        conf = ConfigurationData()

        with TemporaryDirectory() as tmpdir:
            mock_instances = {name.rsplit(".", maxsplit=1)[-1]: MagicMock() for name in _SUB_GENERATOR_NAMES}

            patches = {
                name.rsplit(".", maxsplit=1)[-1]: MagicMock(return_value=mock_instances[name.rsplit(".", maxsplit=1)[-1]]) for name in _SUB_GENERATOR_NAMES
            }

            with patch.multiple("smct.generation.config_generator", **patches):
                gen = ConfigGenerator(populate=True)
                gen.generate(conf, tmpdir)

            for instance in mock_instances.values():
                instance.generate.assert_called_once()

    def test_generate_empty_generator_list_does_not_raise(self) -> None:
        """generate() with no sub-generators completes without error."""
        conf = ConfigurationData()

        with TemporaryDirectory() as tmpdir:
            gen = ConfigGenerator(populate=False)

            gen.generate(conf, tmpdir)  # should not raise
