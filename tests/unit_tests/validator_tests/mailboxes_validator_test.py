#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause

"""Unit tests for MailboxesValidator class"""

import logging
from unittest.mock import Mock, PropertyMock

from smct.configuration.confdata import ConfigurationData
from smct.owners.owner_agent import MailboxMu, ScmiAgent
from smct.owners.owner_lm import LM
from smct.validation.validators.mailboxes_validator import MailboxesValidator


def test_validate_no_mu_mailboxes() -> None:
    """Test validation when no MU mailboxes are present"""
    # Arrange
    mock_config = Mock(spec=ConfigurationData)
    mock_lm = Mock(spec=LM)
    mock_agent = Mock(spec=ScmiAgent)
    mock_mailbox = Mock()

    mock_agent.get_mailbox.return_value = mock_mailbox
    mock_lm.get_all_agents.return_value = [mock_agent]
    mock_config.get_all_lms.return_value = [mock_lm]

    validator = MailboxesValidator()

    # Act
    result = validator.validate(mock_config)

    # Assert
    assert result == []


def test_validate_single_mu_mailbox() -> None:
    """Test validation with single MU mailbox - no errors expected"""
    # Arrange
    mock_config = Mock(spec=ConfigurationData)
    mock_lm = Mock(spec=LM)
    mock_agent = Mock(spec=ScmiAgent)
    mock_mailbox = Mock(spec=MailboxMu)
    mock_owner = Mock()

    mock_mailbox.get_mu.return_value = 1
    mock_agent.get_mailbox.return_value = mock_mailbox
    mock_agent.get_owner.return_value = mock_owner
    mock_agent.get_name.return_value = "agent1"
    mock_agent.get_id.return_value = "agent1_id"
    mock_owner.get_name.return_value = "owner1"
    mock_lm.get_all_agents.return_value = [mock_agent]
    mock_config.get_all_lms.return_value = [mock_lm]
    type(mock_lm).mu_max_count = PropertyMock(return_value=1)

    validator = MailboxesValidator()

    # Act
    result = validator.validate(mock_config)

    # Assert
    assert result == []


def test_validate_duplicate_mu_mailboxes() -> None:
    """Test validation with duplicate MU mailboxes - should generate errors"""
    # Arrange
    mock_config = Mock(spec=ConfigurationData)
    mock_lm = Mock(spec=LM)
    mock_agent1 = Mock(spec=ScmiAgent)
    mock_agent2 = Mock(spec=ScmiAgent)
    mock_mailbox1 = Mock(spec=MailboxMu)
    mock_mailbox2 = Mock(spec=MailboxMu)
    mock_owner1 = Mock()
    mock_owner2 = Mock()

    # Both mailboxes use the same MU
    mock_mailbox1.get_mu.return_value = 1
    mock_mailbox2.get_mu.return_value = 1
    type(mock_lm).mu_max_count = PropertyMock(return_value=1)

    mock_agent1.get_mailbox.return_value = mock_mailbox1
    mock_agent1.get_owner.return_value = mock_owner1
    mock_agent1.get_name.return_value = "agent1"
    mock_agent1.get_id.return_value = "agent1_id"
    mock_owner1.get_name.return_value = "owner1"

    mock_agent2.get_mailbox.return_value = mock_mailbox2
    mock_agent2.get_owner.return_value = mock_owner2
    mock_agent2.get_name.return_value = "agent2"
    mock_agent2.get_id.return_value = "agent2_id"
    mock_owner2.get_name.return_value = "owner2"

    mock_lm.get_all_agents.return_value = [mock_agent1, mock_agent2]
    mock_config.get_all_lms.return_value = [mock_lm]

    validator = MailboxesValidator()

    # Act
    result = validator.validate(mock_config)

    # Assert
    assert len(result) == 2
    assert all(entry.get_level() == logging.ERROR for entry in result)
    expected_messages = ["Duplicate MU 1 used in agent agent1", "Duplicate MU 1 used in agent agent2"]
    actual_messages = [entry.get_error_message() for entry in result]
    assert set(actual_messages) == set(expected_messages)


def test_validate_multiple_lms_with_duplicate_mus() -> None:
    """Test validation across multiple LMs with duplicate MUs"""
    # Arrange
    mock_config = Mock(spec=ConfigurationData)
    mock_lm1 = Mock(spec=LM)
    mock_lm2 = Mock(spec=LM)
    mock_agent1 = Mock(spec=ScmiAgent)
    mock_agent2 = Mock(spec=ScmiAgent)
    mock_mailbox1 = Mock(spec=MailboxMu)
    mock_mailbox2 = Mock(spec=MailboxMu)
    mock_owner1 = Mock()
    mock_owner2 = Mock()

    # Both mailboxes use the same MU
    mock_mailbox1.get_mu.return_value = 2
    mock_mailbox2.get_mu.return_value = 2
    type(mock_lm1).mu_max_count = PropertyMock(return_value=2)
    type(mock_lm2).mu_max_count = PropertyMock(return_value=2)

    mock_agent1.get_mailbox.return_value = mock_mailbox1
    mock_agent1.get_owner.return_value = mock_owner1
    mock_agent1.get_name.return_value = "agent1"
    mock_agent1.get_id.return_value = "agent1_id"
    mock_owner1.get_name.return_value = "owner1"

    mock_agent2.get_mailbox.return_value = mock_mailbox2
    mock_agent2.get_owner.return_value = mock_owner2
    mock_agent2.get_name.return_value = "agent2"
    mock_agent2.get_id.return_value = "agent2_id"
    mock_owner2.get_name.return_value = "owner2"

    mock_lm1.get_all_agents.return_value = [mock_agent1]
    mock_lm2.get_all_agents.return_value = [mock_agent2]
    mock_config.get_all_lms.return_value = [mock_lm1, mock_lm2]

    validator = MailboxesValidator()

    # Act
    result = validator.validate(mock_config)

    # Assert
    assert len(result) == 2
    assert all(entry.get_level() == logging.ERROR for entry in result)
    expected_messages = ["Duplicate MU 2 used in agent agent1", "Duplicate MU 2 used in agent agent2"]
    actual_messages = [entry.get_error_message() for entry in result]
    assert set(actual_messages) == set(expected_messages)
