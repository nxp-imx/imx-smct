#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Module related to TRDC MDAC resources"""
from typing import Any, Dict, List

from smct import utils
from smct.expcetions.cfg_tool_exception import CfgToolException

from ..utils import FormatedInt
from .res_trdc import TrdcResource


class MdacResource(TrdcResource):
    """MDAC resource in TRDC"""

    def __init__(self, raw: Dict[str, Any]):
        super().__init__(raw)
        try:
            self._trdc_id: str = self["trdc"]
            self._master: int = self["master"]
            self._is_core: bool = self["core"]
            self._register: int = self["reg"] if "reg" in self else 0
            self._registers_count: int = self["rcnt"] if "rcnt" in self else 1
        except KeyError as exc:
            raise CfgToolException("Missing required MDAC attributes in database object") from exc

    def get_register(self) -> int:
        """Returns register.

        Returns:
            int: The register value.
        """
        return self._register

    def get_registers_count(self) -> int:
        """Returns number of registers.

        Returns:
            int: The number of registers.
        """
        return self._registers_count

    def get_master(self) -> int:
        """Returns master ID.

        Returns:
            int: The master ID.
        """
        return self._master

    def get_assignment_parameters(self, params: List[str]) -> Dict[str, Any]:
        """Taking CfgFile parameters from an assignment line (overridden).

        Args:
            params: List of parameter strings from assignment line.

        Returns:
            Dict[str, Any]: Dictionary containing parsed assignment parameters.
        """
        known = ["sa", "pa", "mdid", "sid", "kpa"]

        result = {}
        for key in known:
            val: Any = utils.get_attribute_value_from_list(params, key)
            try:
                if val is not None:
                    if key == "sid":
                        val = FormatedInt(val)
                    else:
                        val = utils.parse_int(val)
            except ValueError:
                pass
            if val is not None:
                result[key] = val

        return result

    def is_core(self) -> bool:
        """Returns TRUE when the MDAC assignment is done by core.

        Returns:
            bool: True if the MDAC assignment is done by core, False otherwise.
        """
        return self._is_core
