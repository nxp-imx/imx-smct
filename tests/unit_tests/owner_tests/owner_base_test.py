#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
# pylint: disable=protected-access, missing-module-docstring, missing-function-docstring

from unittest.mock import Mock

import pytest

from smct.owners.owner_base import AssignedDefine, ResourceOwner
from smct.resources.resource_base import AtomicResource, MacroResource


def test_resource_owner_init() -> None:
    owner = ResourceOwner("test_owner_id")
    assert owner.get_id() == "test_owner_id"
    assert not owner.get_owned_resources()
    assert not owner.get_assigned_resources()


def test_resource_owner_get_name() -> None:
    owner = ResourceOwner("test_owner_id")
    assert owner.get_name() == ""


def test_resource_owner_get_did_not_implemented() -> None:
    owner = ResourceOwner("test_owner_id")
    with pytest.raises(NotImplementedError):
        owner.get_did()


def test_resource_owner_assign_define() -> None:
    owner = ResourceOwner("test_owner_id")
    define = AssignedDefine("test_define", "param1=value1")

    owner.assign_define(define)

    assert owner.get_define("test_define") == define


def test_resource_owner_get_define_not_found() -> None:
    owner = ResourceOwner("test_owner_id")
    assert owner.get_define("nonexistent") is None


def test_resource_owner_assign_resource_new() -> None:
    owner = ResourceOwner("test_owner_id")
    mock_resource = Mock(spec=AtomicResource)
    mock_resource.get_assignment_parameters.return_value = {"param1": "value1"}

    result = owner.assign_resource(mock_resource, ["param1=value1"])

    assert result is not None
    assert len(owner.get_owned_resources()) == 1
    assert owner.get_owned_resources()[0].get_resource() == mock_resource


def test_resource_owner_assign_resource_denied() -> None:
    owner = ResourceOwner("test_owner_id")
    mock_resource = Mock(spec=AtomicResource)
    mock_resource.get_assignment_parameters.return_value = None

    result = owner.assign_resource(mock_resource, ["param1=value1"])

    assert result is None
    assert len(owner.get_owned_resources()) == 0


def test_resource_owner_assign_resource_combine_compatible() -> None:
    owner = ResourceOwner("test_owner_id")
    mock_resource = Mock(spec=AtomicResource)
    mock_resource.get_assignment_parameters.return_value = {"param1": "value1"}

    # First assignment
    result1 = owner.assign_resource(mock_resource, ["param1=value1"])

    # Second assignment with compatible parameters
    mock_resource.get_assignment_parameters.return_value = {"param2": "value2"}
    result2 = owner.assign_resource(mock_resource, ["param2=value2"])

    assert result1 == result2
    assert len(owner.get_owned_resources()) == 1


def test_resource_owner_assign_resource_with_defines() -> None:
    owner = ResourceOwner("test_owner_id")
    mock_resource = Mock(spec=AtomicResource)
    mock_resource.get_assignment_parameters.return_value = {"param1": "value1"}

    define = AssignedDefine("test_define", "param2=value2")
    expanded_defines = [define]

    result = owner.assign_resource(mock_resource, ["param1=value1"], expanded_defines)

    assert result is not None
    assert len(owner.get_owned_resources()) == 1


def test_resource_owner_get_assignment_json() -> None:
    owner = ResourceOwner("test_owner_id")
    mock_resource = Mock(spec=AtomicResource)
    mock_resource.get_assignment_parameters.return_value = {"param1": "value1"}

    # Add a define
    define = AssignedDefine("test_define", "param1=value1")
    owner.assign_define(define)

    # Add a resource
    owner.assign_resource(mock_resource, ["param1=value1"])

    json_data = owner.get_assignment_json()

    assert json_data["type"] == "ERROR"
    assert "defines" in json_data
    assert "resources" in json_data
    assert len(json_data["resources"]) == 1


def test_resource_owner_get_resource_assignments() -> None:
    owner = ResourceOwner("test_owner_id")
    mock_resource1 = Mock(spec=AtomicResource)
    mock_resource2 = Mock(spec=AtomicResource)

    mock_resource1.get_assignment_parameters.return_value = {"param1": "value1"}
    mock_resource2.get_assignment_parameters.return_value = {"param2": "value2"}

    owner.assign_resource(mock_resource1, ["param1=value1"])
    owner.assign_resource(mock_resource2, ["param2=value2"])
    owner.assign_resource(mock_resource1, ["param3=value3"])  # Same resource again

    assignments = owner._get_resource_assignments(mock_resource1)
    assert len(assignments) == 1  # Should be combined

    assignments = owner._get_resource_assignments(mock_resource2)
    assert len(assignments) == 1


def test_resource_owner_assign_resource_macro_resource() -> None:
    owner = ResourceOwner("test_owner_id")
    mock_macro_resource = Mock(spec=MacroResource)
    mock_macro_resource.get_assignment_parameters.return_value = {"param1": "value1"}

    result = owner.assign_resource(mock_macro_resource, ["param1=value1"])

    assert result is not None
    assert len(owner.get_owned_resources()) == 1
    assert owner.get_owned_resources()[0].get_resource() == mock_macro_resource


def test_assigned_define_getters_and_json_shape() -> None:
    define = AssignedDefine("FEATURE", "alpha=1 beta=two ignored")

    assert define.get_name() == "FEATURE"
    assert define.get_params() == {"alpha": "1", "beta": "two"}
    assert define.contains_param("alpha", "1") is True
    assert define.contains_param("alpha", "2") is False
    assert define.get_assignment_json() == {"name": "FEATURE", "params": {"alpha": "1", "beta": "two"}}


def test_resource_owner_assign_resource_conflicting_params_creates_second_assignment() -> None:
    owner = ResourceOwner("test_owner_id")
    mock_resource = Mock(spec=AtomicResource)
    mock_resource.get_assignment_parameters.side_effect = [{"mode": "secure"}, {"mode": "nonsecure"}]

    first = owner.assign_resource(mock_resource, ["mode=secure"])
    second = owner.assign_resource(mock_resource, ["mode=nonsecure"])

    assert first is not None
    assert second is not None
    assert first != second
    assert len(owner.get_owned_resources()) == 2
    assert owner._get_resource_assignments(mock_resource) == [first, second]


def test_resource_owner_assign_resource_multiple_defines_filters_json_params() -> None:
    owner = ResourceOwner("test_owner_id")
    mock_resource = Mock(spec=AtomicResource)
    mock_resource.get_name.return_value = "TEST_RESOURCE"
    mock_resource.get_assignment_parameters.return_value = {"alpha": "1", "beta": "2", "gamma": "3"}
    defines = [AssignedDefine("DEF_ALPHA", "alpha=1"), AssignedDefine("DEF_BETA", "beta=2")]

    assignment = owner.assign_resource(mock_resource, ["alpha=1", "beta=2", "gamma=3"], defines, dirty_flag=False)

    assert assignment is not None
    assert assignment.get_defines() == defines
    assert assignment.get_filtered_params() == {"gamma": "3"}
    assert assignment.get_assignment_json() == {
        "name": "TEST_RESOURCE",
        "defines": ["DEF_ALPHA", "DEF_BETA"],
        "params": {"gamma": "3"},
        "dirty_flag": False,
    }


def test_resource_owner_get_assigned_resources_matches_owned_resources() -> None:
    owner = ResourceOwner("test_owner_id")
    mock_resource = Mock(spec=AtomicResource)
    mock_resource.get_assignment_parameters.return_value = {"param": "value"}

    owner.assign_resource(mock_resource, ["param=value"])

    assert owner.get_assigned_resources() is owner.get_owned_resources()


def test_resource_owner_assign_define_replaces_existing_define() -> None:
    owner = ResourceOwner("test_owner_id")
    first = AssignedDefine("DUPLICATE", "value=old")
    replacement = AssignedDefine("DUPLICATE", "value=new")

    owner.assign_define(first)
    owner.assign_define(replacement)

    assert owner.get_define("DUPLICATE") == replacement
    assert owner.get_defines() == {"DUPLICATE": replacement}


def test_resource_owner_get_assignment_json_sorts_and_filters_defines() -> None:
    owner = ResourceOwner("test_owner_id")
    owner.set_name("TestOwner")
    owner.set_dirty_flag(False)
    owner.assign_define(AssignedDefine("ZDEF", "z=1"))
    owner.assign_define(AssignedDefine("EMPTY", "no_assignment"))
    owner.assign_define(AssignedDefine("DFMT1", "fmt=1"))
    owner.assign_define(AssignedDefine("DFMT0", "fmt=0"))

    json_data = owner.get_assignment_json()

    assert json_data["type"] == "ERROR"
    assert json_data["name"] == "TestOwner"
    assert json_data["dirty_flag"] is False
    assert json_data["defines"] == [
        {"name": "DFMT0", "params": {"fmt": "0"}},
        {"name": "DFMT1", "params": {"fmt": "1"}},
        {"name": "ZDEF", "params": {"z": "1"}},
    ]
