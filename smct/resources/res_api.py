#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Module related to API resources"""
import logging
from typing import Any, Dict, List

from smct import utils
from smct.expcetions.cfg_tool_exception import CfgToolException

from ..utils import FormatedInt
from .resource_base import AtomicResource

logger = logging.getLogger()


class ApiResource(AtomicResource):
    """SCMI API resource"""

    # dict of allowed API permission assignment (syntax from .cfg file)
    start_stop_types: Dict[str, str]
    # dict of allowed SCMI permission types
    permission_types: Dict[str, str]

    def __init__(self, raw: Dict[str, Any]) -> None:
        super().__init__(raw)
        try:
            self._api: str = self["api"]  # API kind (PD,CLK,PIN,...)
            self._cat: str = self["cat"]  # DEV,BRD
            self._perm: str = f"{self._api.lower()}Perms"  # name of permsXxx array
        except KeyError as exc:
            raise CfgToolException("Missing required API attributes in database object") from exc

    def get_api_id(self) -> str | None:
        """Return identifier of the resource used in API calls.

        Returns:
            str | None: Identifier used in API calls (e.g. in LM start/stop), or None if resource does not have an array index.
        """
        if self._cat == "DEV":
            return f"DEV_SM_{self._name}"
        if self._cat == "BRD":
            return self._name
        if self._cat == "LMM":
            parts = self._name.split("_")
            if len(parts) != 2:
                raise CfgToolException(f"Cannot determine LMM API permission index for {self._name}")
            return parts[1]
        if self._cat == "BASE":
            return self._name
        return None  # this resource does not have an array index (e.g. SYS, FUSA, ...)

    def get_start_stop_type(self) -> str | None:
        """Return identifier of the LMM_SS_ operation type.

        Returns:
            str | None: LMM_SS_ operation type identifier, or None if invalid API resource type.
        """
        if self._api.lower() not in self.start_stop_types:
            source = "/".join(["user_config", "api_resource", self.get_name()])
            logger.error("Invalid API resource start stop type '%s'", self._api.lower(), extra={"source": source, "validation_id": self._name})
            return None
        return self.start_stop_types[self._api.lower()]

    def get_perms_member(self) -> str:
        """Returns the string with access to member of permission array.

        Returns:
            str: String with access to member of permission array.
        """
        memb = ""
        api_id = self.get_api_id()
        if api_id:
            memb = f"{self._perm}[{api_id}]"
        else:
            memb = self._perm
        return memb

    def is_cpu(self) -> bool:
        """Returns True if the permission is CPU permission.

        Returns:
            bool: True if the permission is CPU permission, False otherwise.
        """
        return self._perm == "cpuPerms"

    def is_fault(self) -> bool:
        """Returns True if the permission is FAULT permission.

        Returns:
            bool: True if the permission is FAULT permission, False otherwise.
        """
        return self._perm == "faultPerms"

    def set_auto(self, auto: bool = True) -> None:
        """Sets this resource as automatic.

        Args:
            auto: Whether to set the resource as automatic. Defaults to True.
        """
        self._raw["auto"] = auto

    def is_auto(self) -> bool:
        """Returns True when this resource is automatic.

        Returns:
            bool: True when this resource is automatic, False otherwise.
        """
        if "auto" in self._raw:
            return self._raw["auto"]
        return False

    def get_assignment_parameters(self, params: List[str]) -> Dict[str, Any] | None:
        """Taking CfgFile parameters from an assignment line (overridden).

        Args:
            params: List of parameters from an assignment line.

        Returns:
            Dict[str, Any] | None: Dictionary of assignment parameters, or None if no assignment should be made.
        """
        # do not assign if this API resource is automatic
        if self.is_auto():
            return None
        # we only care about api parameter
        api = utils.get_attribute_value_from_list(params, "api")
        test_auto = utils.contains_attribute_in_list(params, "test", no_value=True)
        test_explicit = utils.contains_attribute_in_list(params, "test")

        ret: Dict[str, Any] = {}
        if api:
            if api not in self.permission_types.keys():
                raise CfgToolException(f"Unknown API permission level '{api}'")
            ret["api"] = api

        # If test flag is present, then store it for later test generation
        if test_auto:
            ret["test"] = True
        elif test_explicit:
            ret["test"] = utils.get_bool(utils.get_attribute_value_from_list(params, "test"))

        if self.is_cpu():
            sema = utils.get_attribute_value_from_list(params, "sema")
            if sema is not None:
                ret["sema"] = FormatedInt(sema)

        # faults also care about reactions
        if self.is_fault():
            react = utils.get_attribute_value_from_list(params, "reaction")
            if not react:
                raise CfgToolException(f"Fault '{self.get_name()} needs a reaction defined")
            ret["reaction"] = react

            lm = utils.get_attribute_value_from_list(params, "lm")
            if lm:
                ret["lm"] = lm

        if not api and not (test_auto or test_explicit) and not ret:
            return None  # do not assign

        return ret
