#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Unit tests for smct.smct CLI error handling and exception policy."""

import os
from tempfile import TemporaryDirectory
from typing import Any

import pytest

from smct.configuration.configuration_provider import ConfigurationProvider
from smct.exceptions.cfg_tool_exception import CfgToolException
from smct.model.chip_model_provider import ChipModelProvider
from smct.resources.resource_database_provider import ResourceDatabaseProvider
from smct.smct import _get_root_dir, AppErrorException, CATCHABLE_EXCEPTIONS
from tests.test_utils import execute_cli


@pytest.fixture(autouse=True)
def reset_providers() -> None:
    """Reset singleton providers before each test."""
    ConfigurationProvider.clear_configuration()
    ResourceDatabaseProvider.clear_database()
    ChipModelProvider.clear_model()


class TestAppErrorException:
    """Tests for application error formatting."""

    def test_message_with_text_is_prefixed(self) -> None:
        """Verify application errors include the SMCT application prefix."""
        error = AppErrorException("example failure")

        assert str(error) == "SM CfgTool Application: example failure"

    def test_message_without_text_contains_unknown_exception(self) -> None:
        """Verify empty application errors report an unknown exception."""
        error = AppErrorException("")

        assert "Unknown Exception" in str(error)
        assert str(error) == "SM CfgTool Application: Unknown Exception"


class TestMain:
    """Tests for CLI error handling."""

    def test_no_input_source_returns_error_code(self, capsys: Any) -> None:
        """Verify missing input or board is caught and returned as a CLI failure."""
        with TemporaryDirectory() as root_dir, TemporaryDirectory() as output_dir:
            os.makedirs(os.path.join(root_dir, "sm"))

            code, _, _ = execute_cli(capsys, ["--sm_dir", root_dir, "-o", output_dir])

        assert code == 1


class TestGetRootDir:
    """Tests for SM firmware root directory resolution."""

    def test_nonexistent_directory_raises_app_error(self) -> None:
        """Verify an explicit non-existent root directory is rejected."""
        with TemporaryDirectory() as root_dir:
            missing_dir = os.path.join(root_dir, "missing")

            with pytest.raises(AppErrorException):
                _get_root_dir(missing_dir)


class TestCatchableExceptions:
    """Tests for exception policy."""

    def test_tuple_contains_application_and_cfg_tool_exceptions(self) -> None:
        """Verify main catches application and recoverable cfg tool exceptions."""
        assert isinstance(CATCHABLE_EXCEPTIONS, tuple)
        assert AppErrorException in CATCHABLE_EXCEPTIONS
        assert CfgToolException in CATCHABLE_EXCEPTIONS
