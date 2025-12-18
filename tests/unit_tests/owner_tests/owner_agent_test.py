#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Unit tests for ScmiAgent and related classes"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any

from smct.owners.owner_agent import ScmiAgent, Channel, MailboxMu, MailboxLoopback, SmtChannel, ScmiChannel, Mailbox
from smct.owners.owner_lm import LM
from smct.owners.owner_base import AssignedResource
from smct.expcetions.cfg_tool_exception import CfgToolException
from smct.utils import FormatedInt


def test_scmi_agent_init_valid_parameters() -> None:
    """Test ScmiAgent initialization with valid parameters"""
    mock_owner = Mock()
    
    agent = ScmiAgent("agent1", mock_owner, "TestAgent", True, "nseenv", 1)
    
    assert agent.get_id() == "agent1"
    assert agent.get_name() == "TestAgent"
    assert agent.get_secure() == 1
    assert agent.get_owner() == mock_owner
    assert agent.get_safe_type() == "nseenv"
    assert agent.get_did() == 1


def test_scmi_agent_init_with_defaults() -> None:
    """Test ScmiAgent initialization with default parameters"""
    mock_owner = Mock()
    
    agent = ScmiAgent("agent1", mock_owner, "TestAgent", False)
    
    assert agent.get_id() == "agent1"
    assert agent.get_name() == "TestAgent"
    assert agent.get_secure() == 0
    assert agent.get_owner() == mock_owner
    assert agent.get_safe_type() == "nseenv"
    assert agent.get_did() == -1


def test_scmi_agent_set_owner() -> None:
    """Test setting owner for ScmiAgent"""
    mock_owner1 = Mock()
    mock_owner2 = Mock()
    
    agent = ScmiAgent("agent1", mock_owner1, "TestAgent", True)
    agent.set_owner(mock_owner2)
    
    assert agent.get_owner() == mock_owner2


def test_scmi_agent_get_all_scmi_channels_empty() -> None:
    """Test getting SCMI channels when none exist"""
    mock_owner = Mock()
    agent = ScmiAgent("agent1", mock_owner, "TestAgent", True)
    
    channels = agent.get_all_scmi_channels()
    
    assert channels == []


def test_scmi_agent_get_all_xport_channels_empty() -> None:
    """Test getting XPORT channels when none exist"""
    mock_owner = Mock()
    agent = ScmiAgent("agent1", mock_owner, "TestAgent", True)
    
    channels = agent.get_all_xport_channels()

    assert channels == []


def test_scmi_agent_get_all_channels_empty() -> None:
    """Test getting all channels when none exist"""
    mock_owner = Mock()
    agent = ScmiAgent("agent1", mock_owner, "TestAgent", True)
    
    channels = agent.get_all_channels()

    assert channels == []


def test_scmi_agent_get_mailbox_none() -> None:
    """Test getting mailbox when none is set"""
    mock_owner = Mock()
    agent = ScmiAgent("agent1", mock_owner, "TestAgent", True)
    
    assert agent.get_mailbox() is None


def test_scmi_agent_add_mailbox() -> None:
    """Test adding mailbox to ScmiAgent"""
    mock_owner = Mock()
    agent = ScmiAgent("agent1", mock_owner, "TestAgent", True)
    
    Mailbox.mailbox_types = {"mu": "MU", "loopback": "LOOPBACK"}
    Mailbox.mailbox_priority_types = {"very_low": "VERY_LOW"}
    
    mailbox = MailboxMu(5, None, None, None)
    agent.add_mailbox(mailbox)
    
    assert agent.get_mailbox() == mailbox
    assert mailbox.get_owner() == agent


def test_scmi_agent_add_mailbox_already_owned() -> None:
    """Test adding mailbox that's already owned by another agent"""
    mock_owner = Mock()
    agent1 = ScmiAgent("agent1", mock_owner, "TestAgent1", True)
    agent2 = ScmiAgent("agent2", mock_owner, "TestAgent2", True)
    
    Mailbox.mailbox_types = {"mu": "MU"}
    Mailbox.mailbox_priority_types = {"very_low": "VERY_LOW"}
    
    mailbox = MailboxMu(5, None, None, None)
    mailbox.set_owner(agent1)
    
    with pytest.raises(CfgToolException, match="Cannot re-assign already used MAILBOX"):
        agent2.add_mailbox(mailbox)


def test_scmi_agent_add_multiple_mailboxes() -> None:
    """Test adding multiple mailboxes to same agent raises exception"""
    mock_owner = Mock()
    agent = ScmiAgent("agent1", mock_owner, "TestAgent", True)
    
    Mailbox.mailbox_types = {"mu": "MU", "loopback": "LOOPBACK"}
    Mailbox.mailbox_priority_types = {"very_low": "VERY_LOW"}
    
    mailbox1 = MailboxMu(5, None, None, None)
    mailbox2 = MailboxLoopback(None, None)
    
    agent.add_mailbox(mailbox1)
    
    with pytest.raises(CfgToolException, match="SCMI_AGENT can only handle one MAILBOX"):
        agent.add_mailbox(mailbox2)


def test_scmi_agent_add_channel() -> None:
    """Test adding SCMI channel to agent"""
    mock_owner = Mock()
    agent = ScmiAgent("agent1", mock_owner, "TestAgent", True)
    
    ScmiChannel.channel_types = {"a2p": "A2P"}
    ScmiChannel.sequence_types = {"none": "NONE"}
    
    channel = ScmiChannel(agent, "a2p", None, None, None)
    agent.add_channel(channel)
    
    channels = agent.get_all_scmi_channels()
    assert len(channels) == 1
    assert channels[0] == channel
    assert channel.get_agent() == agent


def test_scmi_agent_add_channel_already_assigned() -> None:
    """Test adding channel that's already assigned to another agent"""
    mock_owner = Mock()
    agent1 = ScmiAgent("agent1", mock_owner, "TestAgent1", True)
    agent2 = ScmiAgent("agent2", mock_owner, "TestAgent2", True)
    
    ScmiChannel.channel_types = {"a2p": "A2P"}
    ScmiChannel.sequence_types = {"none": "NONE"}
    
    channel = ScmiChannel(agent1, "a2p", None, None, None)
    
    with pytest.raises(CfgToolException, match="Cannot re-assign CHANNEL to a different agent"):
        agent2.add_channel(channel)


def test_scmi_agent_get_assignment_json() -> None:
    """Test getting assignment JSON for ScmiAgent"""
    mock_owner = Mock()
    agent = ScmiAgent("agent1", mock_owner, "TestAgent", True, "nseenv", 5)
    
    json_data = agent.get_assignment_json()
    
    assert json_data["type"] == "SCMI_AGENT"
    assert json_data["name"] == "TestAgent"
    assert json_data["secure"] == True
    assert json_data["channels"] == []
    assert "mailbox" not in json_data


def test_scmi_agent_get_assignment_json_with_mailbox() -> None:
    """Test getting assignment JSON with mailbox"""
    mock_owner = Mock()
    agent = ScmiAgent("agent1", mock_owner, "TestAgent", True)
    
    Mailbox.mailbox_types = {"mu": "MU"}
    Mailbox.mailbox_priority_types = {"very_low": "VERY_LOW"}
    
    mailbox = MailboxMu(5, None, None, None)
    agent.add_mailbox(mailbox)
    
    json_data = agent.get_assignment_json()
    
    assert "mailbox" in json_data
    assert json_data["mailbox"]["type"] == "mu"
    assert json_data["mailbox"]["mu"] == 5
    

def test_scmi_agent_repr_representation() -> None:
    """Test repr representation of ScmiAgent"""
    mock_owner = Mock()
    agent = ScmiAgent("agent1", mock_owner, "TestAgent", True, "nseenv", 5)
    
    expected = "ScmiAgent('agent1', 5, 'TestAgent', True, 'nseenv', 5)"
    assert repr(agent) == expected


def test_mailbox_mu_init() -> None:
    """Test MailboxMu initialization"""
    Mailbox.mailbox_types = {"mu": "MU"}
    Mailbox.mailbox_priority_types = {"very_low": "VERY_LOW"}
    
    sma = FormatedInt("0x1000")
    mailbox = MailboxMu(5, None, sma, "very_low")
    
    assert mailbox.get_mu() == 5
    assert mailbox.get_sma() == sma
    assert mailbox.get_type() == "mu"
    assert mailbox.get_priority() == "very_low"


def test_mailbox_mu_get_assignment_json() -> None:
    """Test getting assignment JSON for MailboxMu"""
    Mailbox.mailbox_types = {"mu": "MU"}
    Mailbox.mailbox_priority_types = {"very_low": "VERY_LOW"}
    
    sma = FormatedInt("0x2000")
    mailbox = MailboxMu(3, 1, sma, "very_low")
    
    json_data = mailbox.get_assignment_json()
    
    assert json_data["type"] == "mu"
    assert json_data["mu"] == 3
    assert json_data["test"] == 1
    assert json_data["sma"] == sma
    assert json_data["priority"] == "very_low"


def test_mailbox_loopback_init() -> None:
    """Test MailboxLoopback initialization"""
    Mailbox.mailbox_types = {"loopback": "LOOPBACK"}
    Mailbox.mailbox_priority_types = {"very_low": "VERY_LOW"}
    
    mailbox = MailboxLoopback(2, "very_low")
    
    assert mailbox.get_type() == "loopback"
    assert mailbox.get_test() == 2
    assert mailbox.get_priority() == "very_low"


def test_mailbox_set_doorbell_channel() -> None:
    """Test setting doorbell channel for mailbox"""
    Mailbox.mailbox_types = {"mu": "MU"}
    Mailbox.mailbox_priority_types = {"very_low": "VERY_LOW"}
    
    mailbox = MailboxMu(5, None, None, None)
    channel = Mock(spec=Channel)
    channel.get_type.return_value = "smt"
    
    mailbox.set_doorbell_channel(0, channel)
    
    doorbell_channels = mailbox.get_doorbell_channels()
    assert len(doorbell_channels) == 1
    assert doorbell_channels[0] == channel


def test_mailbox_set_doorbell_channel_negative() -> None:
    """Test setting doorbell channel with negative doorbell number"""
    Mailbox.mailbox_types = {"mu": "MU"}
    Mailbox.mailbox_priority_types = {"very_low": "VERY_LOW"}
    
    mailbox = MailboxMu(5, None, None, None)
    channel = Mock(spec=Channel)
    channel.get_type.return_value = "smt"
    
    with patch('smct.owners.owner_agent.logger') as mock_logger:
        mailbox.set_doorbell_channel(-1, channel)
        mock_logger.error.assert_called_once()


def test_channel_init() -> None:
    """Test Channel initialization"""
    channel = Channel()
    
    assert channel.get_type() == "none"


def test_channel_get_assignment_json() -> None:
    """Test getting assignment JSON for Channel"""
    channel = Channel()
    
    json_data = channel.get_assignment_json()
    
    assert json_data["type"] == "none"


def test_smt_channel_init() -> None:
    """Test SmtChannel initialization"""
    SmtChannel.smt_crc_types = {"none": "NONE", "crc": "CRC"}
    
    channel = SmtChannel(1, "crc")
    
    assert channel.get_type() == "smt"
    assert channel.get_doorbell() == 1
    assert channel.get_check() == "crc"


def test_smt_channel_init_invalid_check() -> None:
    """Test SmtChannel initialization with invalid check type"""
    SmtChannel.smt_crc_types = {"none": "NONE", "crc": "CRC"}
    
    with patch('smct.owners.owner_agent.logger') as mock_logger:
        channel = SmtChannel(1, "invalid_check")
        mock_logger.error.assert_called_once()


def test_smt_channel_set_mailbox() -> None:
    """Test setting mailbox for SmtChannel"""
    SmtChannel.smt_crc_types = {"none": "NONE"}
    Mailbox.mailbox_types = {"mu": "MU"}
    Mailbox.mailbox_priority_types = {"very_low": "VERY_LOW"}
    
    channel = SmtChannel(0, None)
    mailbox = MailboxMu(5, None, None, None)
    
    channel.set_mailbox(mailbox)
    
    assert channel.get_mailbox() == mailbox


def test_smt_channel_set_rpc_channel() -> None:
    """Test setting RPC channel for SmtChannel"""
    SmtChannel.smt_crc_types = {"none": "NONE"}
    
    smt_channel = SmtChannel(0, None)
    rpc_channel = Mock(spec=Channel)
    
    smt_channel.set_rpc_channel(rpc_channel)
    
    assert smt_channel.get_rpc_channel() == rpc_channel


def test_smt_channel_get_assignment_json() -> None:
    """Test getting assignment JSON for SmtChannel"""
    SmtChannel.smt_crc_types = {"crc": "CRC"}
    
    channel = SmtChannel(2, "crc")
    
    json_data = channel.get_assignment_json()
    
    assert json_data["type"] == "smt"
    assert json_data["doorbell"] == 2
    assert json_data["check"] == "crc"


def test_scmi_channel_init() -> None:
    """Test ScmiChannel initialization"""
    mock_agent = Mock(spec=ScmiAgent)
    mock_agent.get_id.return_value = "agent1"
    
    ScmiChannel.channel_types = {"a2p": "A2P"}
    ScmiChannel.sequence_types = {"none": "NONE"}
    
    channel = ScmiChannel(mock_agent, "a2p", "none", "test1", "5")
    
    assert channel.get_type() == "scmi"
    assert channel.get_agent() == mock_agent
    assert channel.get_channel_type() == "a2p"
    assert channel.get_sequence() == "none"
    assert channel.get_test() == "test1"
    assert channel.get_notify() == 5


def test_scmi_channel_init_invalid_channel_type() -> None:
    """Test ScmiChannel initialization with invalid channel type"""
    mock_agent = Mock(spec=ScmiAgent)
    
    ScmiChannel.channel_types = {"a2p": "A2P"}
    
    with pytest.raises(CfgToolException, match="Unknown SCMI CHANNEL type"):
        ScmiChannel(mock_agent, "invalid_type", None, None, None)


def test_scmi_channel_init_invalid_sequence() -> None:
    """Test ScmiChannel initialization with invalid sequence type"""
    mock_agent = Mock(spec=ScmiAgent)
    mock_agent.get_id.return_value = "agent1"
    
    ScmiChannel.channel_types = {"a2p": "A2P"}
    ScmiChannel.sequence_types = {"none": "NONE"}
    
    with patch('smct.owners.owner_agent.logger') as mock_logger:
        channel = ScmiChannel(mock_agent, "a2p", "invalid_sequence", None, None)
        mock_logger.error.assert_called_once()


def test_scmi_channel_set_xport_channel() -> None:
    """Test setting XPORT channel for ScmiChannel"""
    mock_agent = Mock(spec=ScmiAgent)
    
    ScmiChannel.channel_types = {"a2p": "A2P"}
    
    scmi_channel = ScmiChannel(mock_agent, "a2p", None, None, None)
    xport_channel = Mock(spec=Channel)
    
    scmi_channel.set_xport_channel(xport_channel)
    
    assert scmi_channel.get_xport_channel() == xport_channel


def test_scmi_channel_set_agent() -> None:
    """Test setting agent for ScmiChannel"""
    mock_agent1 = Mock(spec=ScmiAgent)
    mock_agent2 = Mock(spec=ScmiAgent)
    
    ScmiChannel.channel_types = {"a2p": "A2P"}
    
    channel = ScmiChannel(mock_agent1, "a2p", None, None, None)
    channel.set_agent(mock_agent2)
    
    assert channel.get_agent() == mock_agent2


def test_scmi_channel_get_assignment_json() -> None:
    """Test getting assignment JSON for ScmiChannel"""
    mock_agent = Mock(spec=ScmiAgent)
    
    ScmiChannel.channel_types = {"a2p": "A2P"}
    ScmiChannel.sequence_types = {"seq1": "SEQ1"}
    
    channel = ScmiChannel(mock_agent, "a2p", "seq1", "test_val", "10")
    xport_channel = Mock(spec=Channel)
    xport_channel.get_assignment_json.return_value = {"type": "smt"}
    channel.set_xport_channel(xport_channel)
    
    json_data = channel.get_assignment_json()
    
    assert json_data["type"] == "scmi"
    assert json_data["chtype"] == "a2p"
    assert json_data["sequence"] == "seq1"
    assert json_data["test"] == "test_val"
    assert json_data["notify"] == 10
    assert json_data["xport"] == {"type": "smt"}


def test_scmi_channel_get_assignment_json_no_xport() -> None:
    """Test getting assignment JSON for ScmiChannel without XPORT channel"""
    mock_agent = Mock(spec=ScmiAgent)
    
    ScmiChannel.channel_types = {"a2p": "A2P"}
    
    channel = ScmiChannel(mock_agent, "a2p", None, None, None)
    
    json_data = channel.get_assignment_json()
    
    assert json_data["type"] == "scmi"
    assert json_data["chtype"] == "a2p"
    assert json_data["sequence"] is None
    assert json_data["test"] is None
    assert json_data["notify"] == 0
    assert "xport" not in json_data


def test_scmi_channel_get_channel_type_define() -> None:
    """Test getting channel type define value"""
    mock_agent = Mock(spec=ScmiAgent)
    
    ScmiChannel.channel_types = {"a2p": "A2P_DEFINE", "p2a": "P2A_DEFINE"}
    
    channel_a2p = ScmiChannel(mock_agent, "a2p", None, None, None)
    channel_p2a = ScmiChannel(mock_agent, "p2a", None, None, None)
    
    assert channel_a2p.get_channel_type_define() == "A2P_DEFINE"
    assert channel_p2a.get_channel_type_define() == "P2A_DEFINE"


def test_scmi_channel_get_channel_sequence_define() -> None:
    """Test getting channel sequence define value"""
    mock_agent = Mock(spec=ScmiAgent)
    
    ScmiChannel.channel_types = {"a2p": "A2P"}
    ScmiChannel.sequence_types = {"seq1": "SEQ1_DEFINE", "none": "NONE_DEFINE"}
    
    channel_with_seq = ScmiChannel(mock_agent, "a2p", "seq1", None, None)
    channel_no_seq = ScmiChannel(mock_agent, "a2p", None, None, None)
    
    assert channel_with_seq.get_channel_sequence_define() == "SEQ1_DEFINE"
    assert channel_no_seq.get_channel_sequence_define() == "NONE_DEFINE"


def test_mailbox_get_type_define() -> None:
    """Test getting mailbox type define value"""
    Mailbox.mailbox_types = {"mu": "MU_DEFINE", "loopback": "LOOPBACK_DEFINE", "none": "NONE_DEFINE"}
    Mailbox.mailbox_priority_types = {"very_low": "VERY_LOW"}
    
    mu_mailbox = MailboxMu(5, None, None, None)
    loopback_mailbox = MailboxLoopback(None, None)
    
    assert mu_mailbox.get_type_define() == "MU_DEFINE"
    assert loopback_mailbox.get_type_define() == "LOOPBACK_DEFINE"


def test_mailbox_get_priority_define() -> None:
    """Test getting mailbox priority define value"""
    Mailbox.mailbox_types = {"mu": "MU"}
    Mailbox.mailbox_priority_types = {"high": "HIGH_DEFINE", "very_low": "VERY_LOW_DEFINE"}
    
    high_priority_mailbox = MailboxMu(5, None, None, "high")
    low_priority_mailbox = MailboxMu(3, None, None, None)
    
    assert high_priority_mailbox.get_priority_define() == "HIGH_DEFINE"
    assert low_priority_mailbox.get_priority_define() == "VERY_LOW_DEFINE"


def test_smt_channel_get_check_define() -> None:
    """Test getting SMT channel check define value"""
    SmtChannel.smt_crc_types = {"crc": "CRC_DEFINE", "none": "NONE_DEFINE"}
    
    crc_channel = SmtChannel(1, "crc")
    no_check_channel = SmtChannel(2, None)
    
    assert crc_channel.get_check_define() == "CRC_DEFINE"
    assert no_check_channel.get_check_define() == "NONE_DEFINE"


def test_channel_get_xport_type_invalid() -> None:
    """Test getting XPORT type for invalid channel type"""
    Channel.xport_types = {"smt": "SMT_XPORT", "none": "NONE_XPORT"}
    
    channel = Channel()
    channel._type = "invalid_type"
    
    with patch('smct.owners.owner_agent.logger') as mock_logger:
        result = channel.get_xport_type()
        assert result == "NONE_XPORT"
        mock_logger.error.assert_called_once()


def test_channel_get_rpc_type_invalid() -> None:
    """Test getting RPC type for invalid channel type"""
    Channel.rpc_types = {"scmi": "SCMI_RPC", "none": "NONE_RPC"}
    
    channel = Channel()
    channel._type = "invalid_type"
    
    with patch('smct.owners.owner_agent.logger') as mock_logger:
        result = channel.get_rpc_type()
        assert result == "NONE_RPC"
        mock_logger.error.assert_called_once()