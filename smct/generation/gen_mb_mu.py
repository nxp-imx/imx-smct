#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Module for generating file config_mb_mu.h"""
import typing
from typing import Any, Dict, List

from smct.expcetions.cfg_tool_exception import CfgToolException
from smct.generation.generator import GeneratorBase, GenHeading, GenMacroList, GenMacroValue, GenStructInit
from smct.owners.owner_agent import MailboxMu, ScmiAgent
from smct.owners.owner_lm import LM


class GeneratorMBMU(GeneratorBase):
    """Generator of config_mb_Mu.h"""

    def _get_doxygen_file_name(self) -> str:
        """Gets the doxygen file name.

        Returns:
            str: Empty string for doxygen file name.
        """
        return ""

    def _get_doxygen_brief_lines(self) -> List[str]:
        """Gets the doxygen brief description lines.

        Returns:
            List[str]: List of brief description lines for the header file.
        """
        return ["", "", " Header file containing configuration info for the MB_MU."]

    def _get_generator_info(self) -> Dict[str, Any]:
        """Gets the generator information.

        Returns:
            Dict[str, Any]: Dictionary containing generator name and include files.
        """
        return {
            "name": "MB_MU",
            "incl": ["config_user.h", "mb_mu_config.h"],
        }

    def can_file_open(self, _: str, __: bool) -> bool:
        """Determines if the file can be opened based on configuration.

        Args:
            _: Unused parameter.
            __: Unused parameter.

        Returns:
            bool: True if the configuration contains at least one messaging unit mailbox, False otherwise.
        """
        return len(self._get_configuration().get_all_message_unit_mailboxes()) > 0

    def _print_agent_messaging_units(self, agent: ScmiAgent) -> None:
        """Generates agent messaging unit configuration defines.

        Args:
            agent: The SCMI agent to generate configuration for.
        """
        mailbox = agent.get_mailbox()
        if not isinstance(mailbox, MailboxMu):
            raise CfgToolException("Internal failure, MB_MU type mismatch")
        mailbox = typing.cast(MailboxMu, mailbox)

        mailbox_mu = mailbox.get_mu()
        struct_define = f"SM_MB_MU{mailbox_mu}_CONFIG"
        struct_comment = f"Config for MB_MU{mailbox_mu} instance (uses MU{mailbox_mu}, used by {agent.get_name()})"
        structure_generator = GenStructInit(struct_define, struct_comment)
        structure_generator["mu"] = mailbox.get_mu()
        sma = mailbox.get_sma()
        if sma is not None:
            structure_generator["sma"] = f"{sma}U"
        priority = mailbox.get_priority()
        if priority is not None:
            structure_generator["priority"] = mailbox.get_priority_define()
        doorbell_channels = mailbox.get_doorbell_channels()
        for index in range(0, len(doorbell_channels)):
            doorbell_channel = doorbell_channels[index]
            if doorbell_channel is not None:
                channel_inst = self._get_configuration().get_channel_inst(doorbell_channel)
                structure_generator[f"xportType[{index}]"] = doorbell_channel.get_xport_type()
                structure_generator[f"xportChannel[{index}]"] = channel_inst
        self.print_generator(structure_generator)

    def _print_logical_machine_mailboxes(self, logical_machine: LM) -> None:
        """Generates configuration defines for messaging units of logical machines.

        Args:
            logical_machine: The logical machine to generate mailbox configuration for.
        """
        self.print_generator(GenHeading(f"{logical_machine.get_id()} MB_MU Config ({logical_machine.get_name()})"))

        for agent in logical_machine.get_all_agents():
            mailbox = agent.get_mailbox()
            if isinstance(mailbox, MailboxMu):
                self._print_agent_messaging_units(agent)

    def _print_message_units_summary(self) -> None:
        """Generates defines with summary of messaging units configuration."""
        message_unit_mailboxes_amount = len(self._get_configuration().get_all_message_unit_mailboxes())
        message_unit_numbers = self._get_configuration().get_all_message_unit_numbers()

        self.print_generator(GenHeading("MB_MU Config"))
        self.print_generator(GenMacroValue("SM_NUM_MB_MU", message_unit_mailboxes_amount, "Config for number of MB_MU instances"))

        if message_unit_mailboxes_amount:
            macro_generator = GenMacroList("SM_MB_MU_CONFIG_DATA", "Config data array for MB_MU instances")
            for num in message_unit_numbers:
                macro_generator.add_value(f"SM_MB_MU{num}_CONFIG")
            self.print_generator(macro_generator)

    def print_content(self) -> None:
        """Generates defines of messaging units configuration."""
        for logical_machine in self._get_configuration().get_all_lms():
            self._print_logical_machine_mailboxes(logical_machine)

        self._print_message_units_summary()

    def __str__(self) -> str:
        """Returns string representation of the generator.

        Returns:
            str: String description of the mailbox messaging unit generator.
        """
        return "Mailbox messaging unit generator"
