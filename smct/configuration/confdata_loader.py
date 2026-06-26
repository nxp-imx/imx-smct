#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Module related to user configuration."""

import logging
import typing
from typing import Any, Dict, List, Sequence

from smct.owners.owner_agent import Mailbox, MailboxLoopback, MailboxMu, ScmiAgent, ScmiChannel, SmtChannel
from smct.owners.owner_base import AssignedDefine, ResourceOwner
from smct.owners.owner_dom import DOM
from smct.owners.owner_lm import LM, MSEL
from smct.resources.resource_base import AtomicResource, MacroResource
from smct.resources.resource_database_provider import ResourceDatabaseProvider
from smct.utils import FormatedInt, UInt32Constraints

logger = logging.getLogger()


def _find_resources(resource_name: str) -> Sequence[MacroResource | AtomicResource]:
    """Tries to locate resource by given name in resource database.

    Args:
        resource_name: Name of the resource to find.

    Returns:
        List with atomic resources or macro resource, or empty list when no resource with such name exists.
    """
    macro_resource = ResourceDatabaseProvider.get_database().find_macro_resource(resource_name)
    if macro_resource is not None:
        return [macro_resource]
    return ResourceDatabaseProvider.get_database().find_atomic_resource_by("name", resource_name)


def _create_parameters_list(params: Dict[str, Any]) -> List[str]:
    """Creates list of assignment string from given dictionary.

    Args:
        params: Dictionary of parameters to convert.

    Returns:
        List of assignment strings in format "key=value".
    """
    parameters_list = []
    for param in params:
        parameters_list.append(f"{param}={params[param]}")
    return parameters_list


def _expand_resource_to_atoms(resource: AtomicResource | MacroResource) -> List[AtomicResource]:
    """Expands the given resource to list of atomic resources.

    Args:
        resource: Resource to expand (atomic or macro).

    Returns:
        List of atomic resources. If macro resource is passed then all atomic resources from that macro are returned.
    """
    if isinstance(resource, AtomicResource):
        return [resource]
    if isinstance(resource, MacroResource):
        macro_resource = typing.cast(MacroResource, resource)
        return macro_resource.get_atomic_resources()
    return []


class ConfigLoader:
    """Loader class that parses JSON to objects stored in configuration data."""

    @classmethod
    def load_configuration_handle_start_stops(cls, msel: MSEL, json_msel: Any, ss_sequences: Any) -> None:
        """Loads information about start/stops in logical machine from JSON object.

        Args:
            msel: MSEL object to load start/stops into.
            json_msel: JSON object containing MSEL configuration.
            ss_sequences: Start/stop sequences data.
        """
        starts = []
        source = "/".join(["user_config", msel.get_lm().get_name(), f"MSEL{msel.get_msel()}", "start"])
        for sequence in ss_sequences:
            if sequence["ss"] == json_msel["start"]:
                starts = sequence["resources"]
                break
        if not starts and json_msel["start"] is not None:
            start = json_msel["start"]
            validation_id = ".".join([msel.get_lm().get_id(), f"SS{start}"])
            logger.error("Start sequence '%s' for MSEL%s is not initialized", start, msel.get_msel(), extra={"source": source, "validation_id": validation_id})
        for start in starts:
            resource_name = start["rsrc"]
            resources = _find_resources(resource_name)
            if not resources:
                validation_id = ".".join([msel.get_lm().get_id(), f"SS{json_msel['start']}", resource_name])
                logger.warning("Macro '%s' was not found.", resource_name, extra={"source": source, "validation_id": validation_id})
                continue
            start_value = str(starts.index(start) + 1)
            if "args" in start:
                args = start["args"]
                for arg in args:
                    start_value += "|" + str(arg)
            test = start["test"] if "test" in start else False
            for resource in resources:
                expanded_resource = _expand_resource_to_atoms(resource)
                for atom in expanded_resource:
                    msel.add_start_stop(True, test, atom, start_value)

        stops = []
        source = "/".join(["user_config", msel.get_lm().get_id(), "MSEL" + str(msel.get_msel()), "stop"])
        for sequence in ss_sequences:
            if sequence["ss"] == json_msel["stop"]:
                stops = sequence["resources"]
                break
        if not stops and json_msel["stop"] is not None:
            stop = json_msel["stop"]
            validation_id = ".".join([msel.get_lm().get_id(), f"SS{stop}"])
            logger.error("Stop sequence '%s' for MSEL%s is not initialized", stop, msel.get_msel(), extra={"source": source, "validation_id": validation_id})
        for stop in stops:
            resource_name = stop["rsrc"]
            resources = _find_resources(resource_name)
            if not resources:
                validation_id = ".".join([msel.get_lm().get_id(), f"SS{json_msel['stop']}", resource_name])
                logger.warning("Macro '%s' was not found.", resource_name, extra={"source": source, "validation_id": validation_id})
                continue
            stop_value = str(stops.index(stop) + 1)
            if "args" in stop:
                args = stop["args"]
                for arg in args:
                    stop_value += "|" + str(arg)
            test = stop["test"] if "test" in stop else False
            for resource in resources:
                expanded_resource = _expand_resource_to_atoms(resource)
                for atom in expanded_resource:
                    msel.add_start_stop(False, test, atom, stop_value)

    @classmethod
    def load_configuration_handle_defines(cls, owner: ResourceOwner, json_defines: Any) -> None:
        """Loads information about defines in resource owner from JSON object.

        Args:
            owner: Resource owner to assign defines to.
            json_defines: JSON object containing defines.
        """
        for define in json_defines:
            name = define["name"]
            params = define["params"]
            params_str = " ".join(f"{key}={val}" for key, val in params.items())
            define = AssignedDefine(name, params_str)
            owner.assign_define(define)

    @classmethod
    def load_configuration_assign_resources(cls, target: ResourceOwner, json_resources: Any, common_defines: Dict[str, AssignedDefine]) -> None:
        """Assigns resources from JSON object to given owner.

        Args:
            target: Resource owner to assign resources to.
            json_resources: JSON object containing resource definitions.
            common_defines: Dictionary of common define assignments.
        """
        for json_resource in json_resources:
            resource_name = json_resource["name"]
            defines = json_resource["defines"]
            params = json_resource["params"]
            origin = json_resource["dirty_flag"] if "dirty_flag" in json_resource else True

            defines_list = []
            params_dict: Dict[str, str] = {}
            for define in defines:
                assigned_define = target.get_define(define)
                if assigned_define is None:
                    # If resource owner is an agent, check defines in the agent's owner (LM)
                    if isinstance(target, ScmiAgent):
                        owner = target.get_owner()
                        if owner is not None:
                            assigned_define = owner.get_define(define)
                    if assigned_define is None and define in common_defines:
                        assigned_define = common_defines[define]
                if assigned_define is not None:
                    defines_list.append(assigned_define)
                    params_dict |= assigned_define.get_params()
                else:
                    source = "/".join(["user_config", target.get_name(), resource_name, define])
                    validation_id = ".".join([target.get_id(), "RESOURCES", resource_name, "DEFINE", define])
                    logger.error("Unknown define '%s' used for resource '%s'", define, resource_name, extra={"source": source, "validation_id": validation_id})
            params_dict |= params
            parameters_list = _create_parameters_list(params_dict)

            ignore_api_check = target.get_id() == "LM0" or (isinstance(target, ScmiAgent) and target.get_owner().get_id() == "LM0") or isinstance(target, DOM)
            for resource in _find_resources(resource_name):
                target.assign_resource(resource, parameters_list, defines_list, origin, ignore_api_check)

    @classmethod
    def load_configuration_handle_agents(cls, logical_machine: LM, agents: Any, agents_count: int, common_defines: Dict[str, AssignedDefine]) -> None:
        """Loads information about agents in logical machine from JSON object.

        Args:
            logical_machine: Logical machine to add agents to.
            agents: JSON object containing agent definitions.
            agents_count: Current count of agents for ID generation.
            common_defines: Dictionary of common define assignments.
        """
        sm_num_mb_mu_db = 4
        for agent_index, agent in enumerate(agents):
            agent_id = "SCMI_AGENT" + str(agents_count + agent_index)
            secure = agent["secure"]
            scmi_agent = ScmiAgent(agent_id, logical_machine, agent["name"], secure, logical_machine.get_safe(), logical_machine.get_did())
            origin = agent["dirty_flag"] if "dirty_flag" in agent else True
            scmi_agent.set_dirty_flag(origin)
            json_mailbox = agent["mailbox"]
            mailbox_type = json_mailbox["type"]
            mailbox: Mailbox | None = None
            test = json_mailbox["test"] if "test" in json_mailbox.keys() else None
            priority = json_mailbox["priority"] if "priority" in json_mailbox.keys() else None
            if mailbox_type == "mu":
                sma = json_mailbox["sma"] if "sma" in json_mailbox.keys() else None
                if sma is not None:
                    tmp = FormatedInt(sma)
                    if tmp.get_value() > UInt32Constraints.MAX_VALUE:
                        source = "/".join(["user_config", logical_machine.get_id(), scmi_agent.get_id(), "SMA"])
                        validation_id = ".".join([scmi_agent.get_id(), "SMA"])
                        logger.error(
                            "SMA address %s exceeds maximum 32-bit value",
                            tmp,
                            extra={"source": source, "validation_id": validation_id},
                        )
                        sma = None
                mailbox = MailboxMu(json_mailbox["mu"], test, sma, priority)
            elif mailbox_type == "loopback":
                mailbox = MailboxLoopback(test, priority)

            json_channels = agent["channels"]
            for index, json_channel in enumerate(json_channels):
                channel_type = json_channel["type"]
                sequence = json_channel["sequence"] if "sequence" in json_channel.keys() else None
                test = json_channel["test"] if "test" in json_channel.keys() else None
                if channel_type == "scmi":
                    rpc_channel = ScmiChannel(scmi_agent, json_channel["chtype"], sequence, test, str(json_channel["notify"]))
                    json_xport = json_channel["xport"]
                    xport_type = json_xport["type"]
                    if xport_type == "smt":
                        doorbell_index = json_xport["doorbell"]
                        if doorbell_index >= sm_num_mb_mu_db:
                            source = "/".join(["user_config", logical_machine.get_id(), scmi_agent.get_id()])
                            validation_id = ".".join([scmi_agent.get_id(), "RPC_CHANNELS", str(index), "DB"])
                            logger.error(
                                "Doorbell index '%i' for channel in agent '%s' out of range",
                                doorbell_index,
                                scmi_agent.get_id(),
                                extra={"source": source, "validation_id": validation_id},
                            )
                        xport_channel = SmtChannel(doorbell_index, json_xport["check"])
                        if mailbox is not None:
                            xport_channel.set_mailbox(mailbox)
                        xport_channel.set_rpc_channel(rpc_channel)
                        rpc_channel.set_xport_channel(xport_channel)
                    scmi_agent.add_channel(rpc_channel)
            if mailbox is not None:
                scmi_agent.add_mailbox(mailbox)

            if "defines" in agent:
                json_defines = agent["defines"]
                cls.load_configuration_handle_defines(scmi_agent, json_defines)

            logical_machine.add_agent(scmi_agent)

            if "dup" in agent:
                dup_int = agent["dup"]
                dup_agents = [x for x in logical_machine.get_all_agents() if x.get_id() == ("SCMI_AGENT" + str(dup_int))]
                if len(dup_agents) == 1:
                    scmi_agent.duplicate(dup_agents[0], dup_int)
                else:
                    source = "/".join(["user_config", logical_machine.get_id(), scmi_agent.get_name()])
                    validation_id = ".".join([scmi_agent.get_id(), "DUP"])
                    logger.error(
                        "Agent %s cannot duplicate agent with index %s",
                        scmi_agent.get_name(),
                        dup_int,
                        extra={"source": source, "validation_id": validation_id},
                    )
            elif "resources" in agent:
                cls.load_configuration_assign_resources(scmi_agent, agent["resources"], common_defines)
            else:
                validation_id = ".".join([scmi_agent.get_id(), "NO_RESOURCES"])
                source = "/".join(["user_config", logical_machine.get_id(), scmi_agent.get_name()])
                logger.error(
                    "Agent %s has neither 'dup' nor 'resources' defined",
                    scmi_agent.get_name(),
                    extra={"source": source, "validation_id": validation_id},
                )

    @classmethod
    def load_configuration_handle_logical_machines(cls, logical_machines: Any, common_defines: Dict[str, AssignedDefine]) -> List[LM]:
        """Loads information about logical machines from JSON object.

        Args:
            logical_machines: JSON object containing logical machine definitions.
            common_defines: Dictionary of common define assignments.
        """
        agents_count = 0
        lms: List[LM] = []
        for lm_index, json_logical_machine in enumerate(logical_machines):
            lm_id = "LM" + str(lm_index)
            lm_name = json_logical_machine["name"]
            did = json_logical_machine["did"]
            origin = json_logical_machine["dirty_flag"] if "dirty_flag" in json_logical_machine else True
            debug = json_logical_machine["debug"]
            ss_sequences = json_logical_machine["ss_sequences"]
            json_msels = json_logical_machine["msels"]
            rpc = json_logical_machine["rpc"]
            safe = json_logical_machine["safe"]

            rtime = json_logical_machine["rtime"]
            auto = json_logical_machine["auto"]
            group = json_logical_machine["group"]
            default = json_logical_machine["default"]

            logical_machine = LM(lm_id, did, lm_name, rpc, rtime, safe, group, auto, default)
            logical_machine.set_dirty_flag(origin)
            logical_machine.set_debug(debug)
            for json_msel in json_msels:
                msel = logical_machine.get_msel(json_msel["msel"], json_msel["boot"], json_msel["skip"])
                cls.load_configuration_handle_start_stops(msel, json_msel, ss_sequences)

            if "defines" in json_logical_machine:
                json_defines = json_logical_machine["defines"]
                cls.load_configuration_handle_defines(logical_machine, json_defines)

            if "resources" in json_logical_machine:
                json_resources = json_logical_machine["resources"]
                cls.load_configuration_assign_resources(logical_machine, json_resources, common_defines)

            if "agents" in json_logical_machine:
                agents = json_logical_machine["agents"]
                cls.load_configuration_handle_agents(logical_machine, agents, agents_count, common_defines)
                agents_count += len(agents)
            lms.append(logical_machine)

        return lms

    @classmethod
    def load_config_handle_domains(cls, domains: Any, common_defines: Dict[str, AssignedDefine]) -> List[DOM]:
        """Loads information about domains from JSON object.

        Args:
            domains: JSON object containing domain definitions.
            common_defines: Dictionary of common define assignments.
        """
        doms: List[DOM] = []
        for json_domain in domains:
            did = json_domain["did"]
            domain_id = "DOM" + str(did)
            name = json_domain["name"]
            debug = json_domain["debug"]
            json_resources = json_domain["resources"]
            origin = json_domain["dirty_flag"] if "dirty_flag" in json_domain else True
            domain = DOM(domain_id, did, name)

            domain.set_debug(debug)
            domain.set_dirty_flag(origin)
            doms.append(domain)

            if "defines" in json_domain:
                json_defines = json_domain["defines"]
                cls.load_configuration_handle_defines(domain, json_defines)

            cls.load_configuration_assign_resources(domain, json_resources, common_defines)
        return doms
