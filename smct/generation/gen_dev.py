#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause

"""Module for generating file config_dev.h"""

from typing import Any, Dict, List

from smct import utils
from smct.generation.generator import GeneratorBase, GenMacroList


class GeneratorDev(GeneratorBase):
    """Generator for config_dev.h file"""

    def _get_generator_info(self) -> Dict[str, Any]:
        """Gets generator information dictionary.

        Returns:
            Dict[str, Any]: Dictionary containing generator name and includes.
        """
        # This must be overridden to avoid exception
        return {"name": "dev", "incl": ["config_user.h"]}

    def _get_doxygen_file_name(self) -> str:
        """Gets the doxygen file name.

        Returns:
            str: Empty string for doxygen file name.
        """
        return ""

    def _get_doxygen_brief_lines(self) -> List[str]:
        """Gets doxygen brief description lines.

        Returns:
            List[str]: List of brief description lines for doxygen.
        """
        return ["", "", " Header file containing configuration info for the device abstraction."]

    def _print_device_structures(self) -> None:
        """Generates device configuration macros."""
        generator = GenMacroList("SM_DEV_CONFIG_DATA", "Config for device")
        parts = ["{", " \\\n"]
        for lm in self._get_configuration().get_all_lms():
            for assr in lm.get_all_assignments():
                for cpu_resource in assr.get_cpu_resources():
                    cpu_name = "DEV_SM_" + cpu_resource.get_name().upper()
                    if "sema" in assr.get_params():
                        sema = assr.get_params()["sema"]

                        parts.append("        ")
                        parts.append(f".cpuSemaAddr[{cpu_name}]")
                        parts.append(" = ")
                        parts.append(utils.convert_to_hex(sema.get_value(), digits=0))
                        parts.append("U")
                        parts.append(", \\\n")
        parts.append("    ")
        parts.append("}")
        generator.add_value("".join(parts))
        self.print_generator(generator)

    def print_content(self) -> None:
        """Generates device configuration file."""
        self._print_device_structures()

    def __str__(self) -> str:
        """Returns string representation of the generator.

        Returns:
            str: String representation of the DEV generator.
        """
        return "DEV generator"
