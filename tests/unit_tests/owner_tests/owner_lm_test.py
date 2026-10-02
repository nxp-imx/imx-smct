#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
# pylint: disable=protected-access, missing-module-docstring

from typing import Iterator
from unittest.mock import Mock, patch

import pytest

from smct.exceptions.cfg_tool_exception import CfgToolException
from smct.owners.owner_agent import Channel, ScmiAgent
from smct.owners.owner_base import AssignedResource
from smct.owners.owner_lm import LM, StartStop
from smct.resources.res_api import ApiResource
from smct.resources.resource_base import AtomicResource, MacroResource
from tests import test_utils


@pytest.fixture(autouse=True)
def setup_owner_class_attrs() -> Iterator[None]:
    """Restore LM/Channel class-level type-mapping attributes after each test."""
    with test_utils.restore_owner_class_attrs():
        yield


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


def test_msel_add_start_stop_duplicate_start_keeps_both_entries() -> None:
    """Duplicate start order number keeps both entries (Perl-parity); no logger.error called."""
    LM.safety_types = {"nseenv": "NSEENV"}
    LM.auto_boot_types = {"none": "NONE"}
    Channel.rpc_types = {"none": "NONE"}

    lm = LM("lm1", 1, "TestLM", "none", None, "nseenv", None, None, False)
    msel = lm.get_msel(0)
    res_a = Mock(spec=AtomicResource)
    res_b = Mock(spec=AtomicResource)

    with patch("smct.owners.owner_lm.logger") as mock_logger:
        msel.add_start_stop(True, False, res_a, "2")
        msel.add_start_stop(True, False, res_b, "2")
        mock_logger.error.assert_not_called()

    starts = msel.get_all_start_stops(True)
    assert len(starts) == 2
    assert starts[0].get_resources() is res_a
    assert starts[1].get_resources() is res_b


def test_msel_add_start_stop_duplicate_stop_keeps_both_entries() -> None:
    """Duplicate stop order number keeps both entries (Perl-parity); no logger.error called."""
    LM.safety_types = {"nseenv": "NSEENV"}
    LM.auto_boot_types = {"none": "NONE"}
    Channel.rpc_types = {"none": "NONE"}

    lm = LM("lm1", 1, "TestLM", "none", None, "nseenv", None, None, False)
    msel = lm.get_msel(0)
    res_a = Mock(spec=AtomicResource)
    res_b = Mock(spec=AtomicResource)

    with patch("smct.owners.owner_lm.logger") as mock_logger:
        msel.add_start_stop(False, False, res_a, "3")
        msel.add_start_stop(False, False, res_b, "3")
        mock_logger.error.assert_not_called()

    stops = msel.get_all_start_stops(False)
    assert len(stops) == 2
    assert stops[0].get_resources() is res_a
    assert stops[1].get_resources() is res_b


def test_msel_get_start_stop_buckets_shape() -> None:
    """Buckets for orders 1,2,2,5 have the right structure: gap at 3,4 and duplicate at 2."""
    LM.safety_types = {"nseenv": "NSEENV"}
    LM.auto_boot_types = {"none": "NONE"}
    Channel.rpc_types = {"none": "NONE"}

    lm = LM("lm1", 1, "TestLM", "none", None, "nseenv", None, None, False)
    msel = lm.get_msel(0)
    res_1 = Mock(spec=AtomicResource)
    res_2a = Mock(spec=AtomicResource)
    res_2b = Mock(spec=AtomicResource)
    res_5 = Mock(spec=AtomicResource)

    msel.add_start_stop(True, False, res_1, "1")
    msel.add_start_stop(True, False, res_2a, "2")
    msel.add_start_stop(True, False, res_2b, "2")
    msel.add_start_stop(True, False, res_5, "5")

    buckets = msel.get_start_stop_buckets(True)
    assert len(buckets) == 5
    assert len(buckets[0]) == 1 and buckets[0][0].get_resources() is res_1
    assert len(buckets[1]) == 2
    assert buckets[1][0].get_resources() is res_2a
    assert buckets[1][1].get_resources() is res_2b
    assert len(buckets[2]) == 0  # gap at order 3
    assert len(buckets[3]) == 0  # gap at order 4
    assert len(buckets[4]) == 1 and buckets[4][0].get_resources() is res_5


def test_msel_add_start_stop_out_of_range_still_raises() -> None:
    """Orders 0 and 101 continue to raise CfgToolException."""
    LM.safety_types = {"nseenv": "NSEENV"}
    LM.auto_boot_types = {"none": "NONE"}
    Channel.rpc_types = {"none": "NONE"}

    lm = LM("lm1", 1, "TestLM", "none", None, "nseenv", None, None, False)
    msel = lm.get_msel(0)
    res = Mock(spec=AtomicResource)

    with pytest.raises(CfgToolException):
        msel.add_start_stop(True, False, res, "0")
    with pytest.raises(CfgToolException):
        msel.add_start_stop(True, False, res, "101")


def test_msel_get_flat_index_raises_when_ss_not_present() -> None:
    """get_flat_index raises ValueError when the requested StartStop instance is not stored."""
    LM.safety_types = {"nseenv": "NSEENV"}
    LM.auto_boot_types = {"none": "NONE"}
    Channel.rpc_types = {"none": "NONE"}

    lm = LM("lm1", 1, "TestLM", "none", None, "nseenv", None, None, False)
    msel = lm.get_msel(0)
    res = Mock(spec=AtomicResource)
    msel.add_start_stop(True, False, res, "1")

    stored = msel.get_start_stop_buckets(True)[0][0]
    assert msel.get_flat_index(stored, True) == 0

    with pytest.raises(ValueError):
        msel.get_flat_index(stored, False)  # not in stop buckets

    other_res = Mock(spec=AtomicResource)
    foreign_ss = StartStop(msel, other_res, False, [])
    with pytest.raises(ValueError):
        msel.get_flat_index(foreign_ss, True)
