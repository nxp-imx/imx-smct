#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Unit tests for smct.resources.resdump module-level functions.

All three provider singletons are patched where they are imported into
smct.resources.resdump so that no real database, chip model, or
configuration is required.
"""

import json
import os
import tempfile
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

from smct.configuration.configuration_provider import ConfigurationProvider
from smct.model.chip_model_provider import ChipModelProvider
from smct.resources.resdump import dump_configuration, generate_database
from smct.resources.resource_database_provider import ResourceDatabaseProvider


@pytest.fixture(autouse=True)
def clear_providers() -> None:
    """Reset singleton providers around each test."""
    ConfigurationProvider.clear_configuration()
    ResourceDatabaseProvider.clear_database()
    ChipModelProvider.clear_model()


_ATOMIC_JSON: Dict[str, Any] = {"AtomicResources": {"API": []}}
_MACRO_JSON: Dict[str, Any] = {"MacroResources": []}
_CHIP_JSON: Dict[str, Any] = {"TRDCs": {}, "BCTRLs": {}, "Mixes": []}
_CFG_JSON: Dict[str, Any] = {"assignments": []}


def _setup_database_mocks(mock_rdp: MagicMock, mock_cmp: MagicMock) -> None:
    """Configure mock return values for generate_database calls."""
    mock_rdp.get_database.return_value.get_atomic_resources_json.return_value = _ATOMIC_JSON
    mock_rdp.get_database.return_value.get_macro_resources_json.return_value = _MACRO_JSON
    mock_cmp.get_model.return_value.get_raw_json.return_value = _CHIP_JSON


class TestGenerateDatabase:
    """Tests for resdump.generate_database."""

    def test_creates_atomic_resources_json_file(self) -> None:
        """Test that generate_database writes atomic_resources.json to the output folder."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with (
                patch("smct.resources.resdump.ResourceDatabaseProvider") as mock_rdp,
                patch("smct.resources.resdump.ChipModelProvider") as mock_cmp,
            ):
                _setup_database_mocks(mock_rdp, mock_cmp)
                generate_database(tmpdir)
                assert os.path.isfile(os.path.join(tmpdir, "atomic_resources.json"))

    def test_creates_macro_resources_json_file(self) -> None:
        """Test that generate_database writes macro_resources.json to the output folder."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with (
                patch("smct.resources.resdump.ResourceDatabaseProvider") as mock_rdp,
                patch("smct.resources.resdump.ChipModelProvider") as mock_cmp,
            ):
                _setup_database_mocks(mock_rdp, mock_cmp)
                generate_database(tmpdir)
                assert os.path.isfile(os.path.join(tmpdir, "macro_resources.json"))

    def test_creates_chip_data_json_file(self) -> None:
        """Test that generate_database writes chip_data.json to the output folder."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with (
                patch("smct.resources.resdump.ResourceDatabaseProvider") as mock_rdp,
                patch("smct.resources.resdump.ChipModelProvider") as mock_cmp,
            ):
                _setup_database_mocks(mock_rdp, mock_cmp)
                generate_database(tmpdir)
                assert os.path.isfile(os.path.join(tmpdir, "chip_data.json"))

    def test_atomic_resources_file_is_valid_json(self) -> None:
        """Test that atomic_resources.json contains valid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with (
                patch("smct.resources.resdump.ResourceDatabaseProvider") as mock_rdp,
                patch("smct.resources.resdump.ChipModelProvider") as mock_cmp,
            ):
                _setup_database_mocks(mock_rdp, mock_cmp)
                generate_database(tmpdir)
                path = os.path.join(tmpdir, "atomic_resources.json")
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                assert "AtomicResources" in data

    def test_macro_resources_file_is_valid_json(self) -> None:
        """Test that macro_resources.json contains valid JSON with expected top-level key."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with (
                patch("smct.resources.resdump.ResourceDatabaseProvider") as mock_rdp,
                patch("smct.resources.resdump.ChipModelProvider") as mock_cmp,
            ):
                _setup_database_mocks(mock_rdp, mock_cmp)
                generate_database(tmpdir)
                path = os.path.join(tmpdir, "macro_resources.json")
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                assert "MacroResources" in data

    def test_chip_data_file_is_valid_json(self) -> None:
        """Test that chip_data.json contains valid JSON with expected top-level keys."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with (
                patch("smct.resources.resdump.ResourceDatabaseProvider") as mock_rdp,
                patch("smct.resources.resdump.ChipModelProvider") as mock_cmp,
            ):
                _setup_database_mocks(mock_rdp, mock_cmp)
                generate_database(tmpdir)
                path = os.path.join(tmpdir, "chip_data.json")
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                assert "TRDCs" in data
                assert "BCTRLs" in data


class TestDumpConfiguration:
    """Tests for resdump.dump_configuration."""

    def test_creates_user_configuration_json_file(self) -> None:
        """Test that dump_configuration writes user_configuration.json to the output folder."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("smct.resources.resdump.ConfigurationProvider") as mock_cp:
                mock_cp.get_configuration.return_value.get_assignment_json.return_value = _CFG_JSON
                dump_configuration(tmpdir)
                assert os.path.isfile(os.path.join(tmpdir, "user_configuration.json"))

    def test_user_configuration_file_is_valid_json(self) -> None:
        """Test that user_configuration.json contains valid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("smct.resources.resdump.ConfigurationProvider") as mock_cp:
                mock_cp.get_configuration.return_value.get_assignment_json.return_value = _CFG_JSON
                dump_configuration(tmpdir)
                path = os.path.join(tmpdir, "user_configuration.json")
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                assert "assignments" in data

    def test_dump_configuration_calls_get_assignment_json(self) -> None:
        """Test that dump_configuration calls get_assignment_json on the configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("smct.resources.resdump.ConfigurationProvider") as mock_cp:
                mock_cp.get_configuration.return_value.get_assignment_json.return_value = _CFG_JSON
                dump_configuration(tmpdir)
                mock_cp.get_configuration.return_value.get_assignment_json.assert_called_once()

    def test_dump_configuration_with_non_trivial_data(self) -> None:
        """Test dump_configuration preserves the data returned by get_assignment_json."""
        cfg_data: Dict[str, Any] = {"assignments": [{"resource": "CLK", "params": {"api": "default"}}]}
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("smct.resources.resdump.ConfigurationProvider") as mock_cp:
                mock_cp.get_configuration.return_value.get_assignment_json.return_value = cfg_data
                dump_configuration(tmpdir)
                path = os.path.join(tmpdir, "user_configuration.json")
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                assert data == cfg_data
