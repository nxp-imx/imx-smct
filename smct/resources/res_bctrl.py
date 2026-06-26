#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause

"""Module related to BCTRL resources."""

from typing import Any, Dict

from smct.exceptions.cfg_tool_exception import CfgToolException

from ..utils import FormatedInt
from .resource_base import AtomicResource


class BctrlResource(AtomicResource):
    """Block control resource base class."""

    def __init__(self, raw: Dict[str, Any]):
        """Initialize BctrlResource.

        Args:
            raw: Dictionary containing raw resource data

        Raises:
            CfgToolException: If required BCTRL attributes are missing
        """
        super().__init__(raw)

        try:
            self._bctrl_id: str = self["bctrl"]
        except KeyError as exc:
            raise CfgToolException("Missing required BCTRL attributes in database object") from exc

    def get_bctrl_id(self) -> str:
        """Returns ID of the BCTRL that contains this resource.

        Returns:
            The BCTRL ID string
        """
        return self._bctrl_id


class BctrlResourceIpgDebug(BctrlResource):
    """Block control resource with IPG debug capabilities."""

    def __init__(self, raw: Dict[str, Any]):
        """Initialize BctrlResourceIpgDebug.

        Args:
            raw: Dictionary containing raw resource data

        Raises:
            CfgToolException: If required BCTRL IPG_DEBUG attributes are missing
        """
        super().__init__(raw)
        try:
            self._ipg_debug_regn: int = self["regn"]
            self._ipg_debug_mask: FormatedInt = FormatedInt(self["mask"])
        except KeyError as exc:
            raise CfgToolException("Missing required BCTRL IPG_DEBUG attributes in database object") from exc

    def get_ipg_debug_registers_count(self) -> int:
        """Returns number of IPG debug registers.

        Returns:
            The number of IPG debug registers
        """
        return self._ipg_debug_regn

    def get_ipg_debug_mask(self) -> FormatedInt:
        """Returns IPG debug mask.

        Returns:
            The IPG debug mask as FormatedInt
        """
        return self._ipg_debug_mask
