#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Unit tests for smct.smct CLI argument parsing and version handling."""

from typing import Any

import pytest

from smct.configuration.configuration_provider import ConfigurationProvider
from smct.model.chip_model_provider import ChipModelProvider
from smct.product_info import ProductInfo
from smct.resources.resource_database_provider import ResourceDatabaseProvider
from smct.smct import _parse_arguments
from tests.test_utils import execute_cli


@pytest.fixture(autouse=True)
def reset_providers() -> None:
    """Reset singleton providers before each test."""
    ConfigurationProvider.clear_configuration()
    ResourceDatabaseProvider.clear_database()
    ChipModelProvider.clear_model()


class TestMain:
    """Tests for simple CLI main paths."""

    @pytest.mark.parametrize("flag", ["--version", "-v"])
    def test_version_flag_prints_version(self, capsys: Any, flag: str) -> None:
        """Verify version flags print the product version and exit successfully."""
        code, stdout, stderr = execute_cli(capsys, [flag])

        assert code == 0
        assert ProductInfo.get_smct_version_string() in stdout
        assert stderr == ""

    def test_help_flag_raises_system_exit_zero(self, capsys: Any) -> None:
        """Verify argparse handles --help by raising SystemExit with code 0."""
        with pytest.raises(SystemExit) as exc_info:
            execute_cli(capsys, ["--help"])

        assert exc_info.value.code == 0

    def test_unknown_argument_raises_system_exit_nonzero(self, capsys: Any) -> None:
        """Verify argparse rejects unknown arguments with a non-zero exit."""
        with pytest.raises(SystemExit) as exc_info:
            execute_cli(capsys, ["--unknown-option"])

        assert exc_info.value.code != 0


class TestParseArguments:
    """Tests for direct argument parsing."""

    def test_parse_arguments_with_values_returns_expected_namespace(self) -> None:
        """Verify selected options are parsed into expected namespace attributes."""
        argv = _parse_arguments(["-f", "-c", "file.cfg", "-v"])

        assert argv.force is True
        assert argv.load_cfg == "file.cfg"
        assert argv.version is True

    def test_parse_arguments_without_values_returns_defaults(self) -> None:
        """Verify omitted boolean options default to False."""
        argv = _parse_arguments([])

        assert argv.version is False
        assert argv.force is False
        assert argv.load_cfg is None
