#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause

"""Module with base implementation of resource owner, assigned resource and assigned permissions"""

import logging
import typing
from typing import Any, Dict, List

from smct import utils
from smct.exceptions.cfg_tool_exception import CfgToolException
from smct.resources.res_api import ApiResource
from smct.resources.res_bctrl import BctrlResource
from smct.resources.res_trdc import TrdcResource
from smct.resources.resource_base import AtomicResource, MacroResource
from smct.utils import FormatedInt

logger = logging.getLogger()


class AssignedPermissions:
    """This class represents pair of: 'perm' and 'api' permissions"""

    def __init__(self, perm: str, api: str) -> None:
        self._perm: str = perm
        self._api: str = api
        self._name: str | None = None  # a short name of the pair (e.g. OWNER, READONLY, ...)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, AssignedPermissions):
            return False
        permission = typing.cast(AssignedPermissions, other)
        return self._perm == permission._perm and self._api == permission._api

    def set_name(self, name: str) -> None:
        """Sets name for this assigned permission.

        Args:
            name: The name to set for this assigned permission.
        """
        if self._name:
            source = "/".join(["user_config", "permission_templates", self._name])
            logger.warning("Renaming permission perm=%s, api=%s from '%s to %s", self._perm, self._api, self._name, name, extra={"source": source})
        self._name = name

    def get_name(self) -> str | None:
        """Returns name of this assigned permission. If none was set then returns name based on API and permission.

        Returns:
            The name of this assigned permission or a generated name based on API and permission.
        """
        name = self._name
        if not name:
            name = ""
            if self._perm:
                name += f"perm={self._perm} "
            if self._api:
                name += f"api={self._api} "
            name = name.strip()
            if not name:
                name = "NONE"
        return name

    def get_assignment_json(self) -> object:
        """Returns JSON object with raw data.

        Returns:
            JSON object containing the permission and API data.
        """
        ret = {}
        if self._perm:
            ret["perm"] = self._perm
        if self._api:
            ret["api"] = self._api
        return ret


class AssignedDefine:
    """This class represents user defined macro value"""

    def __init__(self, name: str, params: str):
        self._name = name
        self._params: Dict[str, str] = {}
        param_assignments = utils.parse_line_to_atoms(params)
        for assignment in param_assignments:
            if "=" in assignment:
                name, val = assignment.split("=")
                self._params[name] = val

    def get_assignment_json(self) -> object:
        """Returns JSON object with raw data.

        Returns:
            JSON object containing the name and parameters.
        """
        return {"name": self._name, "params": self._params}

    def get_name(self) -> str:
        """Returns name of this assigned define.

        Returns:
            The name of this assigned define.
        """
        return self._name

    def get_params(self) -> Dict[str, str]:
        """Returns params of this assigned define.

        Returns:
            Dictionary containing the parameters of this assigned define.
        """
        return self._params

    def contains_param(self, param_name: str, param_val: str) -> bool:
        """Returns whether this define contains param_name=param_val pair.

        Args:
            param_name: The parameter name to check.
            param_val: The parameter value to check.

        Returns:
            True if this define contains the specified parameter name-value pair, False otherwise.
        """
        return param_name in self._params and param_val == self._params[param_name]


class AssignedResource:
    """This class represents one atomic resource assigned to ResourceOwner with some parameters"""

    # dict of allowed LMM react types
    react_types: Dict[str, str]

    def __init__(self, owner: "ResourceOwner", res: AtomicResource | MacroResource):
        self._owner: "ResourceOwner" = owner
        self._res: AtomicResource | MacroResource = res
        self._params: Dict[str, Any] = {}
        self._defines: List[AssignedDefine] = []
        self._dirty_flag = True  # Flag to indicate if resource is changed in user configuration

    def get_params(self) -> Dict[str, Any]:
        """Returns parameters of this resource.

        Returns:
            Dictionary containing the parameters of this resource.
        """
        return self._params

    def get_defines(self) -> List[AssignedDefine]:
        """Returns list of assignment defines.

        Returns:
            List of AssignedDefine objects associated with this resource.
        """
        return self._defines

    def set_dirty_flag(self, dirty_flag: bool) -> None:
        """Sets the dirty flag for this resource.

        Args:
            dirty_flag: True if resource is changed in user configuration, False if defined elsewhere (device/xx system .cfg files).
        """
        self._dirty_flag = dirty_flag

    def is_dirty(self) -> bool:
        """Gets the dirty flag for this resource.

        Returns:
            True if resource is changed in user configuration, False if defined elsewhere (device/xx system .cfg files).
        """
        return self._dirty_flag

    def get_resource(self) -> AtomicResource | MacroResource:
        """Returns assigned resource.

        Returns:
            The assigned atomic or macro resource.
        """
        return self._res

    def get_param_value(self, key: str, default: Any = None, no_value: bool = False) -> Any:
        """Returns value of parameter with given name.

        Args:
            key: The parameter key to retrieve.
            default: The default value to return if key is not found.
            no_value: If True, return True when key exists regardless of value.

        Returns:
            The parameter value, default value, or True if no_value is True and key exists.
        """
        if key in self._params:
            if no_value:
                return True
            return self._params[key]
        return default

    def get_param_value_int(self, key: str, default: int = 0) -> int:
        """Returns integer value of parameter with given name.

        Args:
            key: The parameter key to retrieve.
            default: The default integer value to return if key is not found or cannot be converted.

        Returns:
            The parameter value as an integer or the default value.
        """
        value = self.get_param_value(key)
        if value is not None:
            if isinstance(value, int):
                return typing.cast(int, value)
            if isinstance(value, str):
                return utils.parse_int_or_default(value, default, True)
            if isinstance(value, FormatedInt):
                return value.get_value()
            source = "/".join(["user_config", self._owner.get_name(), self._res.get_name()])
            validation_id = ".".join([self._owner.get_id(), "RESOURCES", self._res.get_name()])
            logger.warning(
                "Key '%s' contains value '%s' that is neither int nor string and default value will be used",
                key,
                str(value),
                extra={"source": source, "validation_id": validation_id},
            )
        return default

    def get_atomic_resources(self) -> List[AtomicResource]:
        """Get our one (or more if macro) resource as a list.

        Returns:
            List of atomic resources.
        """
        if isinstance(self._res, AtomicResource):
            return [self._res]
        if isinstance(self._res, MacroResource):
            return self._res.get_atomic_resources()
        return []

    def get_fault_resources(self) -> List[ApiResource]:
        """Returns list of fault resources.

        Returns:
            List of API resources that are fault resources.
        """
        ret = []
        for r in self.get_atomic_resources():
            if isinstance(r, ApiResource) and r.is_fault():
                ret.append(r)
        return ret

    def get_cpu_resources(self) -> List[ApiResource]:
        """Returns list of CPU resources.

        Returns:
            List of API resources that are CPU resources.
        """
        ret = []
        for r in self.get_atomic_resources():
            if isinstance(r, ApiResource) and r.is_cpu():
                ret.append(r)
        return ret

    def get_bctrl_resources(self) -> List[BctrlResource]:
        """Returns list of block control resources.

        Returns:
            List of block control resources.
        """
        ret = []
        for r in self.get_atomic_resources():
            if isinstance(r, BctrlResource):
                ret.append(r)
        return ret

    def get_trdc_resources(self) -> List[TrdcResource]:
        """Returns list of all TRDC resources.

        Returns:
            List of TRDC resources.
        """
        ret = []
        for r in self.get_atomic_resources():
            if isinstance(r, TrdcResource):
                ret.append(r)
        return ret

    def can_combine(self, src: Dict[str, Any]) -> bool:
        """We can be combined if 'src' has all our keys the same. The 'src' may have its own new keys.

        Args:
            src: Dictionary of parameters to check for compatibility.

        Returns:
            True if the parameters can be combined, False otherwise.
        """
        dest = self._params
        for key in src:
            if key in dest:
                if dest[key] != src[key]:
                    return False
        return True

    def combine_with(self, src: Dict[str, Any]) -> bool:
        """Combine 'src' parameters into ours.

        Args:
            src: Dictionary of parameters to combine with current parameters.

        Returns:
            True if combination was successful.

        Raises:
            CfgToolException: If parameters cannot be combined due to conflicting values.
        """
        dest = self._params
        for key in src:
            if key in dest:
                if dest[key] != src[key]:
                    # should never happen if CanCombine was used by caller
                    raise CfgToolException("Cannot combine assignment keys")
            else:
                dest[key] = src[key]

        # all values same
        return True

    def get_assignment_json(self) -> object:
        """Returns JSON object with raw data.

        Returns:
            JSON object containing the resource assignment data.
        """
        self.get_filtered_params()
        ret = {
            "name": self._res.get_name(),
            "defines": [define.get_name() for define in self._defines],
            "params": self.get_filtered_params(),
            "dirty_flag": self._dirty_flag,
        }
        return ret

    def should_generate_test(self) -> bool:
        """Returns flag whether the resource should generate test. False if not set.

        Returns:
            True if the resource should generate test, False otherwise.
        """
        if "test" in self._params:
            return self._params["test"]
        return False

    def should_generate_debug(self) -> bool:
        """Returns True if the resource assignment should generate second assignment for debug domain.

        Returns:
            True if debug assignment should be generated, False otherwise.
        """
        if "nodbg" in self._params:
            return False
        return True

    def get_owner(self) -> "ResourceOwner":
        """Returns owner of this resource.

        Returns:
            The ResourceOwner that owns this resource.
        """
        return self._owner

    def set_params(self, params: Dict[str, Any]) -> None:
        """Sets parameters of this resource.

        Args:
            params: Dictionary of parameters to set for this resource.
        """
        self._params = params

    def get_permission_type(self) -> str | None:
        """Return identifier of the SM_SCMI_PERM_ permission type.

        Returns:
            The permission type identifier or None if not found or invalid.
        """
        if "api" in self._params:
            permission = self._params["api"]
            if permission in ApiResource.permission_types:
                return ApiResource.permission_types[permission]
            source = "/".join(["user_config", self._owner.get_name(), self._res.get_name()])
            validation_id = ".".join([self._owner.get_id(), "RESOURCES", self._res.get_name()])
            logger.error("Unknown SCMI permission type '%s'", permission, extra={"source": source, "validation_id": validation_id})
        return None

    def get_react_type(self) -> str | None:
        """Return identifier of the LMM_REACT_ operation type.

        Returns:
            The reaction type identifier or None if not found or invalid.
        """
        if "reaction" in self._params:
            reaction = self._params["reaction"]
            if reaction in self.react_types:
                return self.react_types[reaction]
            source = "/".join(["user_config", self._owner.get_name(), self._res.get_name()])
            validation_id = ".".join([self._owner.get_id(), "RESOURCES", self._res.get_name()])
            logger.error("Unknown LMM react type '%s'", reaction, extra={"source": source, "validation_id": validation_id})
        return None

    def set_defines(self, used_defines: List[AssignedDefine]) -> None:
        """Sets define to this resource.

        Args:
            used_defines: List of AssignedDefine objects to set for this resource.
        """
        self._defines = []
        for define in used_defines:
            params = define.get_params()
            if params:
                for name, val in params.items():
                    if name not in self._params:
                        self._params[name] = val
                self._defines.append(define)

    def get_filtered_params(self) -> Dict[str, str]:
        """Filters params that are already set in the defines.

        Returns:
            Dictionary of filtered parameters excluding those already defined in defines.
        """
        if self._params:
            filtered_params = self._params.copy()
            for name, val in self._params.items():
                for define in self._defines:
                    if define.contains_param(name, val):
                        filtered_params.pop(name)
            return filtered_params
        return {}


class ResourceOwner:
    """Base for DOM, LM or SCMI_AGENT which can hold assigned resources"""

    def __init__(self, owner_id: str):
        self._id: str = owner_id
        self._name: str = ""  # Will be set by subclasses
        self._resources: List[AssignedResource] = []
        self._defines: Dict[str, AssignedDefine] = {}
        self._dirty_flag = True  # Flag to indicate if resource is changed in user configuration

    def get_id(self) -> str:
        """Returns ID of the resource owner.

        Returns:
            The ID of the resource owner.
        """
        return self._id

    def get_name(self) -> str:
        """Returns name of the resource owner.

        Returns:
            The name of the resource owner.
        """
        return self._name

    def set_name(self, name: str) -> None:
        """Sets name of the resource owner.

        Args:
            The name of the resource owner
        """
        self._name = name

    def get_owned_resources(self) -> List[AssignedResource]:
        """Returns list of all assigned resources.

        Returns:
            List of all assigned resources.
        """
        return self._resources

    def get_did(self) -> int:
        """Returns domain ID. Must be overridden.

        Returns:
            The domain ID.

        Raises:
            NotImplementedError: This method must be overridden by subclasses.
        """
        raise NotImplementedError()

    def set_dirty_flag(self, dirty_flag: bool) -> None:
        """Set the dirty flag for this resource owner.

        Args:
            dirty_flag: True if resource owner is changed in user configuration, False if defined elsewhere (device/xx system .cfg files).
        """
        self._dirty_flag = dirty_flag

    def is_dirty(self) -> bool:
        """Get the dirty flag of this resource owner.

        Returns:
            True if resource owner is changed in user configuration, False if defined elsewhere (device/xx system .cfg files).
        """
        return self._dirty_flag

    def _get_resource_assignments(self, resource: AtomicResource | MacroResource) -> List[AssignedResource]:
        """Return list of assignments for given resource.

        Args:
            resource: The resource to find assignments for.

        Returns:
            List of AssignedResource objects for the given resource.
        """
        result = []
        for assignment in self._resources:
            if assignment.get_resource() == resource:
                result.append(assignment)
        return result

    def assign_resource(
        self,
        res: AtomicResource | MacroResource,
        params: List[str],
        expanded_defines: List[AssignedDefine] | None = None,
        dirty_flag: bool = True,
        ignore_api_check: bool = False,
    ) -> AssignedResource | None:
        """Base resource assignment coming from .cfg file, overridden by LM to handle specials.

        Args:
            res: The resource to assign.
            params: List of parameter strings for the assignment.
            expanded_defines: Optional list of expanded defines to apply.
            dirty_flag: True if resource owner is changed in user configuration, False if defined elsewhere.
            ignore_api_check: Whether to ignore API checks for automatic assignment.

        Returns:
            The AssignedResource object if successful, None if resource denied assignment.
        """

        # resource may deny assignment by returning None
        assr_params = res.get_assignment_parameters(params)
        automatic_api_assignment = isinstance(res, ApiResource) and ignore_api_check
        macro_with_automatic_api = (
            isinstance(res, MacroResource) and ignore_api_check and any(isinstance(atomic_res, ApiResource) for atomic_res in res.get_atomic_resources())
        )
        if assr_params is None:
            if isinstance(res, BctrlResource) or automatic_api_assignment or macro_with_automatic_api:
                assr_params = {}
            else:
                return None

        assr_ret = None

        # is the same resource already assigned?
        existing = self._get_resource_assignments(res)

        # all existing assignments must be compatible
        for e in existing:
            if e.can_combine(assr_params):
                e.combine_with(assr_params)
                assr_ret = e

        # was combined?
        if not assr_ret:
            assr_ret = AssignedResource(self, res)
            assr_ret.set_params(assr_params)
            if expanded_defines:
                assr_ret.set_defines(expanded_defines)
            assr_ret.set_dirty_flag(dirty_flag)
            self._resources.append(assr_ret)

        return assr_ret

    def assign_define(self, define: AssignedDefine) -> None:
        """Assigns define to the resource owner.

        Args:
            define: The AssignedDefine object to assign.
        """
        self._defines[define.get_name()] = define

    def get_assignment_json(self) -> Dict[str, Any]:
        """Returns JSON object with raw data.

        Returns:
            Dictionary containing the assignment data in JSON format.
        """
        # Filter defines that have params
        filtered_defines = [define for define in self._defines.values() if define.get_params()]

        # Sort defines: DFMT0 and DFMT1 first, then alphabetically
        sorted_defines = sorted(
            filtered_defines, key=lambda define: (0 if define.get_name() == "DFMT0" else 1 if define.get_name() == "DFMT1" else 2, define.get_name())
        )

        ret = {
            "type": "ERROR",  # will be filled by descendant
            "name": self._name,
            "defines": [define.get_assignment_json() for define in sorted_defines],
            "resources": [r.get_assignment_json() for r in self._resources],
            "dirty_flag": self._dirty_flag,
        }
        return ret

    def get_assigned_resources(self) -> List[AssignedResource]:
        """Returns list of all resources assigned to this owner.

        Returns:
            List of all AssignedResource objects assigned to this owner.
        """
        return self._resources

    def get_define(self, define_name: str) -> AssignedDefine | None:
        """Returns define of the resource owner, or None if it is not present.

        Args:
            define_name: The name of the define to retrieve.

        Returns:
            The AssignedDefine object if found, None otherwise.
        """
        if define_name in self._defines:
            return self._defines[define_name]
        return None

    def get_defines(self) -> Dict[str, AssignedDefine]:
        """Returns all our define names as a list"""
        return self._defines
