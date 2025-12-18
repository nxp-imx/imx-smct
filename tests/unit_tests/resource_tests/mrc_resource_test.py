#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
from smct.resources.res_mrc import MrcResource
from smct.utils import FormatedInt


def test_get_json():
    raw = {"name": "Lorem", "type": "MBC", "trdc": "A", "mrc": "0"}
    mbc = MrcResource(raw)
    expected_json = raw
    assert mbc.get_raw_json() == expected_json
    begin = FormatedInt(0xFF)
    size = FormatedInt(0xFF)
    mbc.add_default_permission(begin, size, (2, 12), "none", True)
    expected_json["default_permissions"] = []
    expected_json["default_permissions"].append({"begin": begin, "size": size, "domains": {"from": 2, "to": 12},
                                                "permission": "none"})
    mbc.add_default_permission(begin, size, (2, 12), "none", False)
    expected_json["default_permissions"].append({"begin": begin, "size": size, "domains": {"from": 2, "to": 12},
                                                "permission": "none", "no_debug": True})

    assert mbc.get_raw_json() == expected_json
    begin = FormatedInt(0xFFFF)
    mbc.add_default_permission(begin, size, (0, 1), "all", True)
    size2 = FormatedInt(0xF)
    mbc.add_default_permission(begin, size2, (13, 15), "all", True)
    expected_json["default_permissions"].append({"begin": begin, "size": size, "domains": {"from": 0, "to": 1},
                                                "permission": "all"})
    expected_json["default_permissions"].append({"begin": begin, "size": size2, "domains": {"from": 13, "to": 15},
                                                "permission": "all"})
    assert mbc.get_raw_json() == expected_json
