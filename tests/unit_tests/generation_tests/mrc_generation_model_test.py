#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
# pylint: disable=missing-module-docstring, missing-function-docstring

from typing import List

from smct.generation.trdc.mrc_generation_model import MrcGenerationModel
from smct.generation.trdc.mrc_region import MrcRegion
from smct.model.model_trdc import TrdcModel

# Initialize DEBUG_DOMAIN_PERMISSION (normally set by parser from chip model JSON)
TrdcModel.DEBUG_DOMAIN_PERMISSION = 0x6666


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


def test_add_region_same_permission_deduplicates() -> None:
    """Test that adding same region twice with same permission deduplicates (idempotent)"""
    # Arrange
    model = MrcGenerationModel(8)
    region1 = MrcRegion(1, 0x1000, 0x2000, 0x7777)
    region2 = MrcRegion(1, 0x1000, 0x2000, 0x7777)  # Same domain, range, permission
    # Act
    model.add_region(region1)
    model.add_region(region2)
    regions = model.get_regions()
    # Assert - With dedup logic: same permission at same location → deduplicate (only one stored)
    assert len(regions[1]) == 1
    assert regions[1][0].get_permission() == 0x7777


def test_add_region_different_permission_or_merged() -> None:
    """Test that adding same region with different permission ORs them together"""
    # Arrange
    model = MrcGenerationModel(8)
    region1 = MrcRegion(2, 0x1000, 0x2000, 0x6600)
    region2 = MrcRegion(2, 0x1000, 0x2000, 0x4400)  # Same domain, range but DIFFERENT permission
    # Act
    model.add_region(region1)
    model.add_region(region2)
    regions = model.get_regions()
    # Assert - permissions are OR'd together (matching Perl |= behavior)
    assert len(regions[2]) == 1
    assert regions[2][0].get_permission() == 0x6600 | 0x4400


def test_add_region_clearing_behavior_unchanged() -> None:
    """Test that clearing region behavior is preserved (dom_clearing vs non-clearing logic)"""
    # Arrange
    model = MrcGenerationModel(8)
    # Create a real region and a dom_clearing region
    real_region = MrcRegion(3, 0x1000, 0x2000, 0x7700, clearing=False)
    clearing_region = MrcRegion(3, 0x1000, 0x2000, 0x0, clearing=True)
    # Act & Assert - clearing region added first, then real region should replace it
    model.add_region(clearing_region)
    assert len(model.get_regions()[3]) == 1
    model.add_region(real_region)
    assert len(model.get_regions()[3]) == 1
    assert model.get_regions()[3][0] == real_region
    # Act & Assert - real region first, then clearing region should be ignored
    model2 = MrcGenerationModel(8)
    model2.add_region(real_region)
    assert len(model2.get_regions()[3]) == 1
    model2.add_region(clearing_region)
    assert len(model2.get_regions()[3]) == 1
    assert model2.get_regions()[3][0] == real_region


def test_add_region_different_range_no_dedup() -> None:
    """Test that adding regions with different ranges keeps both (no deduplication)"""
    # Arrange
    model = MrcGenerationModel(8)
    region1 = MrcRegion(4, 0x1000, 0x2000, 0x7777)
    region2 = MrcRegion(4, 0x3000, 0x4000, 0x7777)  # Same domain, permission, but DIFFERENT range
    # Act
    model.add_region(region1)
    model.add_region(region2)
    regions = model.get_regions()
    # Assert - Different ranges → both regions kept (no overlap, no dedup)
    assert len(regions[4]) == 2
    assert region1 in regions[4]
    assert region2 in regions[4]


def test_add_region_debug_domain_no_dedup() -> None:
    """Test that debug domain regions are NOT deduplicated (Perl parity)"""
    # Arrange
    model = MrcGenerationModel(8)
    region1 = MrcRegion(9, 0x08600000, 0x089FFFFF, TrdcModel.DEBUG_DOMAIN_PERMISSION)
    region2 = MrcRegion(9, 0x08600000, 0x089FFFFF, TrdcModel.DEBUG_DOMAIN_PERMISSION)  # Same domain, range, permission (debug)
    # Act
    model.add_region(region1)
    model.add_region(region2)
    regions = model.get_regions()
    # Assert - Debug domain regions must NOT be deduplicated (both kept for Perl parity)
    assert len(regions[9]) == 2
    assert region1 in regions[9]
    assert region2 in regions[9]
