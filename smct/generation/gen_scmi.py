#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause

"""Module for generating file config_scmi.h."""

import logging
from typing import Any, Dict, List

from smct.exceptions.cfg_tool_exception import CfgToolException
from smct.generation.generator import GeneratorBase, GenHeading, GenMacroList, GenMacroValue, GenStructInit
from smct.owners.owner_agent import ScmiAgent, ScmiChannel
from smct.owners.owner_base import AssignedResource
from smct.owners.owner_lm import LM
from smct.resources.res_api import ApiResource

logger = logging.getLogger()


class GeneratorSCMI(GeneratorBase):
    """Generator of config_scmi.h."""

    def _get_doxygen_file_name(self) -> str:
        return ""

    def _get_doxygen_brief_lines(self) -> List[str]:
        return ["", "", " Header file containing configuration info for the SCMI RPC."]

    def _get_generator_info(self) -> Dict[str, Any]:
        return {"name": "SCMI", "incl": ["config_user.h"]}

    def _print_agent_struct(self, agent: ScmiAgent, agent_id: int) -> None:
        """Generates SCMI agent configuration structure.

        Args:
            agent: The SCMI agent to generate configuration for.
            agent_id: The ID of the agent.
        """
        conf = self._get_configuration()

        self.print_generator(GenHeading(f"SCMI AGENT{agent_id} Config ({agent.get_name()})"))

        s = GenStructInit(f"SM_SCMI_AGNT{agent_id}_CONFIG", f"Config for SCMI agent {agent_id}")
        s["name"] = f'"{agent.get_name()}"'
        lm = conf.get_lm_of_agent(agent)
        if lm is not None:
            s["scmiInst"] = conf.get_lm_rpc_inst(lm)
        else:
            source = "/".join(["user_config", agent.get_name()])
            logger.error("Agent '%s' is not assigned to any LM", agent, extra={"source": source, "validation_id": agent.get_id()})
        s["domId"] = agent.get_did()
        s["secure"] = agent.get_secure()

        if agent.get_safe_type() == "seenv":
            s["seenvId"] = conf.get_agent_seenv_id(agent)

        s.print_head()
        s.print_members()
        self._print(s.get_head_string(), end="")
        self._print(s.get_members_string(), end="")

        # all API permissions (sorted separately, members only):
        s2 = GenStructInit(None)
        assr: AssignedResource
        for assr in agent.get_owned_resources():
            perm = assr.get_permission_type()
            if perm is not None:
                for a in assr.get_resource().get_atomic_resources():
                    if isinstance(a, ApiResource) and not a.is_auto():
                        memb = a.get_perms_member()
                        # as we are dealing with macro resources, it might happen that some
                        # api resource is assigned twice, but it should be for the same permission
                        if memb in s2 and s2[memb] != perm:
                            name = a.get_name()
                            scmi_id = agent.get_id()
                            raise CfgToolException(f"Cannot resolve dual incompatible assignment of API resource {name} to {scmi_id}")
                        s2[memb] = perm
        s2.set_sorting()
        s2.print_members()
        self._print(s2.get_members_string(), end="")
        s.print_tail()
        self._print(s.get_tail_string(), end="")

    def _print_scmi_channel(self, chan: ScmiChannel, agent_id: int) -> None:
        """Generates SCMI channel configuration.

        Args:
            chan: The SCMI channel to generate configuration for.
            agent_id: The ID of the agent that owns the channel.
        """
        conf = self._get_configuration()
        chan_id = conf.get_channel_inst(chan)

        s = GenStructInit(f"SM_SCMI_CHN{chan_id}_CONFIG", f"Config for SCMI channel {chan_id}")
        s["agentId"] = agent_id
        s["type"] = chan.get_channel_type_define()
        if chan.get_sequence() is not None:
            s["sequence"] = chan.get_channel_sequence_define()
        xport_channel = chan.get_xport_channel()
        if xport_channel is not None:
            s["xportType"] = xport_channel.get_xport_type()
            s["xportChannel"] = conf.get_channel_inst(xport_channel)
        self.print_generator(s)

    def _print_agent(self, agent: ScmiAgent) -> None:
        """Generates SCMI agent configuration.

        Args:
            agent: The SCMI agent to generate configuration for.
        """
        agent_id = self._get_configuration().get_scmi_agent_id(agent)
        self._print_agent_struct(agent, agent_id)

        for ch in agent.get_all_scmi_channels():
            self._print_scmi_channel(ch, agent_id)

    def _print_scmi(self, lm: LM) -> None:
        """Generates SCMI configuration for given logical machine.

        Args:
            lm: The logical machine to generate SCMI configuration for.
        """
        conf = self._get_configuration()
        lm_id = conf.get_lm_id(lm)
        scmi_inst = conf.get_lm_rpc_inst(lm)
        agents = lm.get_all_agents()

        self.print_generator(GenHeading(f"SCMI Instance {scmi_inst} Config ({lm.get_name()})"))
        s = GenStructInit(f"SM_SCMI{scmi_inst}_CONFIG", f"Config for SCMI instance {scmi_inst}")

        s["lmId"] = lm_id
        if len(agents):
            s["numAgents"] = len(agents)
            s["firstAgent"] = conf.get_scmi_agent_id(agents[0])
        self.print_generator(s)

    def _print_agents_summary(self) -> None:
        """Generates SCMI agents configuration summary."""
        agents_len = len(self._get_configuration().get_all_scmi_agents())

        self.print_generator(GenHeading("SCMI Agent Config"))
        self.print_generator(GenMacroValue("SM_SCMI_NUM_AGNT", agents_len, "Config for number of SCMI agents"))

        s = GenMacroList("SM_SCMI_AGNT_CONFIG_DATA", "Config data array for SCMI agents")
        for i in range(0, agents_len):
            s.add_value(f"SM_SCMI_AGNT{i}_CONFIG")
        self.print_generator(s)

    def _print_channels_summary(self) -> None:
        """Generates summary of SCMI channels."""
        chans_len = len(self._get_configuration().get_all_scmi_channels())

        self.print_generator(GenHeading("SCMI Channel Config"))
        self.print_generator(GenMacroValue("SM_SCMI_NUM_CHN", chans_len, "Config for number of SCMI channels"))

        s = GenMacroList("SM_SCMI_CHN_CONFIG_DATA", "Config data array for SCMI channels")
        for i in range(0, chans_len):
            s.add_value(f"SM_SCMI_CHN{i}_CONFIG")
        self.print_generator(s)

    def _print_scmi_summary(self) -> None:
        """Generates summary of SCMI configuration."""
        scmi_len = len(self._get_configuration().get_all_scmi_lms())

        self.print_generator(GenHeading("SCMI Config"))
        self.print_generator(GenMacroValue("SM_NUM_SCMI", scmi_len, "Config for number of SCMI instances"))

        s = GenMacroList("SM_SCMI_CONFIG_DATA", "Config data array for SCMI instances")
        for i in range(0, scmi_len):
            s.add_value(f"SM_SCMI{i}_CONFIG")
        self.print_generator(s)

        self.print_generator(
            GenMacroValue("SM_SCMI_MAX_NOTIFY", self._get_configuration().get_max_scmi_channel_notify(), "Max words to buffer for notification messages")
        )

    def print_content(self) -> None:
        """Emit per-agent and per-LM SCMI sections followed by summary blocks."""
        conf = self._get_configuration()

        for lm in conf.get_all_lms():
            for a in lm.get_all_agents():
                self._print_agent(a)
            if lm.is_scmi():
                self._print_scmi(lm)

        self._print_agents_summary()
        self._print_channels_summary()
        self._print_scmi_summary()

    def __str__(self) -> str:
        """Returns string representation of the generator.

        Returns:
            String representation of the generator.
        """
        return "SCMI generator"
