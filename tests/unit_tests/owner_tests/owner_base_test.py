#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause

from unittest.mock import Mock

import pytest

from smct.owners.owner_base import AssignedDefine, ResourceOwner
from smct.resources.resource_base import AtomicResource, MacroResource


def test_resource_owner_init() -> None:
    owner = ResourceOwner("test_owner_id")
    assert owner.get_id() == "test_owner_id"
    assert owner.get_owned_resources() == []
    assert owner.get_assigned_resources() == []


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
