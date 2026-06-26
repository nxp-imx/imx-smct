#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause

"""Module for generating file config_bctrl.h."""

import logging
from typing import Any, Dict, List

from smct.generation.generator import GenDcdInit, GeneratorBase, GenHeading
from smct.model.chip_model_provider import ChipModelProvider
from smct.model.model_bctrl import BctrlModel
from smct.owners.owner_base import AssignedResource
from smct.resources.res_bctrl import BctrlResourceIpgDebug

logger = logging.getLogger()


class GeneratorBCTRL(GeneratorBase):
    """Generator of config_bctrl.h."""

    def _get_generator_info(self) -> Dict[str, Any]:
        """Get generator information.

        Returns:
            Dict[str, Any]: Dictionary containing generator name and includes.
        """
        return {"name": "BCTRL", "incl": ["config_user.h"]}

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
        return ["", "", " Header file containing configuration info for the device block controls."]

    def _print_bctrl(self, bctrl: BctrlModel, assignments: List[AssignedResource]) -> None:
        """Generates the BCTRL configuration defines.

        Args:
            bctrl (BctrlModel): The BCTRL model to generate configuration for.
            assignments (List[AssignedResource]): List of assigned resources for this BCTRL.
        """
        self.print_generator(GenHeading(f"BCTRL {bctrl.get_letter_id()} Config"))
        dcd = GenDcdInit(f"SM_{bctrl.get_name()}_CONFIG", f"Config for BCTRL {bctrl.get_letter_id()}")
        dcd.set_upper_case_for_offset(True)

        # all assignments related to this bctrl
        for assigned_resource in assignments:
            for ipg in assigned_resource.get_bctrl_resources():
                # so far we only care about IPG_DEBUG resources
                if isinstance(ipg, BctrlResourceIpgDebug):
                    lm = self._get_configuration().get_owner_lm(assigned_resource)
                    if lm is None:
                        continue
                    for cpu in lm.get_all_cpus():
                        offsets = bctrl.get_cpu_offsets_ipg_debug(cpu.get_name())
                        if offsets:
                            if ipg.get_ipg_debug_registers_count() < len(offsets):
                                offset = offsets[ipg.get_ipg_debug_registers_count()]
                                if offset not in dcd:
                                    dcd[offset] = 0
                                dcd[offset] |= ipg.get_ipg_debug_mask().get_value()
                            else:
                                rsrc = assigned_resource.get_resource().get_name()
                                source = "/".join(["user_config", lm.get_name(), rsrc])
                                validation_id = ".".join([lm.get_id(), "RESOURCES", rsrc])
                                logger.error(
                                    "Invalid access from %s to %s IPG_DEBUG register regn=%i",
                                    ipg.get_name(),
                                    bctrl.get_name(),
                                    ipg.get_ipg_debug_registers_count(),
                                    extra={"source": source, "validation_id": validation_id},
                                )
                                return
        self.print_generator(dcd)

    def print_content(self) -> None:
        """Generates the BCTRL configuration defines."""
        bctrls = ChipModelProvider.get_model().get_all_bctrls()
        assignments = self._get_configuration().get_all_bctrl_assignments()
        for bctrl in bctrls:
            bctrl_assignments = []
            if bctrl in assignments:
                bctrl_assignments = assignments[bctrl]
            self._print_bctrl(bctrl, bctrl_assignments)

    def __str__(self) -> str:
        """Returns string representation of the generator.

        Returns:
            str: String representation of the BCTRL generator.
        """
        return "BCTRL generator"
