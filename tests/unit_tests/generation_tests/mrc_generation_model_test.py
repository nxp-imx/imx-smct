#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause

from typing import List

from smct.generation.trdc.mrc_generation_model import MrcGenerationModel
from smct.generation.trdc.mrc_region import MrcRegion
from smct.model.model_trdc import TrdcModel


def _lists_equals(input_list: List[int], expected_list: List[int]) -> bool:
    return set(input_list) == set(expected_list)


def test_basic() -> None:
    model = MrcGenerationModel(8)
    region = MrcRegion(0, 0, 15, 0x7777)
    region1 = MrcRegion(10, 0, 15, 0x7777)
    model.add_region(region)
    model.add_region(region1)
    regions = model.get_regions()
    # Test
    expected_regions = {0: [region], 10: [region1]}
    assert regions == expected_regions


def test_sorted() -> None:
    model = MrcGenerationModel(8)
    region0_1 = MrcRegion(0, 255, 65535, 0x7777)
    region0_2 = MrcRegion(0, 0, 15, 0x7777)
    region1_1 = MrcRegion(1, 0, 15, 0x7777)
    region1_2 = MrcRegion(1, 255, 65535, 0x7777)
    region2_1 = MrcRegion(2, 255, 65535, 0x7777)
    region2_2 = MrcRegion(2, 0, 15, 0x7777)
    region2_3 = MrcRegion(2, 0, 8, 0x7777)
    model.add_region(region0_1)
    model.add_region(region1_1)
    model.add_region(region2_1)
    model.add_region(region0_2)
    model.add_region(region1_2)
    model.add_region(region2_2)
    model.add_region(region2_3)
    model.sort_regions()
    regions = model.get_regions()
    # Test
    expected_regions = {0: [region0_2, region0_1], 1: [region1_1, region1_2], 2: [region2_2, region2_3, region2_1]}
    assert regions == expected_regions


def test_remove_unnecessary() -> None:
    model = MrcGenerationModel(8)
    region0_0 = MrcRegion(0, 0x0, 0xFFFF, 0x0)
    region1_0 = MrcRegion(1, 0x0, 0xFFFF, 0x0)
    region2_0 = MrcRegion(2, 0x0, 0xFFFF, 0x0)
    region3_0 = MrcRegion(3, 0x0, 0xFFFF, 0x0)
    region0_1 = MrcRegion(0, 0xFF, 0xFFFF, 0x7777)
    region0_2 = MrcRegion(0, 0x0, 0xF, 0x7777)
    model.add_region(region0_0)
    model.add_region(region1_0)
    model.add_region(region2_0)
    model.add_region(region3_0)
    model.add_region(region0_1)
    model.add_region(region0_2)
    model.remove_unnecessary_regions()
    regions = model.get_regions()
    # Test
    expected_regions = {0: [region0_1, region0_2], 1: [], 2: [], 3: []}
    assert regions == expected_regions


def test_get_permissions() -> None:
    model = MrcGenerationModel(8)
    region0_0 = MrcRegion(0, 0x0, 0xFFFF, 0x0)
    region1_0 = MrcRegion(1, 0x0, 0xFFFF, 0x0)
    region2_0 = MrcRegion(2, 0x0, 0xFFFF, 0x0)
    region3_0 = MrcRegion(3, 0x0, 0xFFFF, 0x0)
    region0_1 = MrcRegion(0, 0xFF, 0xFFFF, 0x6600)
    region0_2 = MrcRegion(0, 0x0, 0xF, 0x7777)
    model.add_region(region0_0)
    model.add_region(region1_0)
    model.add_region(region2_0)
    model.add_region(region3_0)
    model.add_region(region0_1)
    model.add_region(region0_2)
    assert _lists_equals(model.get_permissions(), [0x0, 0x6600, 0x7777])
    model.remove_unnecessary_regions()
    assert _lists_equals(model.get_permissions(), [0x6600, 0x7777])
    model.generate_debug_regions(9)
    assert _lists_equals(model.get_permissions(), [0x6600, 0x7777, TrdcModel.DEBUG_DOMAIN_PERMISSION])


def test_generate_debug_regions() -> None:
    debug_domain = 7
    model = MrcGenerationModel(8)
    region0_1 = MrcRegion(0, 0xFF, 0xFFFF, 0x6666)
    region1_1 = MrcRegion(1, 0x0, 0xF, 0x7777)
    region9_1 = MrcRegion(debug_domain, 0xFF, 0xFFFF, TrdcModel.DEBUG_DOMAIN_PERMISSION)
    region9_2 = MrcRegion(debug_domain, 0x0, 0xF, TrdcModel.DEBUG_DOMAIN_PERMISSION)
    model.add_region(region0_1)
    model.add_region(region1_1)
    model.generate_debug_regions(debug_domain)
    regions = model.get_regions()
    # Test
    expected_regions = {0: [region0_1], 1: [region1_1], debug_domain: [region9_1, region9_2]}
    assert regions == expected_regions


def test_generate_clearing() -> None:
    model = MrcGenerationModel(8)
    region0_0 = MrcRegion(0, 0x0, 0xFFFF, 0x0)
    region1_0 = MrcRegion(1, 0x0, 0xFFFF, 0x0)
    region2_0 = MrcRegion(2, 0x0, 0xFFFF, 0x0)
    region3_0 = MrcRegion(3, 0x0, 0xFFFF, 0x0)
    region0_1 = MrcRegion(0, 0xFF, 0xFFFF, 0x7777)
    region0_2 = MrcRegion(0, 0x0, 0xF, 0x7777)
    model.add_region(region0_0)
    model.add_region(region1_0)
    model.add_region(region2_0)
    model.add_region(region3_0)
    model.add_region(region0_1)
    model.add_region(region0_2)
    model.remove_unnecessary_regions()
    model.generate_clearing()
    regions = model.get_regions()
    # Test
    clearing_region0 = MrcRegion(0, 0, 0, -1)
    clearing_region1 = MrcRegion(1, 0, 0, -1)
    clearing_region2 = MrcRegion(2, 0, 0, -1)
    clearing_region3 = MrcRegion(3, 0, 0, -1)
    expected_regions = {
        0: [region0_1, region0_2, clearing_region0, clearing_region0],
        1: [clearing_region1, clearing_region1, clearing_region1, clearing_region1],
        2: [clearing_region2, clearing_region2, clearing_region2, clearing_region2],
        3: [clearing_region3, clearing_region3, clearing_region3, clearing_region3],
    }
    assert regions == expected_regions


def test_generate_larger_clearing() -> None:
    """Test MRC clearing generation with non-default clearing value."""
    # Arange
    model = MrcGenerationModel(8)
    region0 = MrcRegion(0, 0xFF, 0xFFFF, 0x7777)

    # Act
    model.add_region(region0)
    model.remove_unnecessary_regions()
    model.generate_clearing(6)
    regions = model.get_regions()

    # Assert
    clearing_region0 = MrcRegion(0, 0, 0, -1)
    expected_regions = {0: [region0, clearing_region0, clearing_region0, clearing_region0, clearing_region0, clearing_region0]}
    assert regions == expected_regions
