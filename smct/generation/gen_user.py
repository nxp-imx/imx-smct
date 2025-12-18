#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Module for generating file config_user.h"""
import os.path
from typing import Any, Dict, List

from smct.generation.generator import GeneratorBase, GenHeading, GenMacroList
from smct.model.chip_model_provider import ChipModelProvider


class GeneratorUser(GeneratorBase):
    """Generator for config_user.h file"""

    def _get_generator_info(self) -> Dict[str, Any]:
        """Get generator information.

        Returns:
            Dict[str, Any]: Dictionary containing generator name and includes.
        """
        # This must be overridden to avoid exception
        return {"name": "user", "incl": ["config.h"]}

    def _get_doxygen_file_name(self) -> str:
        """Get doxygen file name.

        Returns:
            str: Empty string for doxygen file name.
        """
        return ""

    def _get_doxygen_brief_lines(self) -> List[str]:
        """Get doxygen brief description lines.

        Returns:
            List[str]: List of brief description lines for doxygen.
        """
        return ["", "", " Header file containing configuration info for the manual user settings."]

    def can_file_open(self, path: str, __: bool) -> bool:
        """Check if file can be opened.

        Args:
            path (str): Path to the file to check.
            __ (bool): Unused parameter.

        Returns:
            bool: True if file at given path does not exist, False otherwise.
        """
        return not os.path.exists(path)

    def _print_device_structures(self) -> None:
        """Generate device configuration macros."""
        for mix in ChipModelProvider.get_model().get_mixes():
            self.print_generator(GenHeading(f"{mix.upper()} Config"))
            generator = GenMacroList(f"SM_{mix.upper()}_CONFIG", f"Data load config for the {mix.upper()} mix")
            generator.add_value("{ \\\n        SM_CFG_END \\\n    }")
            self.print_generator(generator)

    def print_content(self) -> None:
        """Generate device configuration file."""
        self._print_device_structures()

    def __str__(self) -> str:
        """Get string representation of the generator.

        Returns:
            str: String representation of the generator.
        """
        return "USER generator"
