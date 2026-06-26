#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause

"""Module for generating file config_board.h."""

from typing import Any, Dict, List

from smct.generation.generator import GeneratorBase, GenMacroValue


class GeneratorBoard(GeneratorBase):
    """Generator for config_board.h file."""

    def _get_generator_info(self) -> Dict[str, Any]:
        """Get generator information.

        Returns:
            Dict[str, Any]: Dictionary containing generator name and includes.
        """
        # This must be overridden to avoid exception
        return {"name": "board", "incl": ["config_user.h"]}

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
        return ["", "", " Header file containing configuration info for the board abstraction."]

    def _print_board_defines(self) -> None:
        """Generates board defines like debug UART instance etc."""
        for config, value in self._get_configuration().get_board_configs():
            self.print_generator(GenMacroValue(f"BOARD_{config}", value, f"{config} from cfg file"))

        self.print_generator(GenMacroValue("BOARD_DEBUG_UART_INSTANCE", f"{self._get_configuration().get_debug_uart_instance()}U", "Config for UART instance"))
        self.print_generator(GenMacroValue("BOARD_DEBUG_UART_BAUDRATE", f"{self._get_configuration().get_debug_uart_baudrate()}U", "Config for UART baudrate"))
        self.print_generator(GenMacroValue("BOARD_I2C_INSTANCE", f"{self._get_configuration().get_pmic_i2c_instance()}U", "Config for PMIC I2C instance"))
        self.print_generator(GenMacroValue("BOARD_I2C_BAUDRATE", f"{self._get_configuration().get_pmic_i2c_baudrate()}U", "Config for PMIC I2C baudrate"))

    def print_content(self) -> None:
        """Generates content of this file."""
        self._print_board_defines()

    def __str__(self) -> str:
        """Returns string representation of the generator.

        Returns:
            str: String representation of the generator.
        """
        return "BOARD generator"
