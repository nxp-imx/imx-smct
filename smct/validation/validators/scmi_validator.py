#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Module with SCMI protocol related validations"""
import logging
import re
from typing import List

from smct import utils
from smct.configuration.confdata import ConfigurationData
from smct.validation.validation_entry import ValidationEntry
from smct.validation.validator_base import ValidatorBase


def _validate_agent_ids(configuration: ConfigurationData, result: List[ValidationEntry]) -> None:
    """Checks validity of SCMI agent IDs.

    Args:
        configuration: The configuration data to validate
        result: List to append validation entries to
    """
    pattern = re.compile(r"SCMI_AGENT(\d+)")
    all_agents = configuration.get_all_scmi_agents()
    ids = []
    for agent in all_agents:
        match = pattern.match(agent.get_id())
        if match is not None:
            ids.append(utils.parse_int(match.group(1)))
    agents_amount = len(all_agents)
    if len(ids) == 0:
        return
    highest_id = max(ids)
    lowest_id = min(ids)
    if lowest_id != 0:
        source = "/".join(["user_config", f"SCMI_AGENT{lowest_id}"])
        msg = f"Agent IDs must start from 0, but there is no AGENT0 in the configuration. Lowest ID is {lowest_id}"
        result.append(ValidationEntry(logging.ERROR, source, msg, f"AGENT{lowest_id}.ID"))
    if highest_id >= agents_amount:
        source = "/".join(["user_config", f"SCMI_AGENT{highest_id}"])
        msg = f"Agent {highest_id} has higher ID than there is amount of agents in total ({agents_amount})"
        result.append(ValidationEntry(logging.ERROR, source, msg, f"AGENT{highest_id}.ID"))
    if not utils.are_all_numbers_present(ids):
        result.append(ValidationEntry(logging.ERROR, "user_config", f"Agent IDs contain a gap: {ids}"))
    if not utils.are_numbers_consecutive(ids):
        result.append(ValidationEntry(logging.ERROR, "user_config", f"Agent IDs are not consecutive: {ids}"))


def _validate_channels(configuration: ConfigurationData, result: List[ValidationEntry]) -> None:
    """Checks validity of all SCMI channels.

    Args:
        configuration: The configuration data to validate
        result: List to append validation entries to
    """
    for agent in configuration.get_all_scmi_agents():
        source = "/".join(["user_config", agent.get_owner().get_name(), agent.get_name()])
        validation_id = ".".join([agent.get_id(), "RPC_CHANNELS"])
        a2p_counter = 0
        p2a_notify_counter = 0
        priority_counter = 0
        # Count channel types
        for channel in agent.get_all_scmi_channels():
            channel_type = channel.get_channel_type()
            match channel_type.lower():
                case "a2p":
                    a2p_counter += 1
                case "p2a_notify":
                    p2a_notify_counter += 1
                case "p2a_priority":
                    priority_counter += 1
        # Generate problem entries
        if a2p_counter == 0:
            msg = f"There must be at least one A2P channel in agent '{agent.get_name()}'"
            result.append(ValidationEntry(logging.ERROR, source, msg, validation_id))
        if p2a_notify_counter != 1:
            msg = f"There must be exactly one P2A_NOTIFY channel in agent '{agent.get_name()}'"
            result.append(ValidationEntry(logging.ERROR, source, msg, validation_id))
        if priority_counter > 1:
            msg = f"There must be maximally one P2A_PRIORITY channel in agent '{agent.get_name()}'"
            result.append(ValidationEntry(logging.ERROR, source, msg, validation_id))
    if configuration.get_default_test_channel() == -1 and configuration.get_all_channels():
        msg = "There must be at least one channel with parameter test=default"
        result.append(ValidationEntry(logging.ERROR, "user_config", msg))


def _validate_scmi_agents(configuration: ConfigurationData, result: List[ValidationEntry]) -> None:
    """Checks validity of all SCMI channels.

    Args:
        configuration: The configuration data to validate
        result: List to append validation entries to
    """
    for agent in configuration.get_all_scmi_agents():
        if not agent.get_assigned_resources():
            source = "/".join(["user_config", agent.get_owner().get_name(), agent.get_name()])
            validation_id = ".".join([agent.get_id(), "RESOURCES"])
            msg = f"There are no resources assigned in agent '{agent.get_name()}'"
            result.append(ValidationEntry(logging.WARNING, source, msg, validation_id))


class ScmiValidator(ValidatorBase):
    """Validator of SCMI"""

    def validate(self, configuration: ConfigurationData) -> List[ValidationEntry]:
        """Validates SCMI relates configuration.

        Args:
            configuration: The configuration data to validate

        Returns:
            List of validation entries containing any validation errors or warnings
        """
        result: List[ValidationEntry] = []
        _validate_agent_ids(configuration, result)
        _validate_channels(configuration, result)
        _validate_scmi_agents(configuration, result)
        return result
