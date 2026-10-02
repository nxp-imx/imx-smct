#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Module with logical machine related validations."""

import logging
import re
from typing import Dict, List

from smct import utils
from smct.configuration.confdata import ConfigurationData
from smct.owners.owner_lm import LM
from smct.validation.validation_entry import ValidationEntry
from smct.validation.validator_base import ValidatorBase


def _validate_lm0(logical_machine: LM, result: List[ValidationEntry]) -> None:
    """Checks validity of logical machine 0 configuration.

    Args:
        logical_machine: The logical machine to validate.
        result: List to append validation entries to.
    """
    source = "/".join(["user_config", logical_machine.get_name()])
    did = logical_machine.get_did()
    if did != LM.sm_did:
        validation_id = ".".join([logical_machine.get_id(), "DID"])
        result.append(ValidationEntry(logging.ERROR, source, f"LM0 must have TRDC domain '{LM.sm_did}'", validation_id))
    name = logical_machine.get_name()
    expected_name = "SM"
    if name != expected_name:
        validation_id = ".".join([logical_machine.get_id(), "NAME"])
        result.append(ValidationEntry(logging.ERROR, source, f"LM0 does not have required name '{expected_name}'", validation_id))
    expected_safe = "feenv"
    if logical_machine.get_safe() != expected_safe:
        validation_id = ".".join([logical_machine.get_id(), "SAFE"])
        result.append(ValidationEntry(logging.WARNING, source, f"LM0 does not have required safety type '{expected_safe}'", validation_id))
    expected_boot = 1
    boot = logical_machine.get_boot()
    if boot != expected_boot:
        validation_id = ".".join([logical_machine.get_id(), "MSEL0", "BOOT"])
        result.append(ValidationEntry(logging.ERROR, source, f"LM0 does not have required boot order '{expected_boot}'", validation_id))
    expected_skip = False
    skip = logical_machine.get_skip()
    if skip != expected_skip:
        validation_id = ".".join([logical_machine.get_id(), "MSEL0", "SKIP"])
        msg = f"LM0 does have unsupported parameter skip '{str(skip).lower()}'. " f"Allowed value is '{str(expected_skip).lower()}' or not specifying it"
        result.append(ValidationEntry(logging.ERROR, source, msg, validation_id))
    expected_rpc = "none"
    rpc = logical_machine.get_rpc()
    if rpc != expected_rpc:
        validation_id = ".".join([logical_machine.get_id(), "RPC"])
        result.append(ValidationEntry(logging.ERROR, source, f"LM0 does not have required RPC type '{expected_rpc}'", validation_id))
    else:
        start_stops = logical_machine.get_all_start_stops(is_start=True) + logical_machine.get_all_start_stops(is_start=False)
        if not logical_machine.get_assigned_resources() and not logical_machine.get_all_agents() and not start_stops:
            result.append(ValidationEntry(logging.WARNING, source, "LM0 has no configuration"))


def _validate_lm_names_uniqueness(logical_machines: List[LM], result: List[ValidationEntry]) -> None:
    """Checks validity of logical machines names uniqueness.

    Args:
        logical_machines: List of logical machines to validate.
        result: List to append validation entries to.
    """
    machines_by_names = {}
    for logical_machine in logical_machines:
        if logical_machine.get_name() not in machines_by_names:
            machines_by_names[logical_machine.get_name()] = [logical_machine.get_id()]
        else:
            machines_by_names[logical_machine.get_name()].append(logical_machine.get_id())
    for name, ids in machines_by_names.items():
        if len(ids) > 1:
            for lm_id in ids:
                source = "/".join(["user_config", name])
                validation_id = ".".join([lm_id, "NAME"])
                result.append(ValidationEntry(logging.ERROR, source, f"Logical machines '{', '.join(ids)}' have duplicate name '{name}'", validation_id))


def _validate_lm_ids(logical_machines: List[LM], result: List[ValidationEntry]) -> None:
    """Checks validity of the logical machine IDs.

    Args:
        logical_machines: List of logical machines to validate.
        result: List to append validation entries to.
    """
    pattern = re.compile(r"LM(\d+)")
    ids = []
    for logical_machine in logical_machines:
        lm_id = logical_machine.get_id()
        match = pattern.match(lm_id)
        if match is not None:
            ids.append(utils.parse_int(match.group(1)))
        else:
            source = "/".join(["user_config", logical_machine.get_name()])
            validation_id = ".".join([lm_id, "ID"])
            msg = f"Logical machine ID '{lm_id}' does not match required pattern"
            result.append(ValidationEntry(logging.ERROR, source, msg, validation_id))

    logical_machines_amount = len(logical_machines)
    if len(ids) == 0:
        return
    highest_logical_machine_id = max(ids)
    lowest_logical_machine_id = min(ids)
    if lowest_logical_machine_id != 0:
        source = "/".join(["user_config", f"LM{lowest_logical_machine_id}"])
        validation_id = ".".join([f"LM{lowest_logical_machine_id}", "ID"])
        msg = f"Logical machine IDs must start from 0, but there is no LM0 in the configuration. " f"Lowest ID is {lowest_logical_machine_id}"
        result.append(ValidationEntry(logging.ERROR, source, msg, validation_id))
    if highest_logical_machine_id >= logical_machines_amount:
        source = "/".join(["user_config", f"LM{highest_logical_machine_id}"])
        validation_id = ".".join([f"LM{highest_logical_machine_id}", "ID"])
        msg = f"Logical machine {highest_logical_machine_id} has higher ID " f"than there is amount of logical machines in total ({logical_machines_amount})"
        result.append(ValidationEntry(logging.ERROR, source, msg, validation_id))
    if not utils.are_all_numbers_present(ids):
        result.append(ValidationEntry(logging.ERROR, "user_config", f"Logical machine IDs contain a gap: {ids}"))
    if not utils.are_numbers_consecutive(ids):
        result.append(ValidationEntry(logging.ERROR, "user_config", f"Logical machine IDs are not consecutive: {ids}"))


def _validate_lm_msels(logical_machines: List[LM], result: List[ValidationEntry]) -> None:
    """Checks msels for duplicate start/stop orders and same-resource multi-order definitions.

    Args:
        logical_machines: List of logical machines to validate.
        result: List to append validation entries to.
    """
    for logical_machine in logical_machines:
        for msel in logical_machine.get_all_msels():
            for is_start in (True, False):
                direction = "START" if is_start else "STOP"
                buckets = msel.get_start_stop_buckets(is_start)
                source = "/".join(["user_config", logical_machine.get_name(), f"MSEL{msel.get_msel()}", direction])

                # A. Duplicate order: two or more resources share the same order slot.
                for order_idx, bucket in enumerate(buckets):
                    if len(bucket) > 1:  # includes same resource repeated within one bucket
                        order = order_idx + 1
                        names = ", ".join(ss.get_resources().get_name() for ss in bucket)
                        validation_id = ".".join([logical_machine.get_id(), f"MSEL{msel.get_msel()}", direction, "DUP_ORDER", str(order)])
                        msg = (
                            f"Duplicate {direction.lower()} order {order} in {logical_machine.get_id()} MSEL{msel.get_msel()} — "
                            f"resources [{names}] all share order number {order}. "
                            f"Firmware executes them sequentially; verify if this is intentional."
                        )
                        result.append(ValidationEntry(logging.ERROR, source, msg, validation_id))

                # B. Same resource at multiple distinct orders (a single bucket repeat is left to DUP_ORDER).
                rsrc_orders: Dict[str, List[int]] = {}
                for order_idx, bucket in enumerate(buckets):
                    for ss in bucket:
                        name = ss.get_resources().get_name()
                        if name not in rsrc_orders:
                            rsrc_orders[name] = []
                        rsrc_orders[name].append(order_idx + 1)
                for rsrc_name, orders in rsrc_orders.items():
                    unique_orders = sorted(set(orders))  # set() drops same-bucket repeats (handled by DUP_ORDER)
                    if len(unique_orders) > 1:
                        validation_id = ".".join([logical_machine.get_id(), f"MSEL{msel.get_msel()}", direction, "DUP_RSRC", rsrc_name])
                        msg = (
                            f"Resource '{rsrc_name}' appears in the {direction.lower()} sequence of "
                            f"{logical_machine.get_id()} MSEL{msel.get_msel()} at orders {unique_orders} — typically a typo."
                        )
                        result.append(ValidationEntry(logging.ERROR, source, msg, validation_id))


def _validate_lm_start_stop_non_consecutive(logical_machines: List[LM], result: List[ValidationEntry]) -> None:
    """Checks start/stop sequences for non-consecutive positions.

    Args:
        logical_machines: List of logical machines to validate.
        result: List to append validation entries to.
    """
    for logical_machine in logical_machines:
        for msel in logical_machine.get_all_msels():
            for is_start in (True, False):
                buckets = msel.get_start_stop_buckets(is_start)
                gap_positions = [i + 1 for i, bucket in enumerate(buckets) if not bucket]
                if gap_positions:
                    mode = "start" if is_start else "stop"
                    source = "/".join(["user_config", logical_machine.get_name(), f"MSEL{msel.get_msel()}"])
                    validation_id = ".".join([logical_machine.get_id(), f"MSEL{msel.get_msel()}", mode.upper(), "NON_CONSECUTIVE"])
                    msg = (
                        f"Non-consecutive {mode} sequence in {logical_machine.get_id()} mSel={msel.get_msel()}: "
                        f"positions {gap_positions} are unused — use consecutive indices starting from 1"
                    )
                    result.append(ValidationEntry(logging.WARNING, source, msg, validation_id))


def _validate_lm_default_option(logical_machines: List[LM], result: List[ValidationEntry]) -> None:
    """Checks validity of logical machine default options.

    Args:
        logical_machines: List of logical machines to validate.
        result: List to append validation entries to.
    """
    lm_defaults = list(filter(lambda lm: lm.get_default(), logical_machines))
    if len(lm_defaults) > 1:
        for lm in lm_defaults:
            source = "/".join(["user_config", lm.get_name()])
            validation_id = ".".join([lm.get_id(), "DEFAULT"])
            msg = f"Option 'default' is set for multiple logical machines but will only be applied for the {lm_defaults[-1].get_id()}"
            result.append(ValidationEntry(logging.WARNING, source, msg, validation_id))


class LogicalMachinesValidator(ValidatorBase):
    """Validator of logical machines."""

    def validate(self, configuration: ConfigurationData) -> List[ValidationEntry]:
        """Validates logical machines configuration.

        Args:
            configuration: Configuration data to validate.

        Returns:
            List of validation entries containing any validation errors or warnings.
        """
        result: List[ValidationEntry] = []
        logical_machines = configuration.get_all_lms()
        _validate_lm_ids(logical_machines, result)
        _validate_lm_names_uniqueness(logical_machines, result)
        _validate_lm_default_option(logical_machines, result)
        _validate_lm_msels(logical_machines, result)
        _validate_lm_start_stop_non_consecutive(logical_machines, result)
        for logical_machine in logical_machines:
            if logical_machine.get_id() == "LM0":
                _validate_lm0(logical_machine, result)
        return result
