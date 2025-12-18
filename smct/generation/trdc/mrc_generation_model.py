#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Module related to MRC regions generation model"""
import functools
import logging
from typing import Dict, List

from smct.generation.trdc.mrc_region import MrcRegion
from smct.model.model_trdc import TrdcModel

logger = logging.getLogger()


def _compare_regions_legacy(region1: MrcRegion, region2: MrcRegion) -> int:
    """Compares two regions by start and end addresses

    Args:
        region1: First region to compare
        region2: Second region to compare

    Returns:
        -1 if region1 comes before region2, 0 if equal, 1 if region1 comes after region2
    """
    if str(region1.get_start_address()) < str(region2.get_start_address()):
        return -1
    if str(region1.get_start_address()) == str(region2.get_start_address()):
        if str(region1.get_end_address()) < str(region2.get_end_address()):
            return -1
        if str(region1.get_end_address()) == str(region2.get_end_address()):
            return 0
    return 1


class MrcGenerationModel:
    """Model for generation of MRC"""

    DEFAULT_CLEARING: int = 4

    def __init__(self, regions_count: int) -> None:
        """Initialize MrcGenerationModel

        Args:
            regions_count: Number of regions
        """
        self._regions: Dict[int, List[MrcRegion]] = {}
        self._regions_count = regions_count

    def add_region(self, region: MrcRegion) -> None:
        """Adds region to the model

        Args:
            region: The MRC region to add
        """
        domain = region.get_domain()
        if domain not in self._regions:
            self._regions[domain] = []
        self._regions[domain].append(region)

    def generate_clearing_in_domain(self, domain: int, amount: int) -> None:
        """Generates clearing of registers

        Args:
            amount: Amount of clearing to generate
        """
        need_to_generate = amount - len(self._regions[domain])
        if need_to_generate > 0:
            for _ in range(0, need_to_generate):
                self._regions[domain].append(MrcRegion(domain, 0, 0, -1))

    def generate_clearing(self, amount: int = DEFAULT_CLEARING) -> None:
        """Generates clearing of registers

        Args:
            amount: Amount of clearing to generate
        """
        amount = min(amount, self._regions_count)
        for domain in self._regions:
            self.generate_clearing_in_domain(domain, amount)

    def remove_unnecessary_regions(self) -> None:
        """Removes unnecessary regions. For example: Regions with permission 0"""
        for domain in self._regions:
            to_be_removed = []
            for region in self._regions[domain]:
                if region.get_permission() == 0:
                    to_be_removed.append(region)
            for region in to_be_removed:
                self._regions[domain].remove(region)

    def get_permissions(self) -> List[int]:
        """Returns permissions in order in which the regions are stored in the model

        Returns:
            List of permissions
        """
        result = []
        regions_sorted_by_string = dict(sorted(self._regions.items(), key=str))
        for domain in regions_sorted_by_string:
            for region in self._regions[domain]:
                permission = region.get_permission()
                if permission >= 0 and permission not in result:
                    result.append(permission)
        return result

    def generate_debug_regions(self, debug_domain: int) -> None:
        """Generates copy of all regions in all domains into debug domain

        Args:
            debug_domain: The debug domain to generate regions for
        """
        new_regions = []
        if debug_domain in self._regions and len(self._regions[debug_domain]) > 0:
            source = "/".join(["model", "chip", "TRDC", "MRC", "DOM" + str(debug_domain)])
            logger.error("MRC generation model already contains regions for debug domain %i", debug_domain, extra={"source": source})
            return
        for domain in self._regions:
            for region in self._regions[domain]:
                new_regions.append(MrcRegion(debug_domain, region.get_start_address(), region.get_end_address(), TrdcModel.DEBUG_DOMAIN_PERMISSION))
        if debug_domain not in self._regions:
            self._regions[debug_domain] = []
        for region in new_regions:
            self._regions[debug_domain].append(region)

    def get_regions(self) -> Dict[int, List[MrcRegion]]:
        """Returns list of all regions in the MRC model

        Returns:
            Dictionary mapping domain IDs to lists of MRC regions
        """
        return self._regions

    def sort_regions(self) -> None:
        """Sorts the regions in all domains"""
        for domain in self._regions:
            self._regions[domain].sort(key=functools.cmp_to_key(_compare_regions_legacy))
