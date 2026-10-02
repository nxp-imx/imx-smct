#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause

"""Unit tests for LogicalMachinesValidator class"""

import logging
from unittest.mock import Mock

from smct.owners.owner_lm import LM
from smct.validation.validators.logical_machines_validator import LogicalMachinesValidator
from tests import test_utils


def test_validate_empty_configuration() -> None:
    """Test validation with no logical machines"""
    # Arrange
    validator, config = test_utils.make_validator_and_config(LogicalMachinesValidator)

    # Act
    result = validator.validate(config)

    # Assert
    assert not result


# ============================================================================
# LM ID VALIDATION ERROR TESTS
# ============================================================================


def test_validate_duplicate_lm_ids_error() -> None:
    """Test validation error when LMs have duplicate IDs"""
    # Arrange
    validator, config = test_utils.make_validator_and_config(LogicalMachinesValidator)

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
    assert "Logical machine IDs are not consecutive: [1, 1]" in error_messages


def test_validate_invalid_lm_id_format_error() -> None:
    """Test validation error when LM has invalid ID format"""
    # Arrange
    validator, config = test_utils.make_validator_and_config(LogicalMachinesValidator)

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
    assert "Logical machine ID 'INVALID_ID_123!' does not match required pattern" in error_messages
    assert "Logical machine ID '' does not match required pattern" in error_messages


def test_validate_lm_ids_not_starting_from_zero_error() -> None:
    """Test validation error when LM IDs don't start from 0"""
    # Arrange
    validator, config = test_utils.make_validator_and_config(LogicalMachinesValidator)

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
    assert "Logical machine IDs must start from 0, but there is no LM0 in the configuration. Lowest ID is 1" in error_messages


def test_validate_lm_ids_multiple_gaps_error() -> None:
    """Test validation error when LM IDs have multiple gaps"""
    # Arrange
    validator, config = test_utils.make_validator_and_config(LogicalMachinesValidator)

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
    assert "Logical machine IDs must start from 0, but there is no LM0 in the configuration. Lowest ID is 2" in error_messages
    assert "Logical machine 7 has higher ID than there is amount of logical machines in total (3)" in error_messages
    assert "Logical machine IDs are not consecutive: [2, 5, 7]" in error_messages


def test_validate_lm_names_duplicate_error() -> None:
    """Test validation error when LM names are not unique"""
    # Arrange
    validator, config = test_utils.make_validator_and_config(LogicalMachinesValidator)

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
    validator, config = test_utils.make_validator_and_config(LogicalMachinesValidator)

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
    validator, config = test_utils.make_validator_and_config(LogicalMachinesValidator)

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
    validator, config = test_utils.make_validator_and_config(LogicalMachinesValidator)

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


def test_validate_lm0_does_not_have_required_safe_type_warning() -> None:
    """Test validation warning when LM0 does not have required safety type 'feenv'"""
    # Arrange
    validator, config = test_utils.make_validator_and_config(LogicalMachinesValidator)

    LM.sm_did = 0
    lm0 = Mock(spec=LM)
    lm0.get_id.return_value = "LM0"
    lm0.get_did.return_value = 0
    lm0.get_name.return_value = "SM"
    lm0.get_all_msels.return_value = []
    lm0.get_all_start_stops.return_value = []
    lm0.get_safe.return_value = "nseenv"
    lm0.get_rpc.return_value = "none"
    lm0.get_boot.return_value = 1
    lm0.get_skip.return_value = False

    config.add_lm(lm0)

    # Act
    result = validator.validate(config)

    # Assert
    warning_messages = [entry.get_error_message() for entry in result]
    safe_warnings = [entry for entry in result if entry.get_level() == logging.WARNING and "SAFE" in entry.get_validation_id()]
    safe_errors = [entry for entry in result if entry.get_level() == logging.ERROR and "SAFE" in entry.get_validation_id()]
    assert len(safe_warnings) > 0
    assert len(safe_errors) == 0
    assert "LM0 does not have required safety type 'feenv'" in warning_messages


def test_validate_lm0_does_not_have_required_boot_order_error() -> None:
    """Test validation error when LM0 does not have required boot order '1'"""
    # Arrange
    validator, config = test_utils.make_validator_and_config(LogicalMachinesValidator)

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
    validator, config = test_utils.make_validator_and_config(LogicalMachinesValidator)

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
    validator, config = test_utils.make_validator_and_config(LogicalMachinesValidator)

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
    validator, config = test_utils.make_validator_and_config(LogicalMachinesValidator)

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
    validator, config = test_utils.make_validator_and_config(LogicalMachinesValidator)

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
    """Test validation fails when the same resource appears at multiple start orders in one MSEL."""
    # Arrange
    validator, config = test_utils.make_validator_and_config(LogicalMachinesValidator)

    resource = Mock()
    resource.get_name.return_value = "resource1"

    start_stop1 = Mock()
    start_stop1.get_resources.return_value = resource

    start_stop2 = Mock()
    start_stop2.get_resources.return_value = resource

    msel = Mock()
    msel.get_msel.return_value = 0
    # bucket 0 has start_stop1 (order 1), bucket 1 has start_stop2 (order 2) → DUP_RSRC
    msel.get_start_stop_buckets.side_effect = lambda is_start: [[start_stop1], [start_stop2]] if is_start else []

    lm = Mock(spec=LM)
    lm.get_id.return_value = "LM1"
    lm.get_did.return_value = 1
    lm.get_name.return_value = "TestLM"
    lm.get_all_msels.return_value = [msel]

    config.add_lm(lm)

    # Act
    result = validator.validate(config)

    # Assert
    error_entries = [entry for entry in result if entry.get_level() == logging.ERROR]
    assert len(error_entries) > 0
    assert any("DUP_RSRC.resource1" in entry.get_validation_id() for entry in error_entries)
    assert any("resource1" in entry.get_error_message() for entry in error_entries)


def test_validate_lm_msels_duplicate_order_error() -> None:
    """Two different resources at the same start order produce exactly one DUP_ORDER ERROR."""
    # Arrange
    validator, config = test_utils.make_validator_and_config(LogicalMachinesValidator)

    res_a = Mock()
    res_a.get_name.return_value = "PD_M7"
    res_b = Mock()
    res_b.get_name.return_value = "CPU_M7P"

    ss_a = Mock()
    ss_a.get_resources.return_value = res_a
    ss_b = Mock()
    ss_b.get_resources.return_value = res_b

    msel = Mock()
    msel.get_msel.return_value = 0
    # order 2 has both entries (0-indexed: bucket[1] = [ss_a, ss_b])
    msel.get_start_stop_buckets.side_effect = lambda is_start: [[], [ss_a, ss_b]] if is_start else []

    lm = Mock(spec=LM)
    lm.get_id.return_value = "LM1"
    lm.get_did.return_value = 1
    lm.get_name.return_value = "TestLM"
    lm.get_all_msels.return_value = [msel]
    config.add_lm(lm)

    # Act
    result = validator.validate(config)

    # Assert
    dup_order_errors = [e for e in result if e.get_level() == logging.ERROR and "DUP_ORDER" in e.get_validation_id()]
    assert len(dup_order_errors) == 1
    assert "LM1.MSEL0.START.DUP_ORDER.2" == dup_order_errors[0].get_validation_id()
    assert "PD_M7" in dup_order_errors[0].get_error_message()
    assert "CPU_M7P" in dup_order_errors[0].get_error_message()


def test_validate_lm_msels_same_resource_same_bucket_no_dup_rsrc() -> None:
    """The same resource duplicated within one bucket triggers DUP_ORDER only, not DUP_RSRC."""
    # Arrange
    validator, config = test_utils.make_validator_and_config(LogicalMachinesValidator)

    res = Mock()
    res.get_name.return_value = "PD_M7"

    ss_first = Mock()
    ss_first.get_resources.return_value = res
    ss_second = Mock()
    ss_second.get_resources.return_value = res

    msel = Mock()
    msel.get_msel.return_value = 0
    # bucket[1] (order 2) contains the same resource twice → DUP_ORDER only.
    msel.get_start_stop_buckets.side_effect = lambda is_start: [[], [ss_first, ss_second]] if is_start else []

    lm = Mock(spec=LM)
    lm.get_id.return_value = "LM1"
    lm.get_did.return_value = 1
    lm.get_name.return_value = "TestLM"
    lm.get_all_msels.return_value = [msel]
    config.add_lm(lm)

    # Act
    result = validator.validate(config)

    # Assert
    dup_order_errors = [e for e in result if e.get_level() == logging.ERROR and "DUP_ORDER" in e.get_validation_id()]
    dup_rsrc_errors = [e for e in result if e.get_level() == logging.ERROR and "DUP_RSRC" in e.get_validation_id()]
    assert len(dup_order_errors) == 1
    assert len(dup_rsrc_errors) == 0, f"DUP_RSRC must not fire when the resource is in a single bucket, got: {[e.get_error_message() for e in dup_rsrc_errors]}"


def test_validate_lm_msels_duplicate_resource_single_entry() -> None:
    """Same resource at orders 2 and 5 produces exactly one DUP_RSRC ERROR listing both orders."""
    # Arrange
    validator, config = test_utils.make_validator_and_config(LogicalMachinesValidator)

    res = Mock()
    res.get_name.return_value = "PD_M7"

    ss_at_2 = Mock()
    ss_at_2.get_resources.return_value = res
    ss_at_5 = Mock()
    ss_at_5.get_resources.return_value = res

    msel = Mock()
    msel.get_msel.return_value = 1
    # bucket[1] (order 2) and bucket[4] (order 5) each have one entry for the same resource
    msel.get_start_stop_buckets.side_effect = lambda is_start: [[], [ss_at_2], [], [], [ss_at_5]] if is_start else []

    lm = Mock(spec=LM)
    lm.get_id.return_value = "LM2"
    lm.get_did.return_value = 1
    lm.get_name.return_value = "TestLM"
    lm.get_all_msels.return_value = [msel]
    config.add_lm(lm)

    # Act
    result = validator.validate(config)

    # Assert
    dup_rsrc_errors = [e for e in result if e.get_level() == logging.ERROR and "DUP_RSRC" in e.get_validation_id()]
    assert len(dup_rsrc_errors) == 1
    assert "LM2.MSEL1.START.DUP_RSRC.PD_M7" == dup_rsrc_errors[0].get_validation_id()
    assert "2" in dup_rsrc_errors[0].get_error_message()
    assert "5" in dup_rsrc_errors[0].get_error_message()


def test_validate_lm_msels_duplicate_resource_three_orders() -> None:
    """Same resource at orders 2, 5, 8 still produces exactly one DUP_RSRC ERROR."""
    # Arrange
    validator, config = test_utils.make_validator_and_config(LogicalMachinesValidator)

    res = Mock()
    res.get_name.return_value = "PERF_M7"

    ss_2 = Mock()
    ss_2.get_resources.return_value = res
    ss_5 = Mock()
    ss_5.get_resources.return_value = res
    ss_8 = Mock()
    ss_8.get_resources.return_value = res

    buckets: list = [[], [ss_2], [], [], [ss_5], [], [], [ss_8]]

    msel = Mock()
    msel.get_msel.return_value = 0
    msel.get_start_stop_buckets.side_effect = lambda is_start: buckets if is_start else []

    lm = Mock(spec=LM)
    lm.get_id.return_value = "LM1"
    lm.get_did.return_value = 1
    lm.get_name.return_value = "TestLM"
    lm.get_all_msels.return_value = [msel]
    config.add_lm(lm)

    # Act
    result = validator.validate(config)

    # Assert
    dup_rsrc_errors = [e for e in result if e.get_level() == logging.ERROR and "DUP_RSRC" in e.get_validation_id()]
    assert len(dup_rsrc_errors) == 1
    msg = dup_rsrc_errors[0].get_error_message()
    assert "2" in msg and "5" in msg and "8" in msg


# ============================================================================
# START/STOP NON-CONSECUTIVE SEQUENCE VALIDATION TESTS
# ============================================================================


def test_validate_lm_start_stop_non_consecutive_warning() -> None:
    """Test validation warning when start/stop sequence has non-consecutive positions"""
    # Arrange
    validator, config = test_utils.make_validator_and_config(LogicalMachinesValidator)

    start_stop = Mock()
    start_stop.get_resources.return_value = Mock()
    start_stop.get_resources.return_value.get_name.return_value = "resource1"

    # stop buckets: [[], [], [], [], [ss], [ss]] — positions 1-4 are gaps, valid at 5-6
    msel = Mock()
    msel.get_msel.return_value = 3
    msel.get_start_stop_buckets.side_effect = lambda is_start: [] if is_start else [[], [], [], [], [start_stop], [start_stop]]

    lm = Mock(spec=LM)
    lm.get_id.return_value = "LM1"
    lm.get_did.return_value = 1
    lm.get_name.return_value = "TestLM"
    lm.get_all_msels.return_value = [msel]

    config.add_lm(lm)

    # Act
    result = validator.validate(config)

    # Assert
    warning_entries = [entry for entry in result if entry.get_level() == logging.WARNING]
    warning_messages = [entry.get_error_message() for entry in warning_entries]
    assert len(warning_entries) > 0
    assert any("Non-consecutive stop sequence in LM1 mSel=3" in msg for msg in warning_messages)
    assert any("[1, 2, 3, 4]" in msg for msg in warning_messages)


def test_validate_lm_start_stop_consecutive_no_warning() -> None:
    """Test no warning when start/stop sequence is consecutive"""
    # Arrange
    validator, config = test_utils.make_validator_and_config(LogicalMachinesValidator)

    start_stop1 = Mock()
    start_stop1.get_resources.return_value = Mock()
    start_stop1.get_resources.return_value.get_name.return_value = "resource1"

    start_stop2 = Mock()
    start_stop2.get_resources.return_value = Mock()
    start_stop2.get_resources.return_value.get_name.return_value = "resource2"

    msel = Mock()
    msel.get_msel.return_value = 0
    msel.get_start_stop_buckets.side_effect = lambda is_start: [[start_stop1], [start_stop2]] if is_start else [[start_stop2], [start_stop1]]

    lm = Mock(spec=LM)
    lm.get_id.return_value = "LM1"
    lm.get_did.return_value = 1
    lm.get_name.return_value = "TestLM"
    lm.get_all_msels.return_value = [msel]

    config.add_lm(lm)

    # Act
    result = validator.validate(config)

    # Assert
    non_consecutive_warnings = [entry for entry in result if entry.get_level() == logging.WARNING and "Non-consecutive" in entry.get_error_message()]
    assert len(non_consecutive_warnings) == 0
