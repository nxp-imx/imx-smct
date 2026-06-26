#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause

"""Module for generating file config.mak."""

from typing import Any, Dict

from smct.generation.generator import GeneratorBase
from smct.product_info import ProductInfo


class GeneratorMakeFile(GeneratorBase):
    """Generator for make file."""

    def _get_generator_info(self) -> Dict[str, Any]:
        """Get generator information.

        Returns:
            Dict[str, Any]: Dictionary containing generator name.
        """
        # This must be overridden to avoid exception
        return {"name": "mak"}

    def _should_doxygen_be_generated(self) -> bool:
        """Check if doxygen should be generated.

        Returns:
            bool: False, indicating doxygen should not be generated.
        """
        return False

    def _get_output_file_name(self) -> str:
        """Get the output file name.

        Returns:
            str: The output file name "config.mak".
        """
        return "config.mak"

    def _get_header_protection_macro(self) -> None:
        """Get header protection macro.

        Returns:
            None: No header protection macro is used.
        """
        return None

    def _should_defines_comment_be_generated(self) -> bool:
        """Check if defines comment should be generated.

        Returns:
            bool: False, indicating defines comment should not be generated.
        """
        return False

    def _get_copyright_comment_beginning(self) -> str:
        """Get copyright comment beginning.

        Returns:
            str: Empty string for copyright comment beginning.
        """
        return ""

    def _get_copyright_comment_prefix(self) -> str:
        """Get copyright comment prefix.

        Returns:
            str: The copyright comment prefix "##".
        """
        return "##"

    def _get_copyright_comment_ending(self) -> str:
        """Get copyright comment ending.

        Returns:
            str: Empty string for copyright comment ending.
        """
        return ""

    def _print_makefile(self) -> None:
        """Print the makefile content."""
        configuration = self._get_configuration()
        self._print(f"GEN_CONFIG_VER ?= {ProductInfo.get_sm_fw_compatible_version()}U")
        self._print("")
        self._print(f"BOARD ?= {configuration.get_board_name()}")
        self._print("")
        if len(configuration.get_all_seenv_agents()) > 0:
            self._print("USES_FUSA ?= 1")
        for variable, value in configuration.get_mak_variables():
            self._print(variable.upper() + " ?= " + str(value).upper())
        self._print("")
        self._print(f"include ./devices/{configuration.get_device_name()}/sm/Makefile")
        self._print("include ./boards/$(BOARD)/sm/Makefile")
        self._print("include ./sm/lmm/Makefile")
        if len(configuration.get_all_loopback_mailboxes()) > 0:
            self._print("include ./sm/rpc/mb_loopback/Makefile")
        if len(configuration.get_all_message_unit_mailboxes()) > 0:
            self._print("include ./sm/rpc/mb_mu/Makefile")
        self._print("include ./sm/rpc/scmi/Makefile")
        self._print("include ./sm/rpc/smt/Makefile")
        build_tool = configuration.get_build_tool()
        self._print(f"include ./sm/makefiles/{build_tool}.mak")
        self._print("")

    def print_content(self) -> None:
        """Print the content of the makefile."""
        self._print_makefile()

    def __str__(self) -> str:
        """Returns string representation of the generator.

        Returns:
            str: String representation of the generator.
        """
        return "MAK generator"
