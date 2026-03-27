#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause


from smct.owners.owner_dom import DOM


def test_dom_init_valid_parameters() -> None:
    """Test DOM initialization with valid parameters"""
    dom = DOM("dom1", 1)

    assert dom.get_id() == "dom1"
    assert dom.get_did() == 1
    assert dom.get_name() == "DOM1"
    assert not dom.is_debug()


def test_dom_set_name() -> None:
    """Test setting domain name"""
    dom = DOM("dom1", 1)
    dom.set_name("TestDomain")

    assert dom.get_name() == "TestDomain"


def test_dom_get_name_default() -> None:
    """Test getting default domain name when no name is set"""
    dom = DOM("dom1", 5)

    assert dom.get_name() == "DOM5"


def test_dom_set_debug_default() -> None:
    """Test setting debug flag with default parameter"""
    dom = DOM("dom1", 1)
    dom.set_debug()

    assert dom.is_debug()


def test_dom_set_debug_explicit() -> None:
    """Test setting debug flag with explicit parameter"""
    dom = DOM("dom1", 1)
    dom.set_debug(True)

    assert dom.is_debug()

    dom.set_debug(False)

    assert not dom.is_debug()


def test_dom_get_assignment_json() -> None:
    """Test getting assignment JSON for DOM"""
    dom = DOM("dom1", 1)
    dom.set_name("TestDomain")
    dom.set_debug(True)

    json_data = dom.get_assignment_json()

    assert json_data["type"] == "DOM"
    assert json_data["name"] == "TestDomain"
    assert json_data["did"] == 1
    assert json_data["debug"]
    assert json_data["resources"] == []


def test_dom_get_assignment_json_default_name() -> None:
    """Test getting assignment JSON for DOM with default name"""
    dom = DOM("dom2", 3)

    json_data = dom.get_assignment_json()

    assert json_data["type"] == "DOM"
    assert json_data["name"] == "DOM3"
    assert json_data["did"] == 3
    assert not json_data["debug"]


def test_dom_str() -> None:
    """Test string representation of DOM"""
    dom = DOM("dom1", 1)

    assert str(dom) == "dom1"


def test_dom_repr() -> None:
    """Test representation of DOM"""
    dom = DOM("dom1", 1)

    assert repr(dom) == "DOM('dom1', 1)"
