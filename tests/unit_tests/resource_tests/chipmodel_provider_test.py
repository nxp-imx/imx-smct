#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause

from typing import Any, Dict, List

from smct.model.chip_model_provider import ChipModelProvider
from smct.model.model_chip import ChipModelImx9


def test_identity() -> None:
    instance = ChipModelProvider.get_model()
    assert isinstance(instance, ChipModelImx9)
    instance2 = ChipModelProvider.get_model()
    assert instance == instance2


def test_clear_model() -> None:
    ChipModelProvider.clear_model()
    model = ChipModelProvider.get_model()
    original_id = id(model)
    assert isinstance(model, ChipModelImx9)

    # Create a simple test JSON structure that matches the expected format
    test_json: Dict[str, Any] = {
        "TRDCs": [
            {
                "trdc": "A",
                "name": "TRDC_A",
                "ndid": 16,
                "nmbc": 1,
                "nmrc": 1,
                "nmstr": 5,
                "kpaen": 1,
                "sidsz": 6,
                "MBCs": [{"mbc": 0, "mem": [{"origin": "0x201c0000", "nblks": 32, "blksize": 8192}, {}, {}, {}]}],
                "MRCs": [{"mrc": 0, "nrgns": 8, "memory_region_offset": 14}],
            }
        ],
        "BCTRLs": [{"bctrl": "A", "name": "BCTRL_A", "regs": {"IPG_DEBUG": [{"cpu": "CPU_M33P", "offset": [8]}]}}],
        "Mixes": ["CAMERA", "DDR"],
    }

    # Parse the JSON data using the model's internal parsing methods
    model._parse_trdcs(test_json["TRDCs"])
    model._parse_block_controls(test_json["BCTRLs"])
    mixes: List[str] = test_json["Mixes"]
    for mix in mixes:
        model.add_mix(mix)

    # Verify the data was loaded
    assert len(model.get_all_trdcs()) > 0
    assert len(model.get_all_bctrls()) > 0
    assert len(model.get_mixes()) > 0

    model2 = ChipModelProvider.get_model()
    assert id(model2) == original_id

    ChipModelProvider.clear_model()
    model3 = ChipModelProvider.get_model()
    assert isinstance(model3, ChipModelImx9)
    assert id(model3) != original_id

    # Verify the new model is clean
    assert len(model3.get_all_trdcs()) == 0
    assert len(model3.get_all_bctrls()) == 0
    assert len(model3.get_mixes()) == 0
