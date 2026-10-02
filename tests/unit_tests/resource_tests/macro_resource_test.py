#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
# pylint: disable=missing-module-docstring, missing-function-docstring


from smct.resources.res_api import ApiResource
from smct.resources.resource_base import AtomicResource, MacroResource


def test_get_name() -> None:
    macro = MacroResource("Lorem")
    assert macro.get_name() == "Lorem"


def test_is_empty() -> None:
    macro = MacroResource("Lorem")
    atom = AtomicResource({"name": "Ipsum", "type": "API"})
    assert macro.is_empty()
    macro.add_atomic_resource(atom)
    assert not macro.is_empty()


def test_add_get_atomic_resource() -> None:
    macro = MacroResource("Lorem")
    atom_1 = AtomicResource({"name": "Ipsum", "type": "API"})
    atom_2 = AtomicResource({"name": "Dolor", "type": "API"})
    atoms = macro.get_atomic_resources()
    assert len(atoms) == 0
    assert atom_1 not in atoms
    assert atom_2 not in atoms
    macro.add_atomic_resource(atom_1)
    atoms = macro.get_atomic_resources()
    assert len(atoms) == 1
    assert atom_1 in atoms
    assert atom_2 not in atoms
    macro.add_atomic_resource(atom_2)
    atoms = macro.get_atomic_resources()
    assert len(atoms) == 2
    assert atom_1 in atoms
    assert atom_2 in atoms


def test_add_get_parameters() -> None:
    macro = MacroResource("Lorem")
    parameters = macro.get_parameters()
    assert len(parameters) == 0
    assert "DFMT0" not in parameters
    macro.add_parameter("DFMT0")
    parameters = macro.get_parameters()
    assert len(parameters) == 1
    assert "DFMT0" in parameters


def test_get_assignment_parameters() -> None:
    macro = MacroResource("Lorem")
    assignment_parameters = macro.get_assignment_parameters(["test"])
    assert assignment_parameters is None
    api_resource_1 = ApiResource({"name": "Ipsum", "type": "API", "cat": "DEV", "api": "CLK"})
    macro.add_atomic_resource(api_resource_1)
    assignment_parameters = macro.get_assignment_parameters(["test"])
    assert assignment_parameters is not None
    assert "test" in assignment_parameters
