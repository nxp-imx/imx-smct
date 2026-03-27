#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause.
"""Unit tests for ResourceDb class"""

import json
from typing import Any, cast
from unittest.mock import Mock, mock_open, patch

from smct.exceptions.cfg_tool_exception import CfgToolException
from smct.resources.resdb import ResourceDb, ResourceDbException
from smct.resources.resource_base import AtomicResource, MacroResource


def test_init_creates_empty_database() -> None:
    """Test ResourceDb initialization creates empty collections"""
    db = ResourceDb()

    assert db.is_empty() is True
    assert db.macro_resources_list() == []


def test_is_empty_with_atomic_resources_only() -> None:
    """Test is_empty with only atomic resources"""
    db = ResourceDb()
    mock_atomic = Mock(spec=AtomicResource)
    mock_atomic.__getitem__ = Mock(side_effect=KeyError)
    mock_atomic.get_raw_json.return_value = {"name": "test", "type": "API"}

    db.add_atomic_resource(mock_atomic)
    assert db.is_empty() is True  # Still empty without macro resources


def test_is_empty_with_macro_resources() -> None:
    """Test is_empty returns False when macro resources exist"""
    db = ResourceDb()
    mock_atomic = Mock(spec=AtomicResource)
    mock_atomic.__getitem__ = Mock(side_effect=KeyError)
    mock_atomic.get_raw_json.return_value = {"name": "test", "type": "API"}

    mock_macro = Mock(spec=MacroResource)
    mock_macro.get_raw_json.return_value = {"name": "macro_test", "atoms": []}

    db.add_atomic_resource(mock_atomic)
    db.add_macro_resource(mock_macro)
    assert db.is_empty() is False


def test_add_atomic_resource() -> None:
    """Test adding atomic resources to database"""
    db = ResourceDb()
    mock_atomic = Mock(spec=AtomicResource)
    mock_atomic.__getitem__ = Mock(side_effect=KeyError)
    mock_atomic.get_raw_json.return_value = {"name": "test_resource", "type": "API"}

    db.add_atomic_resource(mock_atomic)

    atomic_list = list(db.atomic_resources())
    assert len(atomic_list) == 1
    assert mock_atomic in atomic_list


def test_add_macro_resource() -> None:
    """Test adding macro resources to database"""
    db = ResourceDb()
    mock_macro = Mock(spec=MacroResource)
    mock_macro.get_raw_json.return_value = {"name": "test_macro", "atoms": []}

    db.add_macro_resource(mock_macro)

    macro_list = list(db.macro_resources())
    assert len(macro_list) == 1
    assert mock_macro in macro_list


def test_add_user_resource() -> None:
    """Test adding user resources to database"""
    db = ResourceDb()
    mock_user_resource = Mock(spec=MacroResource)
    mock_user_resource.get_raw_json.return_value = {"name": "user_resource", "atoms": []}

    db.add_user_resource(mock_user_resource)

    macro_list = list(db.macro_resources())
    assert len(macro_list) == 1
    assert mock_user_resource in macro_list


def test_add_automatic_resource() -> None:
    """Test adding automatic resources to database"""
    db = ResourceDb()
    mock_auto_resource = Mock(spec=AtomicResource)
    mock_auto_resource.get_name.return_value = "auto_resource"
    mock_auto_resource.get_raw_json.return_value = {"name": "auto_resource", "type": "API"}
    mock_auto_resource.__getitem__ = Mock(side_effect=KeyError)

    db.add_automatic_resource(mock_auto_resource)

    atomic_list = list(db.atomic_resources())
    assert len(atomic_list) == 1
    assert mock_auto_resource in atomic_list


def test_find_atomic_resource_by_property() -> None:
    """Test finding atomic resources by property"""
    db = ResourceDb()
    mock_atomic1 = Mock(spec=AtomicResource)
    mock_atomic1.__getitem__ = Mock(return_value="API")
    mock_atomic1.get_raw_json.return_value = {"name": "resource1", "type": "API"}

    mock_atomic2 = Mock(spec=AtomicResource)
    mock_atomic2.__getitem__ = Mock(return_value="MBC")
    mock_atomic2.get_raw_json.return_value = {"name": "resource2", "type": "MBC"}

    db.add_atomic_resource(mock_atomic1)
    db.add_atomic_resource(mock_atomic2)

    api_resources = db.find_atomic_resource_by("type", "API")
    assert len(api_resources) == 1
    assert mock_atomic1 in api_resources

    mbc_resources = db.find_atomic_resource_by("type", "MBC")
    assert len(mbc_resources) == 1
    assert mock_atomic2 in mbc_resources

    # Test non-existent property value
    empty_result = db.find_atomic_resource_by("type", "NONEXISTENT")
    assert len(empty_result) == 0


def test_find_macro_resource() -> None:
    """Test finding macro resource by name"""
    db = ResourceDb()
    mock_macro1 = Mock(spec=MacroResource)
    mock_macro1.get_name.return_value = "macro1"
    mock_macro1.get_raw_json.return_value = {"name": "macro1", "atoms": []}

    mock_macro2 = Mock(spec=MacroResource)
    mock_macro2.get_name.return_value = "macro2"
    mock_macro2.get_raw_json.return_value = {"name": "macro2", "atoms": []}

    db.add_macro_resource(mock_macro1)
    db.add_user_resource(mock_macro2)

    found_macro1 = db.find_macro_resource("macro1")
    assert found_macro1 == mock_macro1

    found_macro2 = db.find_macro_resource("macro2")
    assert found_macro2 == mock_macro2

    not_found = db.find_macro_resource("nonexistent")
    assert not_found is None


def test_get_atomic_resources_json() -> None:
    """Test getting atomic resources as JSON"""
    db = ResourceDb()
    mock_atomic = Mock(spec=AtomicResource)
    mock_atomic.__getitem__ = Mock(return_value="API")
    mock_atomic.get_raw_json.return_value = {"name": "test_resource", "type": "API"}

    db.add_atomic_resource(mock_atomic)

    json_result = cast(dict[str, Any], db.get_atomic_resources_json())

    assert "AtomicResources" in json_result
    assert "API" in json_result["AtomicResources"]
    assert len(json_result["AtomicResources"]["API"]) == 1
    assert json_result["AtomicResources"]["API"][0]["name"] == "test_resource"


def test_get_macro_resources_json() -> None:
    """Test getting macro resources as JSON"""
    db = ResourceDb()
    mock_macro = Mock(spec=MacroResource)
    mock_macro.get_raw_json.return_value = {"name": "test_macro", "atoms": ["atom1"]}

    db.add_macro_resource(mock_macro)

    json_result = cast(dict[str, Any], db.get_macro_resources_json())

    assert "MacroResources" in json_result
    assert len(json_result["MacroResources"]) == 1
    assert json_result["MacroResources"][0]["name"] == "test_macro"


def test_get_user_resources_json() -> None:
    """Test getting user resources as JSON"""
    db = ResourceDb()
    mock_user_resource = Mock(spec=MacroResource)
    mock_user_resource.get_raw_json.return_value = {"name": "user_resource", "atoms": ["atom1"]}

    db.add_user_resource(mock_user_resource)

    json_result = db.get_user_resources_json()

    assert "UserResources" in json_result
    assert len(json_result["UserResources"]) == 1
    assert json_result["UserResources"][0]["name"] == "user_resource"


def test_get_automatic_resources_json() -> None:
    """Test getting automatic resources as JSON"""
    db = ResourceDb()
    mock_auto_resource = Mock(spec=AtomicResource)
    mock_auto_resource.get_name.return_value = "auto_resource"
    mock_auto_resource.get_raw_json.return_value = {"name": "auto_resource", "type": "API"}
    mock_auto_resource.__getitem__ = Mock(side_effect=KeyError)

    db.add_automatic_resource(mock_auto_resource)

    json_result = db.get_automatic_resources_json()

    assert "AutomaticResources" in json_result
    assert len(json_result["AutomaticResources"]) == 1
    assert json_result["AutomaticResources"][0]["name"] == "auto_resource"


@patch("builtins.open", new_callable=mock_open)
@patch("json.load")
@patch("os.path.join")
@patch("os.path.exists")
@patch("smct.utils.validate_json")
def test_load_from_json_success(mock_validate: Mock, mock_exists: Mock, mock_join: Mock, mock_json_load: Mock, mock_file: Mock) -> None:
    """Test successful loading from JSON files"""
    db = ResourceDb()

    # Mock os.path.exists to return True for all files
    mock_exists.return_value = True

    # Mock the validation to do nothing - this prevents validate_json from calling json.load
    mock_validate.return_value = None

    # Mock file paths
    mock_join.side_effect = lambda *args: "/".join(args)

    # Mock JSON data
    atomic_data = {"AtomicResources": {"API": [{"name": "test_api", "type": "API", "api": "DEV", "cat": "test"}]}}
    macro_data = {"MacroResources": [{"name": "test_macro", "atoms": ["test_api"]}]}
    user_data = {
        "AutomaticResources": [{"name": "auto_api", "type": "API", "api": "AUTO", "cat": "test"}],
        "UserResources": [{"name": "user_macro", "atoms": ["auto_api"]}],
    }

    # Only provide the data files, since validate_json is mocked and won't load schemas
    mock_json_load.side_effect = [atomic_data, macro_data, user_data]

    # Patch validate_json at the module level where it's imported in resdb.py
    with patch("smct.resources.resdb.validate_json") as mock_validate_resdb:
        mock_validate_resdb.return_value = None

        with patch("smct.resources.resfactory.atomic_resource_from_raw") as mock_factory:
            mock_atomic = Mock(spec=AtomicResource)
            mock_atomic.__getitem__ = Mock(side_effect=KeyError)
            mock_atomic.get_raw_json.return_value = {"name": "test_api", "type": "API"}
            mock_factory.return_value = mock_atomic

            with patch.object(db, "find_atomic_resource_by") as mock_find:
                mock_find.return_value = [mock_atomic]
                result = db.load_from_json("test_folder")
                assert result is True
                assert mock_file.call_count == 3  # Three files opened
                assert mock_json_load.call_count == 3
                assert mock_exists.call_count == 3  # Three files checked for existence


@patch("builtins.open", side_effect=FileNotFoundError)
def test_load_from_json_file_not_found(mock_file: Mock) -> None:
    """Test loading from JSON when file doesn't exist"""
    db = ResourceDb()

    assert db.load_from_json("nonexistent_folder") is False


@patch("builtins.open", new_callable=mock_open)
@patch("json.load", side_effect=json.JSONDecodeError("Invalid JSON", "", 0))
def test_load_from_json_invalid_json(mock_json_load: Mock, mock_file: Mock) -> None:
    """Test loading from JSON with invalid JSON content"""
    db = ResourceDb()

    assert db.load_from_json("test_folder") is False


def test_exception_with_message() -> None:
    """Test ResourceDbException with custom message"""
    message = "Test error message"
    exception = ResourceDbException(message)

    assert str(exception) == "SM CfgTool: SM DB: Test error message"
    assert isinstance(exception, CfgToolException)


def test_exception_with_empty_message() -> None:
    """Test ResourceDbException with empty message"""
    exception = ResourceDbException("")

    assert str(exception) == "SM CfgTool: SM DB: Unknown Exception"
