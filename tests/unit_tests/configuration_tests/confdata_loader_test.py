#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Unit tests for smct.configuration.confdata_loader JSON configuration loading."""

# pylint: disable=missing-function-docstring

from typing import Any, Dict, Iterator
from unittest.mock import Mock, patch

import pytest

from smct.configuration.confdata_loader import _create_parameters_list, ConfigLoader
from smct.owners.owner_base import AssignedDefine, ResourceOwner
from smct.owners.owner_lm import LM
from smct.resources.resource_base import AtomicResource
from tests import test_utils


@pytest.fixture(autouse=True)
def setup_owner_class_attrs() -> Iterator[None]:
    """Reset global providers and owner class state between tests."""
    with test_utils.restore_owner_class_attrs():
        yield


class TestConfigLoader:
    """Tests for ConfigLoader safe JSON handling helpers."""

    def test_create_parameters_list_converts_dict_to_assignment_strings(self) -> None:
        params: Dict[str, Any] = {"perm": "rw", "secure": True, "did": 3}

        assert _create_parameters_list(params) == ["perm=rw", "secure=True", "did=3"]

    def test_load_configuration_handle_defines_assigns_parsed_defines(self) -> None:
        owner = Mock(spec=ResourceOwner)
        json_defines = [{"name": "LOCAL_DEFINE", "params": {"perm": "rw", "api": "none"}}]

        ConfigLoader.load_configuration_handle_defines(owner, json_defines)

        owner.assign_define.assert_called_once()
        assigned_define = owner.assign_define.call_args.args[0]
        assert isinstance(assigned_define, AssignedDefine)
        assert assigned_define.get_name() == "LOCAL_DEFINE"
        assert assigned_define.get_params() == {"perm": "rw", "api": "none"}

    def test_load_configuration_assign_resources_resolves_defines_and_dirty_flag(self) -> None:
        target = Mock(spec=ResourceOwner)
        target.get_id.return_value = "LM1"
        local_define = AssignedDefine("LOCAL", "local=yes")
        target.get_define.side_effect = lambda name: local_define if name == "LOCAL" else None
        common_define = AssignedDefine("COMMON", "common=1")
        resource = Mock(spec=AtomicResource)
        json_resources = [
            {
                "name": "TEST_RESOURCE",
                "defines": ["LOCAL", "COMMON"],
                "params": {"explicit": "value"},
                "dirty_flag": False,
            }
        ]

        with patch("smct.configuration.confdata_loader._find_resources", return_value=[resource]):
            ConfigLoader.load_configuration_assign_resources(target, json_resources, {"COMMON": common_define})

        target.assign_resource.assert_called_once()
        args = target.assign_resource.call_args.args
        assert args[0] == resource
        assert set(args[1]) == {"local=yes", "common=1", "explicit=value"}
        assert args[2] == [local_define, common_define]
        assert args[3] is False
        assert args[4] is False

    def test_load_configuration_handle_logical_machines_builds_lm_objects(self) -> None:
        json_lms = [
            {
                "name": "TestLM",
                "did": 4,
                "dirty_flag": False,
                "debug": True,
                "ss_sequences": [],
                "msels": [],
                "rpc": "scmi",
                "safe": "safe",
                "rtime": None,
                "auto": None,
                "group": 1,
                "default": False,
                "defines": [{"name": "LM_DEFINE", "params": {"boot": "yes"}}],
            }
        ]

        lms = ConfigLoader.load_configuration_handle_logical_machines(json_lms, {})

        assert len(lms) == 1
        assert lms[0].get_id() == "LM0"
        assert lms[0].get_name() == "TestLM"
        assert lms[0].get_did() == 4
        assert lms[0].is_dirty() is False
        lm_define = lms[0].get_define("LM_DEFINE")
        assert lm_define is not None
        assert lm_define.get_params() == {"boot": "yes"}

    def test_load_config_handle_domains_builds_domains_and_delegates_resources(self) -> None:
        common_defines = {"COMMON": AssignedDefine("COMMON", "common=1")}
        resources = [{"name": "TEST_RESOURCE", "defines": [], "params": {}}]
        json_domains = [
            {
                "did": 7,
                "name": "TestDomain",
                "debug": False,
                "resources": resources,
                "dirty_flag": False,
                "defines": [{"name": "DOMAIN_DEFINE", "params": {"dom": "yes"}}],
            }
        ]

        with patch.object(ConfigLoader, "load_configuration_assign_resources") as assign_resources:
            domains = ConfigLoader.load_config_handle_domains(json_domains, common_defines)

        assert len(domains) == 1
        assert domains[0].get_id() == "DOM7"
        assert domains[0].get_name() == "TestDomain"
        assert domains[0].get_did() == 7
        assert domains[0].is_dirty() is False
        domain_define = domains[0].get_define("DOMAIN_DEFINE")
        assert domain_define is not None
        assert domain_define.get_params() == {"dom": "yes"}
        assign_resources.assert_called_once_with(domains[0], resources, common_defines)

    def test_load_configuration_assign_resources_unknown_define_logs_error(self, caplog: pytest.LogCaptureFixture) -> None:
        """Unknown define name logs an error and the resource is still assigned."""
        target = Mock(spec=ResourceOwner)
        target.get_id.return_value = "LM1"
        target.get_name.return_value = "LM1"
        target.get_define.return_value = None  # define is not found locally
        resource = Mock(spec=AtomicResource)
        json_resources = [
            {
                "name": "TEST_RESOURCE",
                "defines": ["NONEXISTENT_DEFINE"],
                "params": {},
                "dirty_flag": True,
            }
        ]

        with caplog.at_level("ERROR"):
            with patch("smct.configuration.confdata_loader._find_resources", return_value=[resource]):
                ConfigLoader.load_configuration_assign_resources(target, json_resources, {})

        assert "Unknown define 'NONEXISTENT_DEFINE'" in caplog.text

    def test_load_configuration_handle_agents_adds_agent_with_mu_mailbox(self) -> None:
        """load_configuration_handle_agents creates an agent with a MailboxMu under the LM."""
        lm = LM("LM0", 1, "TestLM", "scmi", None, "nseenv", None, None, False)
        agents_json = [
            {
                "name": "Agent0",
                "secure": False,
                "dirty_flag": True,
                "mailbox": {"type": "mu", "mu": 0, "test": None, "priority": None},
                "channels": [],
                "resources": [],
            }
        ]

        ConfigLoader.load_configuration_handle_agents(lm, agents_json, 0, {})

        agents = lm.get_all_agents()
        assert len(agents) == 1
        assert agents[0].get_name() == "Agent0"
        assert agents[0].get_mailbox() is not None

    def test_load_configuration_handle_agents_no_resources_logs_error(self, caplog: pytest.LogCaptureFixture) -> None:
        """An agent JSON entry with neither 'dup' nor 'resources' key logs an error."""
        lm = LM("LM0", 1, "TestLM", "scmi", None, "nseenv", None, None, False)
        agents_json = [
            {
                "name": "AgentNoRes",
                "secure": False,
                "dirty_flag": True,
                "mailbox": {"type": "mu", "mu": 0, "test": None, "priority": None},
                "channels": [],
                # neither 'dup' nor 'resources' key present
            }
        ]

        with caplog.at_level("ERROR"):
            ConfigLoader.load_configuration_handle_agents(lm, agents_json, 0, {})

        assert "Agent AgentNoRes has neither 'dup' nor 'resources' defined" in caplog.text

    def test_load_configuration_handle_start_stops_preserves_order_fields(self) -> None:
        """Round-trip start/stop JSON keeps sparse sequence positions."""
        test_utils.set_up()
        source_lm = LM("LM0", 1, "SourceLM", "none", None, "nseenv", None, None, False)
        source_msel = source_lm.get_msel(0)

        start_a = Mock()
        start_a.get_name.return_value = "START_A"
        start_b = Mock()
        start_b.get_name.return_value = "START_B"
        stop_a = Mock()
        stop_a.get_name.return_value = "STOP_A"
        stop_b = Mock()
        stop_b.get_name.return_value = "STOP_B"

        source_msel.add_start_stop(True, False, start_a, "5")
        source_msel.add_start_stop(True, False, start_b, "6")
        source_msel.add_start_stop(False, False, stop_a, "5")
        source_msel.add_start_stop(False, False, stop_b, "6")

        source_json = source_lm.get_assignment_json()
        json_msel = source_json["msels"][0]
        ss_sequences = source_json["ss_sequences"]
        target_lm = LM("LM1", 2, "TargetLM", "none", None, "nseenv", None, None, False)
        target_msel = target_lm.get_msel(0)

        def _find_resources(resource_name: str) -> list[Mock]:
            return [start_a] if resource_name == "START_A" else [start_b] if resource_name == "START_B" else [stop_a] if resource_name == "STOP_A" else [stop_b]

        with (
            patch("smct.configuration.confdata_loader._find_resources", side_effect=_find_resources),
            patch("smct.configuration.confdata_loader._expand_resource_to_atoms", side_effect=lambda resource: [resource]),
        ):
            ConfigLoader.load_configuration_handle_start_stops(target_msel, json_msel, ss_sequences)

        assert target_msel.get_start_stop_buckets(True)[4] != []
        assert target_msel.get_start_stop_buckets(True)[5] != []
        assert target_msel.get_start_stop_buckets(False)[4] != []
        assert target_msel.get_start_stop_buckets(False)[5] != []

    def test_load_configuration_handle_start_stops_missing_order_logs_error_and_skips(self, caplog: pytest.LogCaptureFixture) -> None:
        """An ss_sequence entry without 'order' logs an error and is not added to the MSEL."""
        test_utils.set_up()
        lm = LM("LM0", 1, "TestLM", "none", None, "nseenv", None, None, False)
        msel = lm.get_msel(0)

        # Build a minimal JSON structure: one start entry lacks 'order', one stop entry lacks 'order'
        json_msel: Dict[str, Any] = {"msel": 0, "boot": None, "skip": None, "start": 1, "stop": 2}
        ss_sequences = [
            {"ss": 1, "ss_name": "start_seq", "resources": [{"rsrc": "MISSING_ORDER_START"}]},
            {"ss": 2, "ss_name": "stop_seq", "resources": [{"rsrc": "MISSING_ORDER_STOP"}]},
        ]

        dummy_atom = Mock()
        dummy_atom.get_name.return_value = "DUMMY"

        with caplog.at_level("ERROR"):
            with (
                patch("smct.configuration.confdata_loader._find_resources", return_value=[dummy_atom]),
                patch("smct.configuration.confdata_loader._expand_resource_to_atoms", return_value=[dummy_atom]),
            ):
                ConfigLoader.load_configuration_handle_start_stops(msel, json_msel, ss_sequences)

        # Both entries should have been skipped — no start/stop added
        assert msel.get_all_start_stops(True) == []
        assert msel.get_all_start_stops(False) == []

        # Errors must be logged for both missing 'order' fields
        assert "MISSING_ORDER_START" in caplog.text
        assert "MISSING_ORDER_STOP" in caplog.text
        assert "missing required 'order' field" in caplog.text
