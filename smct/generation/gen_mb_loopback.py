#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause

"""Module for generating file config_mb_loopback.h"""

import typing
from typing import Any, Dict, List

from smct.exceptions.cfg_tool_exception import CfgToolException
from smct.generation.generator import GeneratorBase, GenHeading, GenMacroList, GenMacroValue, GenStructInit
from smct.owners.owner_agent import MailboxLoopback, ScmiAgent
from smct.owners.owner_lm import LM


class GeneratorMailboxLoopback(GeneratorBase):
    """Generator of config_mb_loopback.h"""

    def _get_doxygen_file_name(self) -> str:
        """Get the doxygen file name.

        Returns:
            str: Empty string for doxygen file name.
        """
        return ""

    def _get_doxygen_brief_lines(self) -> List[str]:
        """Get the doxygen brief description lines.

        Returns:
            List[str]: List of brief description lines for doxygen.
        """
        return ["", "", " Header file containing configuration info for the MB_LOOPBACK."]

    def _get_generator_info(self) -> Dict[str, Any]:
        """Get generator information dictionary.

        Returns:
            Dict[str, Any]: Dictionary containing generator name and includes.
        """
        return {
            "name": "MB_LOOPBACK",
            "incl": ["config_user.h", "mb_loopback_config.h"],
        }

    def can_file_open(self, _: str, __: bool) -> bool:
        """Check if the configuration file can be opened.

        Args:
            _: Unused parameter.
            __: Unused parameter.

        Returns:
            bool: True if the configuration contains at least one loopback mailbox, False otherwise.
        """
        return len(self._get_configuration().get_all_loopback_mailboxes()) > 0

    def _print_agent_loopbacks(self, agent: ScmiAgent) -> None:
        """Generate agent messaging unit configuration defines.

        Args:
            agent: The SCMI agent to generate loopback configuration for.
        """
        mailbox = agent.get_mailbox()
        if not isinstance(mailbox, MailboxLoopback):
            raise CfgToolException("Internal failure, MB_LOOPBACK type mismatch")
        mailbox = typing.cast(MailboxLoopback, mailbox)

        mb_index = self._get_configuration().get_mailbox_instance_index(mailbox)
        struct_generator = GenStructInit(f"SM_MB_LOOPBACK{mb_index}_CONFIG", f"Config for MB_LOOPBACK{mb_index} instance (used by {agent.get_name()})")
        priority = mailbox.get_priority()
        if priority is not None:
            struct_generator["priority"] = mailbox.get_priority_define()
        channels = mailbox.get_doorbell_channels()
        for index in range(0, len(channels)):
            doorbell_channel = channels[index]
            if doorbell_channel is not None:
                struct_generator[f"xportType[{index}]"] = doorbell_channel.get_xport_type()
                struct_generator[f"xportChannel[{index}]"] = self._get_configuration().get_channel_inst(doorbell_channel)
        self.print_generator(struct_generator)

    def _print_logical_machine_mailboxes(self, logical_machine: LM) -> None:
        """Generate configuration defines for messaging units of logical machines.

        Args:
            logical_machine: The logical machine to generate mailbox configuration for.
        """
        self.print_generator(GenHeading(f"{logical_machine.get_id()} MB_LOOPBACK Config ({logical_machine.get_name()})"))

        for agent in logical_machine.get_all_agents():
            mailbox = agent.get_mailbox()
            if isinstance(mailbox, MailboxLoopback):
                self._print_agent_loopbacks(agent)

    def _print_mailboxes_summary(self) -> None:
        """Generate defines with summary of messaging units configuration."""
        loopback_mailboxes_amount = len(self._get_configuration().get_all_loopback_mailboxes())

        self.print_generator(GenHeading("MB_LOOPBACK Config"))
        self.print_generator(GenMacroValue("SM_NUM_MB_LOOPBACK", loopback_mailboxes_amount, "Config for number of MB_LOOPBACK instances"))

        if loopback_mailboxes_amount > 0:
            macro_generator = GenMacroList("SM_MB_LOOPBACK_CONFIG_DATA", "Config data array for MB_LOOPBACK instances")
            for index in range(0, loopback_mailboxes_amount):
                macro_generator.add_value(f"SM_MB_LOOPBACK{index}_CONFIG")
            self.print_generator(macro_generator)

    def print_content(self) -> None:
        """Generate defines of messaging units configuration."""
        for logical_machine in self._get_configuration().get_all_lms():
            self._print_logical_machine_mailboxes(logical_machine)

        self._print_mailboxes_summary()

    def __str__(self) -> str:
        """Get string representation of the generator.

        Returns:
            str: String representation of the mailbox loopback generator.
        """
        return "Mailbox loopback generator"
