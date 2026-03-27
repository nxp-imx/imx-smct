#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause

"""Unit tests for ScmiValidator class"""

import logging
from unittest.mock import Mock

from smct.configuration.confdata import ConfigurationData
from smct.owners.owner_lm import LM
from smct.validation.validators.scmi_validator import ScmiValidator


def setup_test_data() -> tuple[ScmiValidator, ConfigurationData]:
    """Set up test fixtures"""
    validator = ScmiValidator()
    config = ConfigurationData()
    return validator, config


def test_validate_empty_configuration() -> None:
    """Test validation with no SCMI agents"""
    # Arrange
    validator, config = setup_test_data()

    # Act
    result = validator.validate(config)

    # Assert
    assert len(result) == 0


def test_validate_agent_ids_not_starting_from_zero_error() -> None:
    """Test validation error when SCMI agent IDs don't start from 0"""
    # Arrange
    validator, config = setup_test_data()

    agent1 = Mock()
    agent1.get_id.return_value = "SCMI_AGENT1"  # Starting from 1 instead of 0
    agent1.get_owner.return_value.get_name.return_value = "owner1"
    agent1.get_name.return_value = "agent1"
    agent1.get_all_scmi_channels.return_value = []
    agent1.get_assigned_resources.return_value = ["resource1"]

    agent2 = Mock()
    agent2.get_id.return_value = "SCMI_AGENT2"
    agent2.get_owner.return_value.get_name.return_value = "owner2"
    agent2.get_name.return_value = "agent2"
    agent2.get_all_scmi_channels.return_value = []
    agent2.get_assigned_resources.return_value = ["resource2"]

    config.get_all_scmi_agents = Mock(return_value=[agent1, agent2])
    config.get_default_test_channel = Mock(return_value=0)
    config.get_all_channels = Mock(return_value=[])

    # Act
    result = validator.validate(config)

    # Assert
    error_messages = [entry.get_error_message() for entry in result]
    error_entries = [entry for entry in result if entry.get_level() == logging.ERROR]
    assert len(error_entries) > 0
    assert "Agent IDs must start from 0, but there is no AGENT0 in the configuration. Lowest ID is 1" in error_messages


def test_validate_agent_ids_higher_than_total_amount_error() -> None:
    """Test validation error when agent ID is higher than total amount"""
    # Arrange
    validator, config = setup_test_data()

    agent1 = Mock()
    agent1.get_id.return_value = "SCMI_AGENT0"
    agent1.get_owner.return_value.get_name.return_value = "owner1"
    agent1.get_name.return_value = "agent1"
    agent1.get_all_scmi_channels.return_value = []
    agent1.get_assigned_resources.return_value = ["resource1"]

    agent2 = Mock()
    agent2.get_id.return_value = "SCMI_AGENT5"  # ID 5 but only 2 agents total
    agent2.get_owner.return_value.get_name.return_value = "owner2"
    agent2.get_name.return_value = "agent2"
    agent2.get_all_scmi_channels.return_value = []
    agent2.get_assigned_resources.return_value = ["resource2"]

    config.get_all_scmi_agents = Mock(return_value=[agent1, agent2])
    config.get_default_test_channel = Mock(return_value=0)
    config.get_all_channels = Mock(return_value=[])

    # Act
    result = validator.validate(config)

    # Assert
    error_messages = [entry.get_error_message() for entry in result]
    error_entries = [entry for entry in result if entry.get_level() == logging.ERROR]
    assert len(error_entries) > 0
    assert "Agent 5 has higher ID than there is amount of agents in total (2)" in error_messages


def test_validate_agent_ids_with_gaps_error() -> None:
    """Test validation error when agent IDs have gaps"""
    # Arrange
    validator, config = setup_test_data()

    agent1 = Mock()
    agent1.get_id.return_value = "SCMI_AGENT0"
    agent1.get_owner.return_value.get_name.return_value = "owner1"
    agent1.get_name.return_value = "agent1"
    agent1.get_all_scmi_channels.return_value = []
    agent1.get_assigned_resources.return_value = ["resource1"]

    agent2 = Mock()
    agent2.get_id.return_value = "SCMI_AGENT2"  # Gap: missing AGENT1
    agent2.get_owner.return_value.get_name.return_value = "owner2"
    agent2.get_name.return_value = "agent2"
    agent2.get_all_scmi_channels.return_value = []
    agent2.get_assigned_resources.return_value = ["resource2"]

    config.get_all_scmi_agents = Mock(return_value=[agent1, agent2])
    config.get_default_test_channel = Mock(return_value=0)
    config.get_all_channels = Mock(return_value=[])

    # Act
    result = validator.validate(config)

    # Assert
    error_messages = [entry.get_error_message() for entry in result]
    error_entries = [entry for entry in result if entry.get_level() == logging.ERROR]
    assert len(error_entries) > 0
    assert "Agent IDs contain a gap: [0, 2]" in error_messages


def test_validate_agent_ids_not_consecutive_error() -> None:
    """Test validation error when agent IDs are not consecutive"""
    # Arrange
    validator, config = setup_test_data()

    agent1 = Mock()
    agent1.get_id.return_value = "SCMI_AGENT2"
    agent1.get_owner.return_value.get_name.return_value = "owner1"
    agent1.get_name.return_value = "agent1"
    agent1.get_all_scmi_channels.return_value = []
    agent1.get_assigned_resources.return_value = ["resource1"]

    agent2 = Mock()
    agent2.get_id.return_value = "SCMI_AGENT5"
    agent2.get_owner.return_value.get_name.return_value = "owner2"
    agent2.get_name.return_value = "agent2"
    agent2.get_all_scmi_channels.return_value = []
    agent2.get_assigned_resources.return_value = ["resource2"]

    config.get_all_scmi_agents = Mock(return_value=[agent1, agent2])
    config.get_default_test_channel = Mock(return_value=0)
    config.get_all_channels = Mock(return_value=[])

    # Act
    result = validator.validate(config)

    # Assert
    error_messages = [entry.get_error_message() for entry in result]
    error_entries = [entry for entry in result if entry.get_level() == logging.ERROR]
    assert len(error_entries) > 0
    assert "Agent IDs are not consecutive: [2, 5]" in error_messages


# ============================================================================
# SCMI CHANNEL VALIDATION ERROR TESTS
# ============================================================================


def test_validate_channels_no_a2p_channel_error() -> None:
    """Test validation error when agent has no A2P channel"""
    # Arrange
    validator, config = setup_test_data()

    channel1 = Mock()
    channel1.get_channel_type.return_value = "p2a_notify"

    owner1 = Mock(spec=LM)
    owner1.get_name.return_value = "owner1"
    owner1.is_scmi.return_value = True

    agent1 = Mock()
    agent1.get_id.return_value = "SCMI_AGENT0"
    agent1.get_name.return_value = "agent1"
    agent1.get_owner.return_value = owner1
    agent1.get_all_scmi_channels.return_value = [channel1]
    agent1.get_assigned_resources.return_value = ["resource1"]

    config.get_all_scmi_agents = Mock(return_value=[agent1])
    config.get_default_test_channel = Mock(return_value=0)
    config.get_all_channels = Mock(return_value=[])

    # Act
    result = validator.validate(config)

    # Assert
    error_messages = [entry.get_error_message() for entry in result]
    error_entries = [entry for entry in result if entry.get_level() == logging.ERROR]
    assert len(error_entries) > 0
    assert "There must be at least one A2P channel in agent 'agent1'" in error_messages


def test_validate_channels_wrong_p2a_notify_count_error() -> None:
    """Test validation error when agent doesn't have exactly one P2A_NOTIFY channel"""
    # Arrange
    validator, config = setup_test_data()

    channel1 = Mock()
    channel1.get_channel_type.return_value = "a2p"

    channel2 = Mock()
    channel2.get_channel_type.return_value = "p2a_notify"

    channel3 = Mock()
    channel3.get_channel_type.return_value = "p2a_notify"  # Second P2A_NOTIFY

    owner1 = Mock(spec=LM)
    owner1.get_name.return_value = "owner1"
    owner1.is_scmi.return_value = True

    agent1 = Mock()
    agent1.get_id.return_value = "SCMI_AGENT0"
    agent1.get_owner.return_value = owner1
    agent1.get_name.return_value = "agent1"
    agent1.get_all_scmi_channels.return_value = [channel1, channel2, channel3]
    agent1.get_assigned_resources.return_value = ["resource1"]

    config.get_all_scmi_agents = Mock(return_value=[agent1])
    config.get_default_test_channel = Mock(return_value=0)
    config.get_all_channels = Mock(return_value=[])

    # Act
    result = validator.validate(config)

    # Assert
    error_messages = [entry.get_error_message() for entry in result]
    error_entries = [entry for entry in result if entry.get_level() == logging.ERROR]
    assert len(error_entries) > 0
    assert "There must be exactly one P2A_NOTIFY channel in agent 'agent1'" in error_messages


def test_validate_channels_multiple_p2a_priority_error() -> None:
    """Test validation error when agent has more than one P2A_PRIORITY channel"""
    # Arrange
    validator, config = setup_test_data()

    channel1 = Mock()
    channel1.get_channel_type.return_value = "a2p"

    channel2 = Mock()
    channel2.get_channel_type.return_value = "p2a_notify"

    channel3 = Mock()
    channel3.get_channel_type.return_value = "p2a_priority"

    channel4 = Mock()
    channel4.get_channel_type.return_value = "p2a_priority"  # Second P2A_PRIORITY

    owner1 = Mock(spec=LM)
    owner1.get_name.return_value = "owner1"
    owner1.is_scmi.return_value = True

    agent1 = Mock()
    agent1.get_id.return_value = "SCMI_AGENT0"
    agent1.get_owner.return_value = owner1
    agent1.get_name.return_value = "agent1"
    agent1.get_all_scmi_channels.return_value = [channel1, channel2, channel3, channel4]
    agent1.get_assigned_resources.return_value = ["resource1"]

    config.get_all_scmi_agents = Mock(return_value=[agent1])
    config.get_default_test_channel = Mock(return_value=0)
    config.get_all_channels = Mock(return_value=[])

    # Act
    result = validator.validate(config)

    # Assert
    error_messages = [entry.get_error_message() for entry in result]
    error_entries = [entry for entry in result if entry.get_level() == logging.ERROR]
    assert len(error_entries) > 0
    assert "There must be maximally one P2A_PRIORITY channel in agent 'agent1'" in error_messages


def test_validate_channels_no_default_test_channel_error() -> None:
    """Test validation error when there's no default test channel"""
    # Arrange
    validator, config = setup_test_data()

    channel1 = Mock()
    channel1.get_channel_type.return_value = "a2p"

    channel2 = Mock()
    channel2.get_channel_type.return_value = "p2a_notify"

    agent1 = Mock()
    agent1.get_id.return_value = "SCMI_AGENT0"
    agent1.get_owner.return_value.get_name.return_value = "owner1"
    agent1.get_name.return_value = "agent1"
    agent1.get_all_scmi_channels.return_value = [channel1, channel2]
    agent1.get_assigned_resources.return_value = ["resource1"]

    config.get_all_scmi_agents = Mock(return_value=[agent1])
    config.get_default_test_channel = Mock(return_value=-1)
    config.get_all_channels = Mock(return_value=[channel1])

    # Act
    result = validator.validate(config)

    # Assert
    error_messages = [entry.get_error_message() for entry in result]
    error_entries = [entry for entry in result if entry.get_level() == logging.ERROR]
    assert len(error_entries) > 0
    assert "There must be at least one channel with parameter test=default" in error_messages


def test_validate_scmi_agents_no_resources_warning() -> None:
    """Test validation warning when agent has no assigned resources"""
    # Arrange
    validator, config = setup_test_data()

    channel1 = Mock()
    channel1.get_channel_type.return_value = "a2p"

    channel2 = Mock()
    channel2.get_channel_type.return_value = "p2a_notify"

    agent1 = Mock()
    agent1.get_id.return_value = "SCMI_AGENT0"
    agent1.get_owner.return_value.get_name.return_value = "owner1"
    agent1.get_name.return_value = "agent1"
    agent1.get_all_scmi_channels.return_value = [channel1, channel2]
    agent1.get_assigned_resources.return_value = []

    config.get_all_scmi_agents = Mock(return_value=[agent1])
    config.get_default_test_channel = Mock(return_value=0)
    config.get_all_channels = Mock(return_value=[channel1])

    # Act
    result = validator.validate(config)

    # Assert
    warning_messages = [entry.get_error_message() for entry in result]
    warning_entries = [entry for entry in result if entry.get_level() == logging.WARNING]
    assert len(warning_entries) > 0
    assert "There are no resources assigned in agent 'agent1'" in warning_messages
