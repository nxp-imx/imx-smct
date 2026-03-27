#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
import pytest

from smct.exceptions.cfg_tool_exception import CfgToolException
from smct.resources.res_api import ApiResource
from tests import test_utils

API_RESOURCES = [
    ("LOREM", "CLK", "DEV", "DEV_SM_LOREM", "LMM_SS_CLK", "clkPerms[DEV_SM_LOREM]", False, False),
    ("IPSUM", "FAULT", "DEV", "DEV_SM_IPSUM", None, "faultPerms[DEV_SM_IPSUM]", False, True),
    ("IPSUM", "CPU", "DEV", "DEV_SM_IPSUM", "LMM_SS_CPU", "cpuPerms[DEV_SM_IPSUM]", True, False),
    ("LOREM", "CTRL", "BRD", "LOREM", "LMM_SS_CTRL", "ctrlPerms[LOREM]", False, False),
    ("LMM_1", "LMM", "LMM", "1", None, "lmmPerms[1]", False, False),
    ("LOREM", "BASE", "BASE", "DEV_SM_LOREM", None, "basePerms[DEV_SM_LOREM]", False, False),
    ("SYS", "SYS", "SYS", None, None, "sysPerms", False, False),
    ("FUSA", "FUSA", "FUSA", None, None, "fusaPerms", False, False),
]


def check_auto(api_resource: ApiResource, auto_by_default: bool = False) -> None:
    if not auto_by_default:
        assert not api_resource.is_auto()
        api_resource.set_auto(True)
    assert api_resource.is_auto()
    # Returns None in AUTO mode
    assert api_resource.get_assignment_parameters(["test", "perm=rw", "lorem", "ipsum=dolor"]) is None


@pytest.mark.parametrize("name, api, cat, expected_api_id, expected_start_stop, expected_perms, is_cpu, is_fault", API_RESOURCES)
def test_api_resource(
    name: str, api: str, cat: str, expected_api_id: str | None, expected_start_stop: str | None, expected_perms: str | None, is_cpu: bool, is_fault: bool
) -> None:
    test_utils.set_up()
    attributes = {"name": name, "type": "API", "api": api, "cat": cat}
    api_resource = ApiResource(attributes)
    assert api_resource.get_api_id() == expected_api_id
    assert api_resource.get_start_stop_type() == expected_start_stop
    assert api_resource.get_perms_member() == expected_perms
    assert api_resource.is_cpu() == is_cpu
    assert api_resource.is_fault() == is_fault
    if api_resource.is_fault():
        with pytest.raises(CfgToolException):
            result = api_resource.get_assignment_parameters(["api=priv", "test"])
        result = api_resource.get_assignment_parameters(["api=priv", "test", "reaction=none", "lm=0"])
        assert result == {"api": "priv", "test": True, "reaction": "none", "lm": "0"}
    else:
        result = api_resource.get_assignment_parameters(["api=priv", "test"])
        assert result == {"api": "priv", "test": True}

    # Test AUTO
    check_auto(api_resource)
