#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause

"""Module with resource database."""

import json
import logging
import os
import typing
from typing import Any, Dict, Generator, List

from smct.exceptions.cfg_tool_exception import CfgToolException
from smct.owners.owner_base import AssignedDefine
from smct.resources.res_api import ApiResource
from smct.resources.resfactory import atomic_resource_from_raw
from smct.resources.resource_base import AtomicResource, MacroResource
from smct.utils import validate_json

logger = logging.getLogger()


class ResourceDbException(CfgToolException):
    """Exception used to indicate problem with resource database of the System manager config tool."""

    def __init__(self, message: str) -> None:
        if not message:
            message = "Unknown Exception"
        message = "SM DB: " + message
        super().__init__(message)


class ResourceDb:
    """Resource database that stores all atomic and macro resources."""

    def __init__(self) -> None:
        self._atomic_resources: List[AtomicResource] = []
        self._macro_resources: List[MacroResource] = []
        self._user_resources: List[MacroResource] = []
        self._automatic_resources: List[AtomicResource] = []
        self._defines: Dict[str, AssignedDefine] = {}
        # indexes for each "key". An index is a dictionary of key "value"->"List" of objects whose [key]==value
        self._indexes: Dict[str, Dict[Any, List[AtomicResource]]] = {}

    def is_empty(self) -> bool:
        """Returns True when there are no atomic nor macro resources.

        Returns:
            bool: True if there are no atomic resources or no macro/user resources
        """
        return len(self._atomic_resources) == 0 or (len(self._macro_resources) == 0 and len(self._user_resources) == 0)

    def atomic_resources(self) -> Generator[AtomicResource, None, None]:
        """Returns generator object that iterates over all atomic resources.

        Returns:
            Generator[AtomicResource, None, None]: Generator yielding all atomic resources including automatic ones
        """
        yield from self._atomic_resources + self._automatic_resources

    def macro_resources(self) -> Generator[MacroResource, None, None]:
        """Returns generator object that iterates over all macro resources.

        Returns:
            Generator[MacroResource, None, None]: Generator yielding all macro resources including user resources
        """
        yield from self._macro_resources + self._user_resources

    def macro_resources_list(self) -> List[MacroResource]:
        """Returns all macro resources.

        Returns:
            List[MacroResource]: Copy of all macro resources including user resources
        """
        return self._macro_resources.copy() + self._user_resources.copy()

    def user_resources_list(self) -> List[MacroResource]:
        """Returns all user resources.

        Returns:
            List[MacroResource]: Copy of all user resources
        """
        return self._user_resources.copy()

    def _add_to_index(self, index: Dict[Any, List[AtomicResource]], property_name: str, atomic_resource: AtomicResource) -> None:
        """Adds the atomic resource to the index by given property value.

        Args:
            index: Dictionary index to add the resource to
            property_name: Name of the property to index by
            atomic_resource: The atomic resource to add to the index
        """
        try:
            val = atomic_resource[property_name]
            if val is not None:
                if val not in index:
                    index[val] = []
                index[val].append(atomic_resource)
        except KeyError:
            pass

    def _build_index(self, property_name: str) -> None:
        """Builds index based on property of all the atomic resources.

        Args:
            property_name: Name of the property to build index for
        """
        index: Dict[Any, List[AtomicResource]] = {}
        for item in self._atomic_resources:
            self._add_to_index(index, property_name, item)
        self._indexes[property_name] = index

    def _get_index(self, property_name: str) -> Dict[Any, List[AtomicResource]]:
        """Returns index dictionary based on given property name.

        Args:
            property_name: Name of the property to get index for

        Returns:
            Dict[Any, List[AtomicResource]]: Index dictionary mapping property values to lists of atomic resources
        """
        if property_name not in self._indexes:
            self._build_index(property_name)
        index = self._indexes[property_name]
        return index

    def add_atomic_resource(self, atomic_resource: AtomicResource) -> None:
        """Adds the atomic resource to the database.

        Args:
            atomic_resource: The atomic resource to add to the database
        """
        name = atomic_resource.get_name()
        if "name" in self._indexes:
            existing = self._indexes["name"].get(name)
            if existing:
                logger.warning(
                    "Duplicate atomic resource name '%s' (already %d in DB)",
                    name,
                    len(existing),
                    extra={"source": "resdb/add_atomic_resource"},
                )

        self._atomic_resources.append(atomic_resource)

        # add to all indexes which were created so far
        for key in self._indexes:
            index = self._indexes[key]
            self._add_to_index(index, key, atomic_resource)

    def add_macro_resource(self, macro_resource: MacroResource) -> None:
        """Adds the macro resource to the database.

        Args:
            macro_resource: The macro resource to add to the database
        """
        self._macro_resources.append(macro_resource)

    def add_user_resource(self, user_resource: MacroResource) -> None:
        """Adds the user resource to the database.

        Args:
            user_resource: The user resource to add to the database
        """
        self._user_resources.append(user_resource)

    def add_define(self, assigned_define: AssignedDefine) -> None:
        """Adds the user resource to the database.

        Args:
            assigned_define: The assigned define to add to the database
        """
        self._defines[assigned_define.get_name()] = assigned_define

    def get_define(self, define_name: str) -> AssignedDefine | None:
        """Returns define with given name if it exists. For DFMT0 and DFMT1 default values are created.

        Args:
            define_name: Name of the define to retrieve

        Returns:
            AssignedDefine | None: The assigned define if found, or None if not found
        """
        if define_name in self._defines:
            return self._defines[define_name]
        if define_name == "DFMT0":
            dfmt_define = AssignedDefine("DFMT0", "sa=bypass")
            self.add_define(dfmt_define)
            return dfmt_define
        if define_name == "DFMT1":
            dfmt_define = AssignedDefine("DFMT1", "sa=bypass pa=bypass")
            self.add_define(dfmt_define)
            return dfmt_define
        return None

    def add_automatic_resource(self, auto_resource: AtomicResource) -> None:
        """Adds the user resource to the database.

        Args:
            auto_resource: The automatic resource to add to the database
        """
        self._automatic_resources.append(auto_resource)

        existing_res = self.find_atomic_resource_by("name", auto_resource.get_name())
        # only add to index if atomic resource is not already defined
        if len(existing_res) == 0:
            # add to all indexes which were created so far
            for key in auto_resource.get_raw_json():
                self._add_to_index(self._get_index(key), key, auto_resource)

    def find_atomic_resource_by(self, property_name: str, property_value: Any) -> List[AtomicResource]:
        """Finds atomic resource by given property name and value.

        Args:
            property_name: Name of the property to search by
            property_value: Value of the property to match

        Returns:
            List[AtomicResource]: List of atomic resources matching the criteria
        """
        index = self._get_index(property_name)

        # given value not yet seen
        if property_value not in index:
            return []

        # get all items whose [key] matches val
        items = index[property_value]
        if len(items) == 0:
            return []

        return items

    def find_macro_resource(self, name: str) -> MacroResource | None:
        """Searches for macro resource with given name. Returns None when no such macro resource exist.

        Args:
            name: Name of the macro resource to find

        Returns:
            MacroResource | None: The macro resource if found, or None if not found
        """
        for m in self._macro_resources + self._user_resources:
            if m.get_name() == name:
                return m
        return None

    def get_atomic_resources_json(self) -> object:
        """Returns raw JSON dictionary with all the data in the database.

        Returns:
            object: JSON dictionary containing atomic resources organized by type
        """
        ret: Dict[str, Any] = {
            "AtomicResources": {},  # atomic resources by type, original was: [i.GetRawJSON() for i in self._atomicRes]
        }

        types = self._get_index("type")
        auto_jsons = [i.get_raw_json() for i in self._automatic_resources]
        for t in types:
            type_raw_jsons = [i.get_raw_json() for i in self.find_atomic_resource_by("type", t) if i is not None]
            ret["AtomicResources"][t] = [type_json for type_json in type_raw_jsons if type_json not in auto_jsons]

        return ret

    def get_macro_resources_json(self) -> object:
        """Returns raw JSON dictionary with all the macro resources in the database.

        Returns:
            object: JSON dictionary containing all macro resources
        """
        ret = {"MacroResources": [i.get_raw_json() for i in self._macro_resources]}
        return ret

    def get_user_resources_json(self) -> Dict[str, Any]:
        """Returns raw JSON dictionary with all the user resources in the database.

        Returns:
            Dict[str, Any]: JSON dictionary containing all user resources
        """
        ret = {"UserResources": [i.get_raw_json() for i in self._user_resources]}
        return ret

    def get_automatic_resources_json(self) -> Dict[str, Any]:
        """Returns raw JSON dictionary with all the automatic resources in the database.

        Returns:
            Dict[str, Any]: JSON dictionary containing all automatic resources
        """
        ret = {"AutomaticResources": [i.get_raw_json() for i in self._automatic_resources]}
        return ret

    def _parse_auto_resources(self, autos: List[Any]) -> None:
        """Parses automatic resources from given JSON object.

        Args:
            autos: List of automatic resource data from JSON
        """
        for auto in autos:
            automatic_resource = ApiResource(auto)
            self.add_automatic_resource(automatic_resource)

    def _parse_atoms(self, atoms: Dict[str, Any]) -> None:
        """Parses atomic resources from given JSON object.

        Args:
            atoms: Dictionary of atomic resource data organized by type
        """
        for atomic_type in atoms:
            type_resources = atoms[atomic_type]
            for resource in type_resources:
                resource_dict = typing.cast(Dict[str, Any], resource)
                atomic = atomic_resource_from_raw(resource_dict)
                self.add_atomic_resource(atomic)

    def _parse_macros(self, macros: Any, user_defined: bool = False) -> None:
        """Parses macro resources from given JSON object.

        Args:
            macros: List of macro resource data from JSON
            user_defined: Whether these are user-defined resources
        """
        for resource in macros:
            macro = MacroResource(resource["name"])
            for atom_name in resource["atoms"]:
                atoms = self.find_atomic_resource_by("name", atom_name)
                if len(atoms) == 1:
                    macro.add_atomic_resource(atoms[0])
                else:
                    for atom in atoms:
                        macro.add_atomic_resource(atom)
            if "params" in resource:
                for param in resource["params"]:
                    macro.add_parameter(param)
            if user_defined:
                self.add_user_resource(macro)
            else:
                self.add_macro_resource(macro)

    def load_from_json(self, smct_configs_folder: str) -> bool:
        """Loads the resource database from JSON file.

        Args:
            smct_configs_folder: Path to the folder containing configuration JSON files

        Returns:
            bool: True if loading was successful, False otherwise
        """
        for file_name in ["atomic_resources.json", "macro_resources.json", "user_configuration.json"]:
            file_path = os.path.join(smct_configs_folder, file_name)
            if not os.path.exists(file_path):
                logger.error("File not found: %s", file_path, extra={"source": file_path})
                return False
            json_object = None
            with open(file_path, "r", encoding="utf-8") as file:
                json_object = json.load(file)
            if json_object is None:
                return False

            if "atomic" in file_name:
                validate_json(json_object, file_name, "atomic_schema.json", "warning")
                self._parse_atoms(json_object["AtomicResources"])
            elif "macro" in file_name:
                validate_json(json_object, file_name, "macro_schema.json", "warning")
                self._parse_macros(json_object["MacroResources"])
            elif "user" in file_name:
                validate_json(json_object, file_name, "user_schema.json", "warning")
                self._parse_auto_resources(json_object["AutomaticResources"])
                self._parse_macros(json_object["UserResources"], user_defined=True)
        return True
