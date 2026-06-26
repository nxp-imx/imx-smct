#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause

"""Module for generating file config.dox."""

from typing import Any, Dict

from smct.generation.generator import GeneratorBase


class GeneratorDoxygen(GeneratorBase):
    """Generator for doxygen file."""

    def _get_generator_info(self) -> Dict[str, Any]:
        """Get generator information.

        Returns:
            Dict[str, Any]: Dictionary containing generator name.
        """
        # This must be overridden to avoid exception
        return {"name": "dox"}

    def _print_doxygen(self) -> None:
        """Print doxygen documentation block."""
        self._print("/*!")
        configuration = self._get_configuration()
        dox_name = configuration.get_doxygen_name().upper().replace(" ", "_")
        dox_desc = configuration.get_doxygen_description()
        self._print(f"@defgroup CONFIG_{dox_name} CONFIG_{dox_name}: {dox_desc}")
        self._print(f"@brief Module for {configuration.get_doxygen_description()}.")
        self._print("*/")

    def _get_output_file_name(self) -> str:
        """Get the output file name.

        Returns:
            str: The output file name.
        """
        return "config.dox"

    def _get_header_protection_macro(self) -> None:
        """Get header protection macro.

        Returns:
            None: No header protection macro for doxygen files.
        """
        return None

    def _should_defines_comment_be_generated(self) -> bool:
        """Check if defines comment should be generated.

        Returns:
            bool: False, defines comments are not generated for doxygen files.
        """
        return False

    def _get_doxygen_group_name(self) -> str:
        """Get the doxygen group name.

        Returns:
            str: The doxygen group name.
        """
        return "SM_CONFIG"

    def print_content(self) -> None:
        """Print the doxygen content."""
        self._print_doxygen()

    def __str__(self) -> str:
        """Return string representation of the generator.

        Returns:
            str: String representation of the generator.
        """
        return "DOX generator"
