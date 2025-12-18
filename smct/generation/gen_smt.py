#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Module for generating file config_smt.h"""
import typing
from typing import Any, Dict, List, Set

from smct.expcetions.cfg_tool_exception import CfgToolException
from smct.generation.generator import GeneratorBase, GenHeading, GenMacroList, GenMacroPresence, GenMacroValue, GenStructInit
from smct.owners.owner_agent import ScmiAgent, SmtChannel
from smct.owners.owner_lm import LM


class GeneratorSMT(GeneratorBase):
    """Generator of config_smt.h"""

    def _get_generator_info(self) -> Dict[str, Any]:
        """Get generator information.

        Returns:
            Dict[str, Any]: Dictionary containing generator name and includes.
        """
        return {
            "name": "SMT",
            "incl": ["config_user.h", "rpc_smt_config.h"],
        }

    def _get_doxygen_file_name(self) -> str:
        """Get doxygen file name.

        Returns:
            str: Empty string for doxygen file name.
        """
        return ""

    def _get_doxygen_brief_lines(self) -> List[str]:
        """Get doxygen brief lines.

        Returns:
            List[str]: List of brief description lines for doxygen.
        """
        return ["", "", " Header file containing configuration info for the SMT."]

    def _print_smt(self, agent: ScmiAgent, smt: SmtChannel) -> None:
        """Generates SMT configuration macros.

        Args:
            agent: The SCMI agent.
            smt: The SMT channel.
        """
        if not isinstance(smt, SmtChannel):
            raise CfgToolException("Internal failure, SMT_CHANNEL type mismatch")

        smt_inst = self._get_configuration().get_channel_inst(smt)
        s = GenStructInit(f"SM_SMT_CHN{smt_inst}_CONFIG", f"Config for SMT channel {smt_inst} (used by {agent.get_name()})")
        rpc_channel = smt.get_rpc_channel()
        if rpc_channel is not None:
            s["rpcType"] = rpc_channel.get_rpc_type()
            s["rpcChannel"] = self._get_configuration().get_channel_inst(rpc_channel)
        mailbox = smt.get_mailbox()
        if mailbox is not None:
            s["mbType"] = mailbox.get_type_define()
            s["mbInst"] = self._get_configuration().get_mailbox_instance_index(mailbox)
        s["mbDoorbell"] = smt.get_doorbell()
        if smt.get_check() is not None:
            s["crc"] = smt.get_check_define()
        self.print_generator(s)

    def _print_agent_smts(self, agent: ScmiAgent) -> None:
        """Generates SMT channels configuration macros from given SCMI agent.

        Args:
            agent: The SCMI agent to generate SMT channels configuration for.
        """
        channels = [typing.cast(SmtChannel, ch) for ch in agent.get_all_xport_channels() if ch.get_type() == "smt"]
        for ch in channels:
            self._print_smt(agent, ch)

    def _print_lm_smts(self, lm: LM) -> None:
        """Generates SMT channels configuration macros of given logical machine. Includes all SCMI channels in this
         logical machine.

        Args:
            lm: The logical machine to generate SMT channels configuration for.
        """
        self.print_generator(GenHeading(f"{lm.get_id()} SMT Config ({lm.get_name()})"))

        for a in lm.get_all_agents():
            self._print_agent_smts(a)

    def _print_smts_summary(self) -> None:
        """Generates SMT summary macros."""
        smt_all = self._get_configuration().get_all_smt_channels()
        smt_len = len(smt_all)

        self.print_generator(GenHeading("SMT Config"))
        self.print_generator(GenMacroValue("SM_NUM_SMT_CHN", smt_len, "Config for number of SMT channels"))

        if smt_len != 0:
            s = GenMacroList("SM_SMT_CHN_CONFIG_DATA", "Config data array for SMT channels")
            for i in range(0, smt_len):
                s.add_value(f"SM_SMT_CHN{i}_CONFIG")
            self.print_generator(s)

            mailbox_types = set()
            for smt_channel in smt_all:
                mailbox = smt_channel.get_mailbox()
                if mailbox is not None:
                    mailbox_types.add(mailbox.get_type())

            for mbt in mailbox_types:
                self.print_generator(GenMacroPresence(f"USES_MB_{mbt.upper()}", f"At least one SMT channel uses MB_{mbt.upper()}"))
            check_types: Set[str] = set()
            for smt in smt_all:
                check_type = smt.get_check()
                if check_type is not None:
                    check_types.add(check_type)
            for crc in check_types:
                self.print_generator(GenMacroPresence(f"USES_CRC_{crc.upper()}", f"At least one SMT channel uses {crc.upper()} check"))

    def print_content(self) -> None:
        """Generates SMT configuration macros of all logical machines followed by SMT summary macros."""
        for lm in self._get_configuration().get_all_lms():
            self._print_lm_smts(lm)

        self._print_smts_summary()

    def __str__(self) -> str:
        """Returns string representation of the generator.

        Returns:
            str: String representation of the generator.
        """
        return "SMT generator"
