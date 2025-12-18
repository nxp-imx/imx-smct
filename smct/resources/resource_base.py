#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Module related to resources"""
import copy
import typing
from typing import Any, Dict, List

from smct import utils
from smct.expcetions.cfg_tool_exception import CfgToolException


class AtomicResource:
    """Base class for all atomic resources"""

    # static properties
    _counter: int = 0

    def __init__(self, raw: Dict[str, Any]):
        """Initialize an AtomicResource instance.

        Args:
            raw: Original raw JSON object (the database item)
        """
        AtomicResource._counter += 1
        self._raw: Dict[str, Any] = raw  # original raw JSON object (the database item)
        try:
            self._name: str = self["name"]  # Name of the atomic resource
            self._type: str = self["type"]  # Type of the atomic resource - API,MBC,MRC,MDAC,...
            self._test: bool = False
            if "test" in self:
                self._test = utils.get_bool(self["test"])
            self._sema: int = -1
            if "sema" in self:
                self._sema = utils.parse_int(self["sema"])
        except KeyError as exc:
            raise CfgToolException("Missing required attributes in database object") from exc

    def __getitem__(self, key: str) -> Any:
        """Access to raw object values is possible using array subscript. Even more complex such as ["key.subkey"]

        Args:
            key: Key to access in the raw object, supports dot notation for nested keys

        Returns:
            The value associated with the key
        """
        try:
            key_parts = key.split(".")
            source: Dict[str, Any] = typing.cast(Dict[str, Any], self._raw)
            for part in key_parts:
                if part not in source:
                    raise KeyError()
                source = source[part]
            return source
        except KeyError as exc:
            raise KeyError(f"Key {key} is not valid for this object") from exc

    def __contains__(self, key: str) -> bool:
        """This helps caller to find out if a member is 'in' our _raw object.

        Args:
            key: Key to check for existence in the raw object

        Returns:
            True if the key exists, False otherwise
        """
        try:
            _ = self[key]
        except KeyError:
            return False
        return True

    def rename(self, new_name: str) -> None:
        """Renames the resource

        Args:
            new_name: New name for the resource
        """
        self._name = new_name
        self._raw["name"] = new_name

    def get_name(self) -> str:
        """Returns name of the atomic resource

        Returns:
            Name of the atomic resource
        """
        return self._name

    def get_atomic_resources(self) -> List["AtomicResource"]:
        """Returns list with this atomic resource

        Returns:
            List containing this atomic resource
        """
        return [self]

    def get_api_id(self) -> str | None:
        """Return identifier of the resource used in API calls (e.g. in LM start/stop)

        Returns:
            Identifier of the resource used in API calls
        """
        raise CfgToolException(f"Resource {self._name} cannot be used in Api calls")

    def get_start_stop_type(self) -> str | None:
        """Return identifier of the LMM_SS_ operation type

        Returns:
            Identifier of the LMM_SS_ operation type
        """
        raise CfgToolException(f"Resource {self._name} cannot be used in Start/Stop operations")

    def get_raw_json(self) -> Dict[str, Any]:
        """Returns the raw JSON representation of this atomic resource

        Returns:
            Deep copy of the raw JSON representation
        """
        raw = copy.deepcopy(self._raw)
        return raw

    def get_assignment_parameters(self, _: List[str]) -> Dict[str, Any] | None:
        """Taking configuration parameters from an assignment line (typically overridden)

        Args:
            _: List of parameters (unused in base implementation)

        Returns:
            Configuration parameters or None
        """
        return None

    def should_generate_test(self) -> bool:
        """Returns True when this resource should generate test

        Returns:
            True if this resource should generate test, False otherwise
        """
        return self._test

    def get_parameters(self) -> List[str]:
        """Returns list of parameters

        Returns:
            List of parameters
        """
        return []

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._raw})"


class MacroResource:
    """Representation of Macro resource. Contains names of multiple atomic resources of which this macro resource
    is made of."""

    def __init__(self, name: str):
        """Initialize a MacroResource instance.

        Args:
            name: Name of the macro resource
        """
        self._name: str = name  # Name of the macro resource
        self._atoms: List[AtomicResource] = []  # List of atomic resource names that make this macro resource
        self._params: List[str] = []  # additional parameters required by the macro itself (e.g. DFMT0/DFMT1)

    def get_name(self) -> str:
        """Returns name of the macro resource

        Returns:
            Name of the macro resource
        """
        return self._name

    def is_empty(self) -> bool:
        """Returns True when this maro resource is not made of any atomic resources

        Returns:
            True if this macro resource contains no atomic resources, False otherwise
        """
        return len(self._atoms) == 0

    def add_atomic_resource(self, atom: AtomicResource) -> None:
        """Adds atomic resource to this macro resource

        Args:
            atom: Atomic resource to add to this macro resource
        """
        self._atoms.append(atom)

    def add_parameter(self, param: str) -> None:
        """Adds assignment parameter to this macro resource

        Args:
            param: Parameter to add to this macro resource
        """
        self._params.append(param)

    def get_atomic_resources(self) -> List[AtomicResource]:
        """Returns list of all atomic resources

        Returns:
            List of all atomic resources in this macro resource
        """
        return self._atoms

    def get_assignment_parameters(self, params: List[str]) -> Dict[str, Any] | None:
        """Returns configuration parameters from an assignment

        Args:
            params: List of parameters to process

        Returns:
            Configuration parameters dictionary or None
        """
        result: Dict[str, Any] | None = None
        for atom in self._atoms:
            assignment = atom.get_assignment_parameters(params)
            if assignment is not None:
                if result is None:
                    result = {}
                result |= assignment
        return result

    def get_raw_json(self) -> Dict[str, Any]:
        """Returns raw JSON representation of this macro resource

        Returns:
            Raw JSON representation as a dictionary
        """
        raw: Dict[str, Any] = {"name": self._name}
        atom_names: List[str] = []
        for a in self._atoms:
            atom_names.append(a.get_name())
        raw["atoms"] = atom_names
        if len(self._params) != 0:
            raw["params"] = self._params.copy()
        return raw

    def get_parameters(self) -> List[str]:
        """Returns list of parameters

        Returns:
            List of parameters for this macro resource
        """
        return self._params

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._name})"
