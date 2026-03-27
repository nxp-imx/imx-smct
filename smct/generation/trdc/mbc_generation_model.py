#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause

"""Module related to MBC blocks generation model"""

import functools
import logging
from typing import Dict, List

from smct.generation.trdc.mbc_block import MbcBlock
from smct.model.model_trdc import TrdcModel

logger = logging.getLogger()


def _compare_blocks_legacy(block1: MbcBlock, block2: MbcBlock) -> int:
    """Compares two regions by start and end addresses

    Args:
        block1: First MBC block to compare
        block2: Second MBC block to compare

    Returns:
        int: -1 if block1 < block2, 0 if equal, 1 if block1 > block2
    """
    if block1.get_mbc() < block2.get_mbc():
        return -1
    if block1.get_mbc() == block2.get_mbc():
        if block1.get_domain() < block2.get_domain():
            return -1
        if block1.get_domain() == block2.get_domain():
            if block1.get_mem() < block2.get_mem():
                return -1
            if block1.get_mem() == block2.get_mem():
                block1_begin, _ = block1.get_block_range()
                block2_begin, _ = block2.get_block_range()
                if block1_begin < block2_begin:
                    return -1
                if block1_begin == block2_begin:
                    return 0
    return 1


class MbcGenerationModel:
    """Model for generation of MBC"""

    def __init__(self) -> None:
        self._blocks: Dict[int, List[MbcBlock]] = {}

    def add_block(self, block: MbcBlock) -> None:
        """Add block to the model

        Args:
            block: MBC block to add to the model
        """
        domain = block.get_domain()
        if domain not in self._blocks:
            self._blocks[domain] = []
        self._blocks[domain].append(block)

    def get_permissions(self) -> List[int]:
        """Returns permissions in order in which the regions are stored in the model

        Returns:
            List[int]: List of permissions for the regions
        """
        result = [0x0, TrdcModel.DEBUG_DOMAIN_PERMISSION, 0x7777]
        self.sort_blocks()
        for domain in sorted(self._blocks.keys()):
            for block in self._blocks[domain]:
                permission = block.get_permission()
                if permission >= 0 and permission not in result:
                    result.append(permission)
                if len(result) > 8:
                    source = "/".join(["user_config", block.get_name()])
                    validation_id = ".".join([f"DOM{domain}", "RESOURCES", block.get_name()])
                    logger.error("More than 8 distinct permissions present in one MBC", extra={"source": source, "validation_id": validation_id})
        return result

    def sort_blocks(self) -> None:
        """Sort the blocks in all domains"""
        for domain in self._blocks:
            self._blocks[domain].sort(key=functools.cmp_to_key(_compare_blocks_legacy))

    def get_blocks(self) -> Dict[int, List[MbcBlock]]:
        """Return list of all blocks in the MBC model

        Returns:
            Dict[int, List[MbcBlock]]: Dictionary mapping domain IDs to lists of MBC blocks
        """
        return self._blocks
