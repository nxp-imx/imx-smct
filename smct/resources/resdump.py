#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Module for exporting resources"""
import json
import os.path
import sys

from smct.configuration.configuration_provider import ConfigurationProvider
from smct.model.chip_model_provider import ChipModelProvider
from smct.resources.resource_database_provider import ResourceDatabaseProvider
from smct.utils import FormatedIntEncoder


def _dump_atoms_to_file() -> None:
    """Generates the atomic resources from resource database into JSON file.

    Returns:
        None
    """
    print(json.dumps(ResourceDatabaseProvider.get_database().get_atomic_resources_json(), indent=4, cls=FormatedIntEncoder))


def _dump_macros_to_file() -> None:
    """Generates the macro resources from resource database into JSON file.

    Returns:
        None
    """
    print(json.dumps(ResourceDatabaseProvider.get_database().get_macro_resources_json(), indent=4))


def _dump_chip_model_to_file() -> None:
    """Generates the chip model content as JSON.

    Returns:
        None
    """
    print(json.dumps(ChipModelProvider.get_model().get_raw_json(), indent=4, cls=FormatedIntEncoder))


def generate_database(output_folder: str) -> None:
    """Generates resource database and chip model into given file.

    Args:
        output_folder: The folder path where the generated files will be saved.

    Returns:
        None
    """
    files = {
        "atomic_resources": _dump_atoms_to_file,
        "macro_resources": _dump_macros_to_file,
        "chip_data": _dump_chip_model_to_file,
    }

    previous_stdout = sys.stdout
    for file in files:
        try:
            file_path = os.path.join(output_folder, f"{file}.json")
            with open(file_path, "w", encoding="utf-8") as open_file:
                sys.stdout = open_file
                files[file]()
        finally:
            sys.stdout = previous_stdout


def _dump_configuration_to_json() -> None:
    """Generates configuration content as JSON.

    Returns:
        None
    """
    print(json.dumps(ConfigurationProvider.get_configuration().get_assignment_json(), indent=4, cls=FormatedIntEncoder))


def dump_configuration(output_folder: str) -> None:
    """Generates configuration into given file.

    Args:
        output_folder: The folder path where the configuration file will be saved.

    Returns:
        None
    """
    stdout_old = sys.stdout
    try:
        file_path = os.path.join(output_folder, "user_configuration.json")
        with open(file_path, "w", encoding="utf-8") as file:
            sys.stdout = file
            _dump_configuration_to_json()
    finally:
        sys.stdout = stdout_old
