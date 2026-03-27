#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause

"""Module related to block control model"""

from typing import Dict, List, Optional

from smct.exceptions.cfg_tool_exception import CfgToolException


class BctrlModel:
    """Block control unit model"""

    def __init__(self, id_letter: str, name: Optional[str] = None) -> None:
        """Initialize BctrlModel instance.

        Args:
            id_letter: Single-letter identifier of the TRDC module
            name: Friendly name of the TRDC module. If None, defaults to "BCTRL_{id_letter}"

        Raises:
            CfgToolException: If id_letter is more than one character
        """
        if len(id_letter) > 1:
            raise CfgToolException(f"The '{id_letter} is invalid TRDC identifier, use single letter ID")

        # single-letter identifier of the TRDC module
        self._id_letter: str = id_letter
        # friendly name of the TRDC module
        self._name: str = name if name else f"BCTRL_{id_letter}"

        # IPG_DEBUG register offsets for each CPU (identified by CPU AtomicResource ID e.g. 'CPU_M33P')
        self._ipg_debug_offset: Dict[str, List[int | None]] = {}

    def __lt__(self, other: object) -> bool:
        return isinstance(other, BctrlModel) and self._id_letter < other._id_letter

    def __gt__(self, other: object) -> bool:
        return isinstance(other, BctrlModel) and self._id_letter > other._id_letter

    def get_name(self) -> str:
        """Gets name of the TRDC module.

        Returns:
            The name of the TRDC module
        """
        return self._name

    def get_letter_id(self) -> str:
        """Gets single-letter ID of the TRDC module.

        Returns:
            The single-letter identifier of the TRDC module
        """
        return self._id_letter

    def add_register_ipg_debug(self, cpu: str, regn: int, offset: int) -> None:
        """Assign IPG_DEBUG_x register to the BCTRL chip model.

        Args:
            cpu: CPU identifier (e.g. 'CPU_M33P')
            regn: Register number
            offset: Register offset value
        """
        if cpu not in self._ipg_debug_offset:
            self._ipg_debug_offset[cpu] = []
        offsets = self._ipg_debug_offset[cpu]
        while regn >= len(offsets):
            offsets.append(None)
        offsets[regn] = offset

    def get_cpu_offsets_ipg_debug(self, cpu_name: str) -> List[int | None] | None:
        """Returns list of CPU offsets for IPG DEBUG. Returns None if the cpu is not registered.

        Args:
            cpu_name: Name of the CPU to get offsets for

        Returns:
            List of CPU offsets for IPG DEBUG, or None if the CPU is not registered
        """
        if cpu_name in self._ipg_debug_offset:
            return self._ipg_debug_offset[cpu_name]
        return None

    def get_raw_json(self) -> object:
        """Returns JSON object with all data.

        Returns:
            JSON object containing all BCTRL model data
        """
        return {
            "bctrl": self._id_letter,
            "name": self._name,
            "regs": {"IPG_DEBUG": [{"cpu": cpu, "offset": off} for cpu, off in self._ipg_debug_offset.items()]},
        }
