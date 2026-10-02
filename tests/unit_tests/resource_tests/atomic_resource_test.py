#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
# pylint: disable=missing-module-docstring, missing-function-docstring

import pytest

from smct.exceptions.cfg_tool_exception import CfgToolException
from smct.resources.resource_base import AtomicResource


def test_basic() -> None:
    attributes = {"name": "Lorem", "type": "API", "test": "True", "myAttr": 2}
    atom = AtomicResource(attributes)
    assert atom.get_name() == "Lorem"
    assert atom.should_generate_test()
    assert "myAttr" in atom
    assert atom["myAttr"] == 2
    assert atom.get_atomic_resources() == [atom]
    assert atom.get_raw_json() == attributes


def test_advanced() -> None:
    attributes = {"name": "Ipsum", "type": "MRC"}
    atom = AtomicResource(attributes)
    assert not atom.should_generate_test()
    assert atom.get_name() != "Lorem"
    atom.rename("Lorem")
    assert atom.get_name() == "Lorem"
    # Functions that are not implemented in the base class
    with pytest.raises(CfgToolException):
        atom.get_api_id()
    with pytest.raises(CfgToolException):
        atom.get_start_stop_type()
