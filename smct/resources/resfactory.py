#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause

"""Module with resource factory."""

from typing import Any, Dict

from smct.exceptions.cfg_tool_exception import CfgToolException
from smct.resources.res_api import ApiResource
from smct.resources.res_bctrl import BctrlResourceIpgDebug
from smct.resources.res_mbc import MbcResource
from smct.resources.res_mdac import MdacResource
from smct.resources.res_mrc import MrcResource
from smct.resources.resource_base import AtomicResource


def atomic_resource_from_raw(raw: Dict[str, Any]) -> AtomicResource:
    """Creates atomic resource object based on raw database specification.

    Args:
        raw: Dictionary containing raw database specification with resource type and configuration.

    Returns:
        AtomicResource: An atomic resource object of the appropriate type.

    Raises:
        CfgToolException: If the resource type is not recognized or missing from the raw specification.
    """
    factory = {
        "API": ApiResource,
        "MBC": MbcResource,
        "MRC": MrcResource,
        "MDAC": MdacResource,
        "BCTRL_IPG_DEBUG": BctrlResourceIpgDebug,
    }
    if "type" in raw and raw["type"] in factory:
        return factory[raw["type"]](raw)
    raise CfgToolException(f"Cannot recognize atomic resource definition record '{raw}'")
