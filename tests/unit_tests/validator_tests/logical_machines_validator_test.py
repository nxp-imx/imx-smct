#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Unit tests for LogicalMachinesValidator class"""
import logging
import pytest
from unittest.mock import Mock, patch
from typing import List, Any

from smct.configuration.confdata import ConfigurationData
from smct.owners.owner_lm import LM
from smct.validation.validators.logical_machines_validator import LogicalMachinesValidator
from smct.validation.validation_entry import ValidationEntry


def setup_test_data() -> tuple[LogicalMachinesValidator, ConfigurationData]:
    """Set up test fixtures"""
    validator = LogicalMachinesValidator()
    config = ConfigurationData()
    return validator, config


def test_validate_empty_configuration() -> None:
    """Test validation with no logical machines"""
    # Arrange
    validator, config = setup_test_data()
    
    # Act
    result = validator.validate(config)
    
    # Assert
    assert len(result) == 0

# ============================================================================
# LM ID VALIDATION ERROR TESTS
# ============================================================================

def test_validate_duplicate_lm_ids_error() -> None:
    """Test validation error when LMs have duplicate IDs"""
    # Arrange
    validator, config = setup_test_data()
    
    lm1 = Mock(spec=LM)
    lm1.get_id.return_value = "LM1"
    lm1.get_did.return_value = 1
    lm1.get_name.return_value = "TestLM1"
    lm1.get_all_msels.return_value = []
    
    lm2 = Mock(spec=LM)
    lm2.get_id.return_value = "LM1"  # Duplicate ID
    lm2.get_did.return_value = 2
    lm2.get_name.return_value = "TestLM2"
    lm2.get_all_msels.return_value = []
    
    config.add_lm(lm1)
    config.add_lm(lm2)
    
    # Act
    result = validator.validate(config)
    
    # Assert
    error_messages = [entry.get_error_message() for entry in result]
    error_entries = [entry for entry in result if entry.get_level() == logging.ERROR]
    assert len(error_entries) > 0
    assert 'Logical machine IDs are not consecutive: [1, 1]' in error_messages


def test_validate_invalid_lm_id_format_error() -> None:
    """Test validation error when LM has invalid ID format"""
    # Arrange
    validator, config = setup_test_data()
    
    lm1 = Mock(spec=LM)
    lm1.get_id.return_value = "INVALID_ID_123!"  # Invalid characters
    lm1.get_did.return_value = 1
    lm1.get_name.return_value = "TestLM1"
    lm1.get_all_msels.return_value = []
    
    lm2 = Mock(spec=LM)
    lm2.get_id.return_value = ""  # Empty ID
    lm2.get_did.return_value = 2
    lm2.get_name.return_value = "TestLM2"
    lm2.get_all_msels.return_value = []
    
    config.add_lm(lm1)
    config.add_lm(lm2)
    
    # Act
    result = validator.validate(config)
    
    # Assert
    error_messages = [entry.get_error_message() for entry in result]
    error_entries = [entry for entry in result if entry.get_level() == logging.ERROR]
    assert len(error_entries) > 0
    assert f"Logical machine ID 'INVALID_ID_123!' does not match required pattern" in error_messages
    assert f"Logical machine ID '' does not match required pattern" in error_messages

def test_validate_lm_ids_not_starting_from_zero_error() -> None:
    """Test validation error when LM IDs don't start from 0"""
    # Arrange
    validator, config = setup_test_data()
    
    lm1 = Mock(spec=LM)
    lm1.get_id.return_value = "LM1"  # Starting from 1 instead of 0
    lm1.get_did.return_value = 1
    lm1.get_name.return_value = "TestLM1"
    lm1.get_all_msels.return_value = []
    
    lm2 = Mock(spec=LM)
    lm2.get_id.return_value = "LM2"
    lm2.get_did.return_value = 2
    lm2.get_name.return_value = "TestLM2"
    lm2.get_all_msels.return_value = []
    
    config.add_lm(lm1)
    config.add_lm(lm2)
    
    # Act
    result = validator.validate(config)
    
    # Assert
    error_messages = [entry.get_error_message() for entry in result]
    error_entries = [entry for entry in result if entry.get_level() == logging.ERROR]
    assert len(error_entries) > 0
    assert 'Logical machine IDs must start from 0, but there is no LM0 in the configuration. Lowest ID is 1' in error_messages

def test_validate_lm_ids_multiple_gaps_error() -> None:
    """Test validation error when LM IDs have multiple gaps"""
    # Arrange
    validator, config = setup_test_data()
    
    lm1 = Mock(spec=LM)
    lm1.get_id.return_value = "LM2"  # Starting from 2
    lm1.get_did.return_value = 1
    lm1.get_name.return_value = "TestLM2"
    lm1.get_all_msels.return_value = []
    
    lm2 = Mock(spec=LM)
    lm2.get_id.return_value = "LM5"  # Gap: missing LM3, LM4
    lm2.get_did.return_value = 2
    lm2.get_name.return_value = "TestLM5"
    lm2.get_all_msels.return_value = []
    
    lm3 = Mock(spec=LM)
    lm3.get_id.return_value = "LM7"  # Gap: missing LM6
    lm3.get_did.return_value = 3
    lm3.get_name.return_value = "TestLM7"
    lm3.get_all_msels.return_value = []
    
    config.add_lm(lm1)
    config.add_lm(lm2)
    config.add_lm(lm3)
    
    # Act
    result = validator.validate(config)
    
    # Assert
    error_messages = [entry.get_error_message() for entry in result]
    error_entries = [entry for entry in result if entry.get_level() == logging.ERROR]
    assert len(error_entries) > 0
    assert 'Logical machine IDs must start from 0, but there is no LM0 in the configuration. Lowest ID is 2' in error_messages
    assert 'Logical machine 7 has higher ID than there is amount of logical machines in total (3)' in error_messages
    assert 'Logical machine IDs are not consecutive: [2, 5, 7]' in error_messages

def test_validate_lm_names_duplicate_error() -> None:
    """Test validation error when LM names are not unique"""
    # Arrange
    validator, config = setup_test_data()
    
    lm1 = Mock(spec=LM)
    lm1.get_id.return_value = "LM1"
    lm1.get_did.return_value = 1
    lm1.get_name.return_value = "DuplicateName"
    lm1.get_all_msels.return_value = []
    
    lm2 = Mock(spec=LM)
    lm2.get_id.return_value = "LM2"
    lm2.get_did.return_value = 2
    lm2.get_name.return_value = "DuplicateName"
    lm2.get_all_msels.return_value = []
    
    config.add_lm(lm1)
    config.add_lm(lm2)
    
    # Act
    result = validator.validate(config)
    
    # Assert
    error_messages = [entry.get_error_message() for entry in result]
    error_entries = [entry for entry in result if entry.get_level() == logging.ERROR]
    assert len(error_entries) > 0
    assert "Logical machines 'LM1, LM2' have duplicate name 'DuplicateName'" in error_messages

def test_validate_lm_default_option_multiple_error() -> None:
    """Test validation error when multiple LMs have default option set"""
    # Arrange
    validator, config = setup_test_data()
    
    lm1 = Mock(spec=LM)
    lm1.get_id.return_value = "LM1"
    lm1.get_did.return_value = 1
    lm1.get_name.return_value = "TestLM1"
    lm1.get_all_msels.return_value = []
    lm1.get_default.return_value = True
    
    lm2 = Mock(spec=LM)
    lm2.get_id.return_value = "LM2"
    lm2.get_did.return_value = 2
    lm2.get_name.return_value = "TestLM2"
    lm2.get_all_msels.return_value = []
    lm2.get_default.return_value = True
    
    config.add_lm(lm1)
    config.add_lm(lm2)
    
    # Act
    result = validator.validate(config)
    
    # Assert
    error_messages = [entry.get_error_message() for entry in result]
    error_entries = [entry for entry in result if entry.get_level() == logging.ERROR]
    assert len(error_entries) > 0
    assert "Option 'default' is set for multiple logical machines but will only be applied for the LM2" in error_messages

def test_validate_lm0_does_not_have_did_0_error() -> None:
    """Test validation error when LM0 does not have did 0"""
    # Arrange
    validator, config = setup_test_data()
    
    LM.sm_did = 0
    lm0 = Mock(spec=LM)
    lm0.get_id.return_value = "LM0"
    lm0.get_did.return_value = 1
    lm0.get_name.return_value = "SM"
    lm0.get_all_msels.return_value = []
    lm0.get_all_start_stops.return_value = []
    lm0.get_safe.return_value = "feenv"
    lm0.get_rpc.return_value = "none"
    lm0.get_boot.return_value = 1
    lm0.get_skip.return_value = False
    
    config.add_lm(lm0)
    
    # Act
    result = validator.validate(config)
    
    # Assert
    error_messages = [entry.get_error_message() for entry in result]
    error_entries = [entry for entry in result if entry.get_level() == logging.ERROR]
    assert len(error_entries) > 0
    assert "LM0 must have TRDC domain '0'" in error_messages


def test_validate_lm0_does_not_have_required_name_error() -> None:
    """Test validation error when LM0 does not have required name 'SM'"""
    # Arrange
    validator, config = setup_test_data()
    
    LM.sm_did = 0
    lm0 = Mock(spec=LM)
    lm0.get_id.return_value = "LM0"
    lm0.get_did.return_value = 0
    lm0.get_name.return_value = "WrongName"
    lm0.get_all_msels.return_value = []
    lm0.get_all_start_stops.return_value = []
    lm0.get_safe.return_value = "feenv"
    lm0.get_rpc.return_value = "none"
    lm0.get_boot.return_value = 1
    lm0.get_skip.return_value = False
    
    config.add_lm(lm0)
    
    # Act
    result = validator.validate(config)
    
    # Assert
    error_messages = [entry.get_error_message() for entry in result]
    error_entries = [entry for entry in result if entry.get_level() == logging.ERROR]
    assert len(error_entries) > 0
    assert "LM0 does not have required name 'SM'" in error_messages


def test_validate_lm0_does_not_have_required_safe_type_error() -> None:
    """Test validation error when LM0 does not have required safety type 'feenv'"""
    # Arrange
    validator, config = setup_test_data()
    
    LM.sm_did = 0
    lm0 = Mock(spec=LM)
    lm0.get_id.return_value = "LM0"
    lm0.get_did.return_value = 0
    lm0.get_name.return_value = "SM"
    lm0.get_all_msels.return_value = []
    lm0.get_all_start_stops.return_value = []
    lm0.get_safe.return_value = "wrong_safe"
    lm0.get_rpc.return_value = "none"
    lm0.get_boot.return_value = 1
    lm0.get_skip.return_value = False
    
    config.add_lm(lm0)
    
    # Act
    result = validator.validate(config)
    
    # Assert
    error_messages = [entry.get_error_message() for entry in result]
    error_entries = [entry for entry in result if entry.get_level() == logging.ERROR]
    assert len(error_entries) > 0
    assert "LM0 does not have required safety type 'feenv'" in error_messages


def test_validate_lm0_does_not_have_required_boot_order_error() -> None:
    """Test validation error when LM0 does not have required boot order '1'"""
    # Arrange
    validator, config = setup_test_data()
    
    LM.sm_did = 0
    lm0 = Mock(spec=LM)
    lm0.get_id.return_value = "LM0"
    lm0.get_did.return_value = 0
    lm0.get_name.return_value = "SM"
    lm0.get_all_msels.return_value = []
    lm0.get_all_start_stops.return_value = []
    lm0.get_safe.return_value = "feenv"
    lm0.get_rpc.return_value = "none"
    lm0.get_boot.return_value = 2
    lm0.get_skip.return_value = False
    
    config.add_lm(lm0)
    
    # Act
    result = validator.validate(config)
    
    # Assert
    error_messages = [entry.get_error_message() for entry in result]
    error_entries = [entry for entry in result if entry.get_level() == logging.ERROR]
    assert len(error_entries) > 0
    assert "LM0 does not have required boot order '1'" in error_messages


def test_validate_lm0_has_unsupported_skip_parameter_error() -> None:
    """Test validation error when LM0 has unsupported skip parameter"""
    # Arrange
    validator, config = setup_test_data()
    
    LM.sm_did = 0
    lm0 = Mock(spec=LM)
    lm0.get_id.return_value = "LM0"
    lm0.get_did.return_value = 0
    lm0.get_name.return_value = "SM"
    lm0.get_all_msels.return_value = []
    lm0.get_all_start_stops.return_value = []
    lm0.get_safe.return_value = "feenv"
    lm0.get_rpc.return_value = "none"
    lm0.get_boot.return_value = 1
    lm0.get_skip.return_value = True
    
    config.add_lm(lm0)
    
    # Act
    result = validator.validate(config)
    
    # Assert
    error_messages = [entry.get_error_message() for entry in result]
    error_entries = [entry for entry in result if entry.get_level() == logging.ERROR]
    assert len(error_entries) > 0
    assert "LM0 does have unsupported parameter skip 'true'. Allowed value is 'false' or not specifying it" in error_messages


def test_validate_lm0_does_not_have_required_rpc_type_error() -> None:
    """Test validation error when LM0 does not have required RPC type 'none'"""
    # Arrange
    validator, config = setup_test_data()
    
    LM.sm_did = 0
    lm0 = Mock(spec=LM)
    lm0.get_id.return_value = "LM0"
    lm0.get_did.return_value = 0
    lm0.get_name.return_value = "SM"
    lm0.get_all_msels.return_value = []
    lm0.get_all_start_stops.return_value = []
    lm0.get_safe.return_value = "feenv"
    lm0.get_rpc.return_value = "wrong_rpc"
    lm0.get_boot.return_value = 1
    lm0.get_skip.return_value = False
    
    config.add_lm(lm0)
    
    # Act
    result = validator.validate(config)
    
    # Assert
    error_messages = [entry.get_error_message() for entry in result]
    error_entries = [entry for entry in result if entry.get_level() == logging.ERROR]
    assert len(error_entries) > 0
    assert "LM0 does not have required RPC type 'none'" in error_messages


def test_validate_lm0_has_no_configuration_warning() -> None:
    """Test validation warning when LM0 has no configuration"""
    # Arrange
    validator, config = setup_test_data()
    
    LM.sm_did = 0
    lm0 = Mock(spec=LM)
    lm0.get_id.return_value = "LM0"
    lm0.get_did.return_value = 0
    lm0.get_name.return_value = "SM"
    lm0.get_all_msels.return_value = []
    lm0.get_all_start_stops.return_value = []
    lm0.get_safe.return_value = "feenv"
    lm0.get_rpc.return_value = "none"
    lm0.get_boot.return_value = 1
    lm0.get_skip.return_value = False
    lm0.get_assigned_resources.return_value = []
    lm0.get_all_agents.return_value = []
    
    config.add_lm(lm0)
    
    # Act
    result = validator.validate(config)
    
    # Assert
    warning_messages = [entry.get_error_message() for entry in result]
    warning_entries = [entry for entry in result if entry.get_level() == logging.WARNING]
    assert len(warning_entries) > 0
    assert "LM0 has no configuration" in warning_messages


def test_validate_lm0_valid_configuration() -> None:
    """Test validation passes when LM0 has valid configuration"""
    # Arrange
    validator, config = setup_test_data()
    
    LM.sm_did = 0
    lm0 = Mock(spec=LM)
    lm0.get_id.return_value = "LM0"
    lm0.get_did.return_value = 0
    lm0.get_name.return_value = "SM"
    lm0.get_all_msels.return_value = []
    lm0.get_all_start_stops.return_value = []
    lm0.get_safe.return_value = "feenv"
    lm0.get_rpc.return_value = "none"
    lm0.get_boot.return_value = 1
    lm0.get_skip.return_value = False
    lm0.get_assigned_resources.return_value = ["resource1"]
    lm0.get_all_agents.return_value = []
    
    config.add_lm(lm0)
    
    # Act
    result = validator.validate(config)
    
    # Assert
    lm0_specific_errors = [entry for entry in result if "LM0" in entry.get_error_message()]
    assert len(lm0_specific_errors) == 0

def test_validate_lm_msels_redefinition_error() -> None:
    """Test validation fails when LM has redefined start/stop resources in msels"""
    # Arrange
    validator, config = setup_test_data()
    
    # Mock resource
    resource = Mock()
    resource.get_name.return_value = "resource1"
    
    # Mock start/stop entries with same resource
    start_stop1 = Mock()
    start_stop1.get_resources.return_value = resource
    
    start_stop2 = Mock()
    start_stop2.get_resources.return_value = resource
    
    # Mock msel
    msel = Mock()
    msel.get_msel.return_value = 0
    msel.get_all_start_stops.side_effect = lambda start: [start_stop1, start_stop2] if start else []
    
    # Mock LM
    lm = Mock(spec=LM)
    lm.get_id.return_value = "LM1"
    lm.get_did.return_value = 1
    lm.get_name.return_value = "TestLM"
    lm.get_all_msels.return_value = [msel]
    
    config.add_lm(lm)
    
    # Act
    result = validator.validate(config)
    
    # Assert
    error_messages = [entry.get_error_message() for entry in result]
    error_entries = [entry for entry in result if entry.get_level() == logging.ERROR]
    assert len(error_entries) > 0
    assert any("Redefinition of Start/Stop order for resource 'resource1'" in msg for msg in error_messages)