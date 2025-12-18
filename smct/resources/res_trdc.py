#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Module related to TRDC resources"""
import logging
from typing import Any, Dict, List, Tuple

from smct import utils
from smct.generation.trdc.mrc_generation_model import MrcGenerationModel
from smct.model.model_trdc import TrdcModel

from ..utils import FormatedInt, UInt64Constraints
from .default_permission import DefaultPermission
from .resource_base import AtomicResource

logger = logging.getLogger()


class TrdcResource(AtomicResource):
    """Base class for TRDC resources like MBC, MRC and MDAC"""

    def __init__(self, raw: Dict[str, Any]):
        super().__init__(raw)

        self._trdc_id: str = ""

    def get_trdc_id(self) -> str:
        """Returns ID of the TRDc that contains this resource

        Returns:
            str: The ID of the TRDC that contains this resource
        """
        return self._trdc_id


class MbcMrcResource(TrdcResource):
    """Base class for MBC and MRC - which are assignable with permissions"""

    def __init__(self, raw: Dict[str, Any]):
        super().__init__(raw)
        self._clr: int = MrcGenerationModel.DEFAULT_CLEARING
        self._default_permissions: List[DefaultPermission] = []

        if "default_permissions" in self:
            permissions = self["default_permissions"]
            for permission in permissions:
                if all(x in permission for x in ["begin", "size", "domains", "permission"]):
                    domains = permission["domains"]
                    did_tuple = None
                    if all(x in domains for x in ["from", "to"]):
                        did_tuple = (domains["from"], domains["to"])
                    if did_tuple is None:
                        source = "/".join(["model", "chip", "TRDC" + self.get_trdc_id(), "MBC" + str(raw["mbc"]), "MEM" + str(raw["mbc"]), self._name])
                        logger.warning("Domains of default permission require attributes 'from' and 'to'", extra={"source": source})
                        continue
                    generate_debug = "no_debug" not in permission or permission["no_debug"] is False
                    permission["begin"] = FormatedInt(permission["begin"]) if isinstance(permission["begin"], str) else (FormatedInt(str(permission["begin"])))
                    if permission["begin"].get_value() > UInt64Constraints.MAX_VALUE:
                        source = "/".join(["atomic_resources", self.get_name(), "default_permission", permissions.index(permission), "BEGIN"])
                        logger.error("Begin address %s exceeds maximum 64-bit value.", permission["begin"], extra={"source": source})
                        permission["begin"] = FormatedInt(UInt64Constraints.DEFAULT_VALUE)
                    permission["size"] = FormatedInt(permission["size"]) if isinstance(permission["size"], str) else (FormatedInt(str(permission["size"])))
                    if permission["size"].get_value() > UInt64Constraints.MAX_VALUE:
                        source = "/".join(["atomic_resources", self.get_name(), "default_permission", permissions.index(permission), "SIZE"])
                        logger.error("Size %s exceeds maximum 64-bit value.", permission["size"], extra={"source": source})
                        permission["size"] = FormatedInt(UInt64Constraints.DEFAULT_VALUE)
                    self.add_default_permission(permission["begin"], permission["size"], did_tuple, permission["permission"], generate_debug)
                else:
                    source = "/".join(["model", "chip", "TRDC" + self.get_trdc_id(), "MBC" + str(raw["mbc"]), "MEM" + str(raw["mbc"]), self._name])
                    logger.warning(
                        "Default permission of following resource must contain 'begin', 'size'," + " 'domains' and 'permission' element: %s",
                        raw,
                        extra={"source": source},
                    )

    def add_default_permission(self, begin: FormatedInt, size: FormatedInt, dids: Tuple[int, int], perm: str, should_generate_debug: bool) -> None:
        """Adds default permission configuration

        Args:
            begin (FormatedInt): The beginning address of the permission
            size (FormatedInt): The size of the permission region
            dids (Tuple[int, int]): Tuple containing the domain ID range (from, to)
            perm (str): The permission type
            should_generate_debug (bool): Whether to generate debug access
        """
        new_permission = DefaultPermission(begin, size, dids, perm, should_generate_debug)
        if new_permission not in self._default_permissions:
            self._default_permissions.append(new_permission)

    def get_default_permissions(self) -> List[DefaultPermission]:
        """Returns list of default permission objects

        Returns:
            List[DefaultPermission]: List of default permission objects
        """
        return self._default_permissions

    def get_assignment_parameters(self, params: List[str]) -> Dict[str, Any] | None:
        """Taking CfgFile parameters from an assignment line (overridden)

        Args:
            params (List[str]): List of parameter strings from assignment line

        Returns:
            Dict[str, Any] | None: Dictionary of assignment parameters or None if assignment should be prevented
        """
        # perm
        perm = utils.get_attribute_value_from_list(params, "perm")
        if not perm or perm not in TrdcModel.permission_types:
            source = "/".join(["model", "chip", "TRDC" + self.get_trdc_id(), self.get_name()])
            logger.error("A valid 'perm' permission needs to be defined for %s, but '%s' was given", self._name, perm, extra={"source": source})
            return None

        no_debug_access = utils.contains_attribute_in_list(params, "nodbg", no_value=True) or (
            utils.contains_attribute_in_list(params, "nodbg") and utils.get_bool(utils.get_attribute_value_from_list(params, "nodbg"))
        )
        begin_attr = utils.get_attribute_value_from_list(params, "begin")
        size = FormatedInt(0)
        begin = FormatedInt(begin_attr) if begin_attr else FormatedInt(0)
        if begin.get_value() > UInt64Constraints.MAX_VALUE:
            source = "/".join(["atomic_resources", self.get_name(), "default_permission", "BEGIN"])
            logger.error("Begin address %s exceeds maximum 64-bit value.", begin, extra={"source": source})
            begin = FormatedInt(UInt64Constraints.DEFAULT_VALUE)
        if begin_attr is not None:
            end_attr = utils.get_attribute_value_from_list(params, "end")
            end = utils.parse_int(end_attr) if end_attr else 0
            size_attr = utils.get_attribute_value_from_list(params, "size")
            size = FormatedInt(size_attr) if size_attr else FormatedInt(0)
            if end and not size_attr:
                if end < begin.get_value():
                    source = "/".join(["model", "chip", "TRDC" + self.get_trdc_id(), self.get_name()])
                    logger.error('Bad begin(%s)..end(%s) values defined for "%s"', str(begin), str(end), self.get_name(), extra={"source": source})
                else:
                    size = FormatedInt(end - begin.get_value() + 1)
            if size.get_value() > UInt64Constraints.MAX_VALUE:
                source = "/".join(["atomic_resources", self.get_name(), "default_permission", "SIZE"])
                logger.error("Size %s exceeds maximum 64-bit value.", size, extra={"source": source})
                size = FormatedInt(UInt64Constraints.DEFAULT_VALUE)
        did = utils.get_attribute_value_from_list(params, "did")
        if did:
            # using did, means overriding assignment and setting just default permissions
            dids = utils.parse_int_range(did)
            self.add_default_permission(begin, size, dids, perm, not no_debug_access)
            # prevent resource assignment, this was just default permission override
            return None

        result: Dict[str, Any] = {"perm": perm}
        if begin_attr is not None:
            result |= {"begin": begin, "size": size}
        clr = utils.get_attribute_value_from_list(params, "clr")
        if clr:
            self._clr = int(clr)
            result |= {"clr": clr}
        if no_debug_access:
            result |= {"nodbg": True}

        return result

    def get_raw_json(self) -> Dict[str, Any]:
        """Get the raw JSON representation of the resource

        Returns:
            Dict[str, Any]: Dictionary containing the raw JSON representation
        """
        result = super().get_raw_json()
        if len(self._default_permissions) > 0:
            result["default_permissions"] = []
            for default_permission in self._default_permissions:
                begin = default_permission.get_begin()
                size = default_permission.get_size()
                dids = default_permission.get_dids()
                perm = default_permission.get_permission()
                no_debug = not default_permission.should_generate_debug_access()
                did_begin, did_end = dids
                domain_range = {"from": did_begin, "to": did_end}
                obj = {"begin": begin, "size": size, "domains": domain_range, "permission": perm}
                if no_debug:
                    obj["no_debug"] = no_debug
                result["default_permissions"].append(obj)
        return result
