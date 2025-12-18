#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
import pytest

from smct.expcetions.cfg_tool_exception import CfgToolException
from smct.resources.resfactory import atomic_resource_from_raw


def test_atomic_resource_from_raw_api():
    input_dictionary = {
        "type": "API",
        "name": "Lorem",
        "api": "DEV",
        "cat": "ipsum"
    }
    output = atomic_resource_from_raw(input_dictionary)
    assert repr(output) == f"ApiResource({input_dictionary})"


def test_atomic_resource_from_raw_api_invalid():
    input_dictionary = {
        "type": "API",
        "name": "Lorem",
        "cat": "ipsum"
    }
    with pytest.raises(CfgToolException):
        atomic_resource_from_raw(input_dictionary)


def test_atomic_resource_from_raw_mbc():
    input_dictionary = {
        "name": "MBC_TEST",
        "desc": "MBC_TEST=1.2",
        "type": "MBC",
        "trdc": "TRDC_TEST",
        "mbc": 0,
        "mem": 1,
        "blk": 2,
        "write_type": "block"
    }
    output = atomic_resource_from_raw(input_dictionary)
    assert repr(output) == f"MbcResource({input_dictionary})"


def test_atomic_resource_from_raw_mbc_invalid():
    input_dictionary = {
        "name": "MBC_TEST",
        "desc": "MBC_TEST=1.2",
        "type": "MBC",
        "trdc": "TRDC_TEST",
        "mbc": 0,
        "mem": 1,
        "blk": 2,
        "write_type": "block"
    }
    with pytest.raises(CfgToolException):
        copy = input_dictionary.copy()
        copy.pop("mbc")
        atomic_resource_from_raw(copy)
    with pytest.raises(CfgToolException):
        copy = input_dictionary.copy()
        copy.pop("mem")
        atomic_resource_from_raw(copy)
    with pytest.raises(CfgToolException):
        copy = input_dictionary.copy()
        copy.pop("trdc")
        atomic_resource_from_raw(copy)


def test_atomic_resource_from_raw_mrc():
    input_dictionary = {
        "name": "MRC_TEST",
        "desc": "MRC_TEST=0",
        "type": "MRC",
        "trdc": "TRDC_TEST",
        "mrc": 0
    }
    output = atomic_resource_from_raw(input_dictionary)
    assert repr(output) == f"MrcResource({input_dictionary})"


def test_atomic_resource_from_raw_mrc_invalid():
    input_dictionary = {
        "name": "MRC_TEST",
        "desc": "MRC_TEST=0",
        "type": "MRC",
        "trdc": "TRDC_TEST",
        "mrc": 0
    }
    with pytest.raises(CfgToolException):
        copy = input_dictionary.copy()
        copy.pop("mrc")
        atomic_resource_from_raw(copy)
    with pytest.raises(CfgToolException):
        copy = input_dictionary.copy()
        copy.pop("trdc")
        atomic_resource_from_raw(copy)


def test_atomic_resource_from_raw_mdac():
    input_dictionary = {
        "name": "MDAC_TEST",
        "desc": "MDAC_TEST=0-2",
        "type": "MDAC",
        "trdc": "TRDC_TEST",
        "master": 16,
        "core": 1,
        "reg": 0,
        "rcnt": 3
    }
    output = atomic_resource_from_raw(input_dictionary)
    assert repr(output) == f"MdacResource({input_dictionary})"


def test_atomic_resource_from_raw_mdac_invalid():
    input_dictionary = {
        "name": "MDAC_TEST",
        "desc": "MDAC_TEST=0-2",
        "type": "MDAC",
        "trdc": "TRDC_TEST",
        "master": 16,
        "core": 1,
        "reg": 0,
        "rcnt": 3
    }
    with pytest.raises(CfgToolException):
        copy = input_dictionary.copy()
        copy.pop("trdc")
        atomic_resource_from_raw(copy)
    with pytest.raises(CfgToolException):
        copy = input_dictionary.copy()
        copy.pop("master")
        atomic_resource_from_raw(copy)
    with pytest.raises(CfgToolException):
        copy = input_dictionary.copy()
        copy.pop("core")
        atomic_resource_from_raw(copy)


def test_atomic_resource_from_raw_ipg_debug():
    input_dictionary = {
        "name": "BCTRL_A_IPG_DEBUG_TEST",
        "desc": "BCTRL_A_IPG_DEBUG_TEST=0x2",
        "type": "BCTRL_IPG_DEBUG",
        "bctrl": "BCTRL_TEST",
        "regn": 0,
        "mask": "0x2"
    }
    output = atomic_resource_from_raw(input_dictionary)
    assert repr(output) == f"BctrlResourceIpgDebug({input_dictionary})"


def test_atomic_resource_from_raw_ipg_debug_invalid():
    input_dictionary = {
        "name": "BCTRL_A_IPG_DEBUG_TEST",
        "desc": "BCTRL_A_IPG_DEBUG_TEST=0x2",
        "type": "BCTRL_IPG_DEBUG",
        "bctrl": "BCTRL_TEST",
        "regn": 0,
        "mask": 2
    }
    with pytest.raises(CfgToolException):
        copy = input_dictionary.copy()
        copy.pop("regn")
        atomic_resource_from_raw(copy)
    with pytest.raises(CfgToolException):
        copy = input_dictionary.copy()
        copy.pop("mask")
        atomic_resource_from_raw(copy)

