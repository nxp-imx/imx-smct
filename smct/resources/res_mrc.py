#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Module related to TRDC MRC resources"""
from typing import Any, Dict

from smct.expcetions.cfg_tool_exception import CfgToolException
from smct.generation.trdc.mrc_generation_model import MrcGenerationModel

from .res_trdc import MbcMrcResource


class MrcResource(MbcMrcResource):
    """MRC resource object"""

    def __init__(self, raw: Dict[str, Any]):
        super().__init__(raw)

        try:
            self._trdc_id: str = self["trdc"]
            self._mrc: int = self["mrc"]
            self._clr: int = MrcGenerationModel.DEFAULT_CLEARING
        except KeyError as exc:
            raise CfgToolException("Missing required MRC attributes in database object") from exc

    def set_clr(self, clr: int) -> None:
        """Sets clr of the MRC resource.

        Returns:
            int: The clr of the MRC resource..
        """
        self._clr = clr

    def get_clr(self) -> int:
        """Returns clr of the MRC resource.
        Returns:
            int: The clr of the MRC resource..
        """
        return self._clr

    def get_index(self) -> int:
        """Returns index of the MRC register.

        Returns:
            int: The index of the MRC register.
        """
        return self._mrc

    def get_start_register_name(self, domain: int, region: int) -> str:
        """Returns name of the start register.

        Args:
            domain (int): The domain number.
            region (int): The region number.

        Returns:
            str: The name of the start register.
        """
        return f"TRDC_{self._trdc_id}_MRC{self._mrc}_DOM{domain}_RGD{region}_W0"

    def get_end_register_name(self, domain: int, region: int) -> str:
        """Returns name of the end register.

        Args:
            domain (int): The domain number.
            region (int): The region number.

        Returns:
            str: The name of the end register.
        """
        return f"TRDC_{self._trdc_id}_MRC{self._mrc}_DOM{domain}_RGD{region}_W1"
