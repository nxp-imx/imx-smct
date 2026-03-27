#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause

from typing import List

from smct.generation.trdc.mbc_block import MbcBlock
from smct.generation.trdc.mbc_generation_model import MbcGenerationModel
from smct.model.model_trdc import TrdcModel
from smct.resources.res_mbc import MbcResource


def _lists_equals(input_list: List[int], expected_list: List[int]) -> bool:
    return set(input_list) == set(expected_list)


def test_basic() -> None:
    # Arrange
    model = MbcGenerationModel()
    raw1 = {"name": "Lorem", "type": "MBC", "trdc": "A", "mbc": "0", "mem": "0", "blk": "42", "bcnt": "2"}
    res1 = MbcResource(raw1)
    block1 = MbcBlock(1, res1, (42, 44), 0x4400)
    raw2 = {"name": "Ipsum", "type": "MBC", "trdc": "A", "mbc": "0", "mem": "1", "blk": "2", "bcnt": "2"}
    res2 = MbcResource(raw2)
    block2 = MbcBlock(5, res2, (2, 4), 0x6660)
    # Act
    model.add_block(block1)
    model.add_block(block2)
    blocks = model.get_blocks()
    # Assert
    expected_blocks = {1: [block1], 5: [block2]}
    assert blocks == expected_blocks


def test_get_permissions() -> None:
    # Arrange
    model = MbcGenerationModel()
    raw1 = {"name": "Lorem", "type": "MBC", "trdc": "A", "mbc": "0", "mem": "0", "blk": "0", "bcnt": "32"}
    res1 = MbcResource(raw1)
    block1 = MbcBlock(1, res1, (0, 32), 0x4400)
    raw2 = {"name": "Ipsum", "type": "MBC", "trdc": "A", "mbc": "0", "mem": "0", "blk": "0", "bcnt": "32"}
    res2 = MbcResource(raw2)
    block2 = MbcBlock(10, res2, (0, 32), 0x6600)
    raw3 = {"name": "Lorem", "type": "MBC", "trdc": "A", "mbc": "0", "mem": "0", "blk": "0", "bcnt": "32"}
    res3 = MbcResource(raw3)
    block3 = MbcBlock(2, res3, (0, 32), 0x7700)
    raw4 = {"name": "Ipsum", "type": "MBC", "trdc": "A", "mbc": "0", "mem": "1", "blk": "0", "bcnt": "32"}
    res4 = MbcResource(raw4)
    block4 = MbcBlock(3, res4, (0, 32), 0x6660)
    # Act
    model.add_block(block1)
    model.add_block(block2)
    model.add_block(block3)
    model.add_block(block4)
    # Assert
    expected_perms = [0x0, TrdcModel.DEBUG_DOMAIN_PERMISSION, 0x7777, 0x4400, 0x7700, 0x6660, 0x6600]
    assert _lists_equals(model.get_permissions(), expected_perms)


def test_sort_blocks() -> None:
    # Arrange
    model = MbcGenerationModel()
    raw1 = {"name": "Lorem", "type": "MBC", "trdc": "A", "mbc": "0", "mem": "0", "blk": "10", "bcnt": "22"}
    res1 = MbcResource(raw1)
    block1 = MbcBlock(1, res1, (10, 22), 0x4400)
    raw2 = {"name": "Ipsum", "type": "MBC", "trdc": "A", "mbc": "0", "mem": "0", "blk": "0", "bcnt": "32"}
    res2 = MbcResource(raw2)
    block2 = MbcBlock(1, res2, (0, 32), 0x6600)
    raw3 = {"name": "Lorem", "type": "MBC", "trdc": "A", "mbc": "0", "mem": "1", "blk": "0", "bcnt": "32"}
    res3 = MbcResource(raw3)
    block3 = MbcBlock(2, res3, (0, 32), 0x7700)
    raw4 = {"name": "Ipsum", "type": "MBC", "trdc": "A", "mbc": "0", "mem": "0", "blk": "0", "bcnt": "32"}
    res4 = MbcResource(raw4)
    block4 = MbcBlock(2, res4, (0, 32), 0x6660)
    # Act
    model.add_block(block1)
    model.add_block(block2)
    model.add_block(block3)
    model.add_block(block4)
    # Assert
    expected_blocks = {1: [block1, block2], 2: [block3, block4]}
    blocks = model.get_blocks()
    assert blocks == expected_blocks

    model.sort_blocks()
    expected_blocks = {1: [block2, block1], 2: [block4, block3]}
    blocks = model.get_blocks()
    assert blocks == expected_blocks
