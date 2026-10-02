#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Unit tests for smct.resources.resource_base — gap coverage for AtomicResource and MacroResource.

The existing atomic_resource_test.py covers flat __getitem__, __contains__ True, get_name,
should_generate_test, get_atomic_resources, get_raw_json basic equality, rename, get_api_id
and get_start_stop_type raising CfgToolException.

The existing macro_resource_test.py covers get_name, is_empty, add/get_atomic_resource,
add/get_parameters, and get_assignment_parameters.

This file adds only the uncovered gaps identified in the session plan.
"""

from typing import Any, Dict

import pytest

from smct.configuration.configuration_provider import ConfigurationProvider
from smct.model.chip_model_provider import ChipModelProvider
from smct.resources.res_mdac import MdacResource
from smct.resources.resource_base import AtomicResource, MacroResource
from smct.resources.resource_database_provider import ResourceDatabaseProvider


@pytest.fixture(autouse=True)
def clear_providers() -> None:
    """Reset singleton providers around each test."""
    ConfigurationProvider.clear_configuration()
    ResourceDatabaseProvider.clear_database()
    ChipModelProvider.clear_model()


class TestAtomicResourceGaps:
    """Gap tests for AtomicResource not covered by atomic_resource_test.py."""

    def test_getitem_dot_notation_nested_access(self) -> None:
        """Test __getitem__ with dot-notation resolves nested dict keys."""
        raw: Dict[str, Any] = {
            "name": "NESTED",
            "type": "API",
            "outer": {"inner": 42},
        }
        atom = AtomicResource(raw)
        assert atom["outer.inner"] == 42

    def test_getitem_dot_notation_missing_key_raises(self) -> None:
        """Test __getitem__ with a non-existent nested key raises KeyError."""
        raw: Dict[str, Any] = {"name": "NESTED_MISS", "type": "API"}
        atom = AtomicResource(raw)
        with pytest.raises(KeyError):
            _ = atom["outer.inner"]

    def test_contains_returns_false_for_absent_key(self) -> None:
        """Test __contains__ returns False when the key is not in the raw dict."""
        raw: Dict[str, Any] = {"name": "ATOM", "type": "API"}
        atom = AtomicResource(raw)
        assert "nonexistent" not in atom

    def test_get_parameters_returns_empty_list(self) -> None:
        """Test that get_parameters returns an empty list by default."""
        raw: Dict[str, Any] = {"name": "ATOM", "type": "API"}
        atom = AtomicResource(raw)
        assert not atom.get_parameters()

    def test_get_assignment_parameters_returns_none(self) -> None:
        """Test that the base get_assignment_parameters always returns None."""
        raw: Dict[str, Any] = {"name": "ATOM", "type": "API"}
        atom = AtomicResource(raw)
        assert atom.get_assignment_parameters(["pa=1", "sa=bypass"]) is None

    def test_get_raw_json_deep_copy_independence(self) -> None:
        """Test that mutating the returned dict from get_raw_json does not affect the resource."""
        raw: Dict[str, Any] = {"name": "DEEP", "type": "API", "extra": "original"}
        atom = AtomicResource(raw)
        copy1 = atom.get_raw_json()
        copy1["extra"] = "mutated"
        copy2 = atom.get_raw_json()
        assert copy2["extra"] == "original"

    def test_contains_dot_notation_nested_true(self) -> None:
        """Test __contains__ returns True for a valid nested dot-notation key."""
        raw: Dict[str, Any] = {"name": "NEST", "type": "API", "a": {"b": 1}}
        atom = AtomicResource(raw)
        assert "a.b" in atom

    def test_contains_dot_notation_nested_false(self) -> None:
        """Test __contains__ returns False for an invalid nested dot-notation key."""
        raw: Dict[str, Any] = {"name": "NEST", "type": "API", "a": {"b": 1}}
        atom = AtomicResource(raw)
        assert "a.c" not in atom


class TestMacroResourceGaps:
    """Gap tests for MacroResource not covered by macro_resource_test.py."""

    def test_get_raw_json_shape_name_and_atoms_keys(self) -> None:
        """Test get_raw_json returns a dict with 'name' and 'atoms' keys."""
        macro = MacroResource("MY_MACRO")
        atom1 = AtomicResource({"name": "ATOM_A", "type": "API"})
        atom2 = AtomicResource({"name": "ATOM_B", "type": "API"})
        macro.add_atomic_resource(atom1)
        macro.add_atomic_resource(atom2)
        raw = macro.get_raw_json()
        assert raw["name"] == "MY_MACRO"
        assert raw["atoms"] == ["ATOM_A", "ATOM_B"]

    def test_get_raw_json_includes_params_when_present(self) -> None:
        """Test get_raw_json includes 'params' key only when parameters have been added."""
        macro = MacroResource("MACRO_WITH_PARAMS")
        macro.add_parameter("DFMT0")
        macro.add_parameter("DFMT1")
        raw = macro.get_raw_json()
        assert "params" in raw
        assert raw["params"] == ["DFMT0", "DFMT1"]

    def test_get_raw_json_no_params_key_when_empty(self) -> None:
        """Test get_raw_json omits 'params' key when no parameters have been added."""
        macro = MacroResource("MACRO_NO_PARAMS")
        raw = macro.get_raw_json()
        assert "params" not in raw

    def test_get_assignment_parameters_merged_from_two_atoms(self) -> None:
        """Test get_assignment_parameters merges results from multiple atoms.

        Uses one base AtomicResource (returns None) and one MdacResource (returns a
        real dict) to demonstrate that the merge actually requires both atoms: if the
        MdacResource were lost the macro would return None instead of the expected dict.
        """
        macro = MacroResource("MERGED")
        # atom1 is a base AtomicResource whose get_assignment_parameters always returns None
        atom1 = AtomicResource({"name": "BASE_ATOM", "type": "API"})
        # atom2 is an MdacResource whose get_assignment_parameters returns a real dict
        mdac = MdacResource({"name": "MDAC1", "type": "MDAC", "trdc": "A", "master": 1, "core": False})
        macro.add_atomic_resource(atom1)
        macro.add_atomic_resource(mdac)

        result = macro.get_assignment_parameters(["sa=5", "pa=2"])

        # Result must be non-None (contributed by mdac, not by atom1)
        assert result is not None
        assert result["sa"] == 5
        assert result["pa"] == 2

        # Confirm: a macro containing only atom1 (base AtomicResource) returns None
        # This shows the test would fail if the MdacResource atom were absent from the macro
        macro_without_mdac = MacroResource("WITHOUT_MDAC")
        macro_without_mdac.add_atomic_resource(atom1)
        assert macro_without_mdac.get_assignment_parameters(["sa=5", "pa=2"]) is None
