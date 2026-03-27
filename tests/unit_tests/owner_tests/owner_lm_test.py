#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause

from unittest.mock import Mock, patch

import pytest

from smct.exceptions.cfg_tool_exception import CfgToolException
from smct.owners.owner_agent import Channel, ScmiAgent
from smct.owners.owner_base import AssignedResource
from smct.owners.owner_lm import LM
from smct.resources.res_api import ApiResource
from smct.resources.resource_base import MacroResource


def test_lm_init_valid_parameters() -> None:
    """Test LM initialization with valid parameters"""
    LM.safety_types = {"nseenv": "NSEENV", "seenv": "SEENV"}
    LM.auto_boot_types = {"none": "NONE", "auto": "AUTO"}
    Channel.rpc_types = {"none": "NONE", "scmi": "SCMI"}

    lm = LM("lm1", 1, "TestLM", "scmi", 100, "nseenv", 2, "auto", True)

    assert lm.get_id() == "lm1"
    assert lm.get_did() == 1
    assert lm.get_name() == "TestLM"
    assert lm.get_rpc() == "scmi"
    assert lm.get_rtime() == 100
    assert lm.get_safe() == "nseenv"
    assert lm.get_group() == 2
    assert lm.get_auto() == "auto"
    assert lm.get_default()


def test_lm_init_invalid_rpc_type() -> None:
    """Test LM initialization with invalid RPC type"""
    LM.safety_types = {"nseenv": "NSEENV"}
    LM.auto_boot_types = {"none": "NONE"}
    Channel.rpc_types = {"none": "NONE", "scmi": "SCMI"}

    with patch("smct.owners.owner_lm.logger") as mock_logger:
        lm = LM("lm1", 1, "TestLM", "invalid_rpc", None, None, None, None, False)
        assert lm.get_rpc() == "none"
        mock_logger.error.assert_called_once()


def test_lm_init_invalid_safety_type() -> None:
    """Test LM initialization with invalid safety type"""
    LM.safety_types = {"nseenv": "NSEENV"}
    LM.auto_boot_types = {"none": "NONE"}
    Channel.rpc_types = {"none": "NONE"}

    with patch("smct.owners.owner_lm.logger") as mock_logger:
        lm = LM("lm1", 1, "TestLM", None, None, "invalid_safe", None, None, False)
        assert lm.get_safe() == "nseenv"
        mock_logger.error.assert_called_once()


def test_lm_init_invalid_auto_boot_type() -> None:
    """Test LM initialization with invalid auto boot type"""
    LM.safety_types = {"nseenv": "NSEENV"}
    LM.auto_boot_types = {"none": "NONE"}
    Channel.rpc_types = {"none": "NONE"}

    with patch("smct.owners.owner_lm.logger") as mock_logger:
        lm = LM("lm1", 1, "TestLM", None, None, None, None, "invalid_auto", False)
        assert lm.get_auto() is None
        mock_logger.error.assert_called_once()


def test_lm_add_agent() -> None:
    """Test adding SCMI agent to LM"""
    LM.safety_types = {"nseenv": "NSEENV"}
    LM.auto_boot_types = {"none": "NONE"}
    Channel.rpc_types = {"scmi": "SCMI"}

    lm = LM("lm1", 1, "TestLM", "scmi", None, None, None, None, False)
    agent = Mock(spec=ScmiAgent)
    agent.get_owner.return_value = None
    agent.get_name.return_value = "agent1"

    lm.add_agent(agent)

    assert len(lm.get_all_agents()) == 1
    assert lm.get_all_agents()[0] == agent


def test_lm_add_agent_reassignment_error() -> None:
    """Test error when reassigning agent to different LM"""
    LM.safety_types = {"nseenv": "NSEENV"}
    LM.auto_boot_types = {"none": "NONE"}
    Channel.rpc_types = {"scmi": "SCMI"}

    lm1 = LM("lm1", 1, "TestLM1", "scmi", None, None, None, None, False)
    lm2 = LM("lm2", 2, "TestLM2", "scmi", None, None, None, None, False)

    agent = Mock(spec=ScmiAgent)
    agent.get_owner.return_value = lm1
    agent.get_name.return_value = "agent1"

    with pytest.raises(CfgToolException):
        lm2.add_agent(agent)


def test_lm_get_msel_existing() -> None:
    """Test getting existing MSEL"""
    LM.safety_types = {"nseenv": "NSEENV"}
    LM.auto_boot_types = {"none": "NONE"}
    Channel.rpc_types = {"none": "NONE"}

    lm = LM("lm1", 1, "TestLM", None, None, None, None, None, False)
    msel1 = lm.get_msel(1, 1, False)
    msel2 = lm.get_msel(1, 1, False)

    assert msel1 == msel2
    assert len(lm.get_all_msels()) == 1


def test_lm_get_msel_redefinition_error() -> None:
    """Test error when redefining MSEL boot parameter"""
    LM.safety_types = {"nseenv": "NSEENV"}
    LM.auto_boot_types = {"none": "NONE"}
    Channel.rpc_types = {"none": "NONE"}

    lm = LM("lm1", 1, "TestLM", None, None, None, None, None, False)

    with patch("smct.owners.owner_lm.logger") as mock_logger:
        lm.get_msel(1, 1, False)
        lm.get_msel(1, 2, False)  # Different boot value
        mock_logger.error.assert_called()


def test_lm_handle_start_stops_macro_resource() -> None:
    """Test handling start/stops for macro resource (should be ignored)"""
    LM.safety_types = {"nseenv": "NSEENV"}
    LM.auto_boot_types = {"none": "NONE"}
    Channel.rpc_types = {"none": "NONE"}

    lm = LM("lm1", 1, "TestLM", None, None, None, None, None, False)
    resource = Mock(spec=MacroResource)
    params = ["start=1|10"]

    lm.handle_start_stops(resource, params)

    assert len(lm.get_all_msels()) == 0


def test_lm_get_max_msel_num() -> None:
    """Test getting maximum MSEL number"""
    LM.safety_types = {"nseenv": "NSEENV"}
    LM.auto_boot_types = {"none": "NONE"}
    Channel.rpc_types = {"none": "NONE"}

    lm = LM("lm1", 1, "TestLM", None, None, None, None, None, False)
    lm.get_msel(1)
    lm.get_msel(5)
    lm.get_msel(3)

    assert lm.get_max_msel_num() == 5


def test_lm_get_all_faults() -> None:
    """Test getting all faults from LM and agents"""
    LM.safety_types = {"nseenv": "NSEENV"}
    LM.auto_boot_types = {"none": "NONE"}
    Channel.rpc_types = {"scmi": "SCMI"}

    lm = LM("lm1", 1, "TestLM", "scmi", None, None, None, None, False)

    # Mock LM resource with faults
    lm_resource = Mock(spec=AssignedResource)
    lm_resource.get_fault_resources.return_value = ["fault1"]
    lm._resources = [lm_resource]

    # Mock agent with resource with faults
    agent_resource = Mock(spec=AssignedResource)
    agent_resource.get_fault_resources.return_value = ["fault2"]
    agent = Mock(spec=ScmiAgent)
    agent.get_owned_resources.return_value = [agent_resource]
    agent.get_owner.return_value = None
    agent.get_name.return_value = "agent1"
    lm.add_agent(agent)

    faults = lm.get_all_faults()

    assert len(faults) == 2
    assert lm_resource in faults
    assert agent_resource in faults


def test_lm_get_all_cpus() -> None:
    """Test getting all CPU resources"""
    LM.safety_types = {"nseenv": "NSEENV"}
    LM.auto_boot_types = {"none": "NONE"}
    Channel.rpc_types = {"none": "NONE"}

    lm = LM("lm1", 1, "TestLM", None, None, None, None, None, False)

    # Mock CPU resource
    cpu_resource = Mock(spec=ApiResource)
    cpu_resource.is_cpu.return_value = True

    # Mock non-CPU resource
    non_cpu_resource = Mock(spec=ApiResource)
    non_cpu_resource.is_cpu.return_value = False

    assigned_resource = Mock(spec=AssignedResource)
    assigned_resource.get_atomic_resources.return_value = [cpu_resource, non_cpu_resource]
    lm._resources = [assigned_resource]

    cpus = lm.get_all_cpus()

    assert len(cpus) == 1
    assert cpu_resource in cpus


def test_lm_is_scmi() -> None:
    """Test SCMI protocol detection"""
    LM.safety_types = {"nseenv": "NSEENV"}
    LM.auto_boot_types = {"none": "NONE"}
    Channel.rpc_types = {"none": "NONE", "scmi": "SCMI"}

    lm_scmi = LM("lm1", 1, "TestLM", "scmi", None, None, None, None, False)
    lm_none = LM("lm2", 2, "TestLM2", "none", None, None, None, None, False)

    assert lm_scmi.is_scmi()
    assert not lm_none.is_scmi()


def test_lm_get_assignment_json_scmi() -> None:
    """Test getting assignment JSON for SCMI LM"""
    LM.safety_types = {"nseenv": "NSEENV"}
    LM.auto_boot_types = {"auto": "AUTO"}
    Channel.rpc_types = {"scmi": "SCMI"}

    lm = LM("lm1", 1, "TestLM", "scmi", 100, "nseenv", 2, "auto", True)

    agent = Mock(spec=ScmiAgent)
    agent.get_assignment_json.return_value = {"agent": "data"}
    agent.get_owner.return_value = None
    agent.get_name.return_value = "agent1"
    lm.add_agent(agent)

    json_data = lm.get_assignment_json()

    assert json_data["type"] == "LM"
    assert json_data["rpc"] == "scmi"
    assert json_data["rtime"] == 100
    assert json_data["group"] == 2
    assert json_data["auto"] == "auto"
    assert json_data["default"]
    assert json_data["safe"] == "nseenv"
    assert "agents" in json_data
    assert json_data["resources"] == []


def test_lm_get_assignment_json_non_scmi() -> None:
    """Test getting assignment JSON for non-SCMI LM"""
    LM.safety_types = {"nseenv": "NSEENV"}
    LM.auto_boot_types = {"none": "NONE"}
    Channel.rpc_types = {"none": "NONE"}

    lm = LM("lm1", 1, "TestLM", "none", None, None, None, None, False)

    json_data = lm.get_assignment_json()

    assert json_data["type"] == "LM"
    assert json_data["rpc"] == "none"
    assert "agents" not in json_data or json_data.get("agents") == []


def test_lm_get_define_methods() -> None:
    """Test various get_*_define methods"""
    LM.safety_types = {"nseenv": "NSEENV_DEFINE"}
    LM.auto_boot_types = {"auto": "AUTO_DEFINE", "none": "NONE_DEFINE"}
    Channel.rpc_types = {"scmi": "SCMI_DEFINE", "none": "NONE_DEFINE"}

    lm = LM("lm1", 1, "TestLM", "scmi", None, "nseenv", None, "auto", False)

    assert lm.get_safe_define() == "NSEENV_DEFINE"
    assert lm.get_rpc_define() == "SCMI_DEFINE"
    assert lm.get_auto_define() == "AUTO_DEFINE"
