#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause

"""Test utility functions for SMCT testing framework."""

import os.path
import subprocess
from contextlib import contextmanager
from typing import Any, Dict, Iterator, List, Tuple, Type

from smct import smct
from smct.configuration.confdata import ConfigurationData
from smct.configuration.confdata_fusa import FusaTask
from smct.model.model_trdc import MbcModel, MrcModel, TrdcModel
from smct.owners.owner_agent import Channel, Mailbox, ScmiAgent
from smct.owners.owner_lm import LM
from smct.parsers.resource_parser import ResourceParser

# ---------------------------------------------------------------------------
# TRDC register layout constants shared between test files
# ---------------------------------------------------------------------------

DFMT0_REG: Dict[str, Dict[str, int]] = {
    "SA": {"offset": 5, "width": 2},
    "VLD": {"offset": 3, "width": 1},
    "DFMT": {"offset": 2, "width": 1},
    "DID": {"offset": 0, "width": 2},
    "KPA": {"offset": 4, "width": 1},
    "SID": {"offset": 8, "width": 6},
}

DFMT1_REG: Dict[str, Dict[str, int]] = {
    "SA": {"offset": 5, "width": 2},
    "PA": {"offset": 7, "width": 2},
    "VLD": {"offset": 3, "width": 1},
    "DFMT": {"offset": 2, "width": 1},
    "DID": {"offset": 0, "width": 2},
    "KPA": {"offset": 4, "width": 1},
    "SID": {"offset": 8, "width": 6},
}


def execute_cli(capsys: Any, arguments: List[str]) -> Tuple[int, str, str]:
    """Execute SMCT CLI with given arguments and capture output.

    Args:
        capsys: Pytest capsys fixture for capturing stdout/stderr
        arguments: List of command-line arguments to pass to SMCT

    Returns:
        Tuple of (exit_code, stdout, stderr)
    """
    code = smct.main(arguments)
    out, error = capsys.readouterr()
    return code, out, error


def get_smct_root() -> str:
    """Get the root directory of the SMCT project.

    Returns:
        Absolute path to SMCT root directory
    """
    folder, _ = os.path.split(os.path.realpath(__file__))
    return os.path.abspath(os.path.join(folder, ".."))


def execute_binary(binary_path: str, arguments: List[str], stdin: str | None = None, timeout: int = 300) -> Tuple[int, str, str]:
    """Execute external binary with given arguments.

    Args:
        binary_path: Path to the binary to execute
        arguments: List of command-line arguments
        stdin: Optional stdin input string
        timeout: Maximum seconds to wait for process completion (default: 300)

    Returns:
        Tuple of (exit_code, stdout, stderr)
    """
    process_arguments = [binary_path] + arguments
    input_data = stdin.encode("utf-8") if stdin is not None else None
    with subprocess.Popen(process_arguments, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as process:
        try:
            stdout_bytes, stderr_bytes = process.communicate(input=input_data, timeout=timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate()
            raise
    return process.returncode, stdout_bytes.decode("utf-8"), stderr_bytes.decode("utf-8")


def set_up() -> None:
    """Set up test environment by parsing default resources."""
    rp = ResourceParser("default")
    rp.parse_soc_resources()


# ---------------------------------------------------------------------------
# Generic restore helper
# ---------------------------------------------------------------------------


def restore_class_attr(cls: type, name: str, val: Any) -> None:
    """Restore a class attribute to its saved value, or delete it if it was absent.

    Args:
        cls: The class whose attribute to restore.
        name: The attribute name.
        val: The original value returned by ``getattr(cls, name, None)``; ``None``
             signals the attribute did not exist before and should be deleted.
    """
    if val is None:
        if hasattr(cls, name):
            delattr(cls, name)
    else:
        setattr(cls, name, val)


# ---------------------------------------------------------------------------
# File-read helper
# ---------------------------------------------------------------------------


def read_generated_file(file_path: str) -> str:
    """Read and return the entire text content of a generated file.

    Args:
        file_path: Absolute path to the file to read.

    Returns:
        File contents as a string.
    """
    with open(file_path, "r", encoding="utf-8") as fh:
        return fh.read()


# ---------------------------------------------------------------------------
# Context managers for class-attribute save/restore
# ---------------------------------------------------------------------------


@contextmanager
def restore_mbc_mrc_class_attrs(
    *,
    block_size: int = 0x8000,
    register_width: int = 32,
    nse_bit_offset: int = 4,
    strt_addr_offset: int = 14,
    end_addr_offset: int = 14,
) -> Iterator[None]:
    """Save/restore MbcModel and MrcModel class-level attributes.

    Sets standard test values on entry and restores originals on exit.

    Args:
        block_size: Value for MbcModel.block_size (default 0x8000).
        register_width: Value for MbcModel.register_width (default 32).
        nse_bit_offset: Value for MbcModel.nse_bit_offset (default 4).
        strt_addr_offset: Value for MrcModel.strt_addr_offset (default 14).
        end_addr_offset: Value for MrcModel.end_addr_offset (default 14).
    """
    orig_bs = getattr(MbcModel, "block_size", None)
    orig_rw = getattr(MbcModel, "register_width", None)
    orig_nse = getattr(MbcModel, "nse_bit_offset", None)
    orig_strt = getattr(MrcModel, "strt_addr_offset", None)
    orig_end = getattr(MrcModel, "end_addr_offset", None)
    MbcModel.block_size = block_size
    MbcModel.register_width = register_width
    MbcModel.nse_bit_offset = nse_bit_offset
    MrcModel.strt_addr_offset = strt_addr_offset
    MrcModel.end_addr_offset = end_addr_offset
    try:
        yield
    finally:
        restore_class_attr(MbcModel, "block_size", orig_bs)
        restore_class_attr(MbcModel, "register_width", orig_rw)
        restore_class_attr(MbcModel, "nse_bit_offset", orig_nse)
        restore_class_attr(MrcModel, "strt_addr_offset", orig_strt)
        restore_class_attr(MrcModel, "end_addr_offset", orig_end)


@contextmanager
def restore_trdc_class_attrs(
    *,
    pa_types: Dict[str, Any] | None = None,
    sa_types: Dict[str, Any] | None = None,
    permission_types: Dict[str, Any] | None = None,
    dfmt0_register: Dict[str, Any] | None = None,
    dfmt1_register: Dict[str, Any] | None = None,
    debug_domain_permission: int | None = None,
) -> Iterator[None]:
    """Save/restore TrdcModel class-level attributes and set specified test values.

    Only attributes explicitly passed (non-None) are mutated; others are left
    unchanged.  All saved values are restored unconditionally on exit.

    Args:
        pa_types: Test value for TrdcModel.pa_types.
        sa_types: Test value for TrdcModel.sa_types.
        permission_types: Test value for TrdcModel.permission_types.
        dfmt0_register: Test value for TrdcModel.DFMT0_register.
        dfmt1_register: Test value for TrdcModel.DFMT1_register.
        debug_domain_permission: Test value for TrdcModel.DEBUG_DOMAIN_PERMISSION.
    """
    _trdc_attrs = [
        "pa_types",
        "sa_types",
        "permission_types",
        "DFMT0_register",
        "DFMT1_register",
        "DEBUG_DOMAIN_PERMISSION",
    ]
    saved = {a: getattr(TrdcModel, a, None) for a in _trdc_attrs}
    if pa_types is not None:
        TrdcModel.pa_types = pa_types
    if sa_types is not None:
        TrdcModel.sa_types = sa_types
    if permission_types is not None:
        TrdcModel.permission_types = permission_types
    if dfmt0_register is not None:
        TrdcModel.DFMT0_register = dfmt0_register
    if dfmt1_register is not None:
        TrdcModel.DFMT1_register = dfmt1_register
    if debug_domain_permission is not None:
        TrdcModel.DEBUG_DOMAIN_PERMISSION = debug_domain_permission
    try:
        yield
    finally:
        for attr, val in saved.items():
            restore_class_attr(TrdcModel, attr, val)


@contextmanager
def restore_owner_class_attrs() -> Iterator[None]:
    """Save/restore owner class-level type-mapping attributes.

    Saves Channel.rpc_types, LM.safety_types, LM.auto_boot_types,
    Mailbox.mailbox_types, Mailbox.mailbox_priority_types, and
    FusaTask.task_types, then sets canonical test values for each before
    yielding.  All originals are restored on exit.
    """
    _owner_attrs: List[Tuple[type, str]] = [
        (Channel, "rpc_types"),
        (LM, "safety_types"),
        (LM, "auto_boot_types"),
        (Mailbox, "mailbox_types"),
        (Mailbox, "mailbox_priority_types"),
        (FusaTask, "task_types"),
    ]
    saved = [(cls, attr, getattr(cls, attr, None)) for cls, attr in _owner_attrs]
    Channel.rpc_types = {"none": "NONE", "scmi": "SCMI"}
    LM.safety_types = {"nseenv": "NSEENV", "safe": "SAFE"}
    LM.auto_boot_types = {"auto": "AUTO"}
    Mailbox.mailbox_types = {"mu": "MU", "loopback": "LOOPBACK"}
    Mailbox.mailbox_priority_types = {"np": "NP"}
    FusaTask.task_types = {"handler": "handler", "thread": "thread", "periodic": "periodic"}
    try:
        yield
    finally:
        for cls, attr, val in saved:
            restore_class_attr(cls, attr, val)


@contextmanager
def restore_dfmt_registers() -> Iterator[None]:
    """Save/restore TrdcModel.DFMT0_register and DFMT1_register around a test.

    Does not mutate the attributes — only saves and restores them, so the test
    body can freely set them without leaking state to the next test.
    """
    orig_dfmt0 = getattr(TrdcModel, "DFMT0_register", None)
    orig_dfmt1 = getattr(TrdcModel, "DFMT1_register", None)
    try:
        yield
    finally:
        restore_class_attr(TrdcModel, "DFMT0_register", orig_dfmt0)
        restore_class_attr(TrdcModel, "DFMT1_register", orig_dfmt1)


# ---------------------------------------------------------------------------
# Data-builder helpers
# ---------------------------------------------------------------------------


def build_two_seenv_lms(
    conf: ConfigurationData,
) -> Tuple[LM, ScmiAgent, ScmiAgent, LM, ScmiAgent]:
    """Build two SEENV LMs with agents and add them to *conf*.

    Creates ``first_seenv_lm`` (two agents) and ``second_seenv_lm`` (one
    agent), wires them up, adds both to *conf*, and returns the objects so
    callers can make assertions against them.

    Args:
        conf: ConfigurationData instance to populate.

    Returns:
        Tuple of (first_seenv_lm, first_agent0, first_agent1,
                  second_seenv_lm, second_agent0).
    """
    first_seenv_lm = LM("first_seenv_lm_id", 1, "FirstSeenvLM", "scmi", None, "seenv", None, None, True)
    first_agent0 = ScmiAgent("first_agent0_id", first_seenv_lm, "FirstAgent0", True)
    first_agent1 = ScmiAgent("first_agent1_id", first_seenv_lm, "FirstAgent1", True)
    first_seenv_lm.add_agent(first_agent0)
    first_seenv_lm.add_agent(first_agent1)
    second_seenv_lm = LM("second_seenv_lm_id", 2, "SecondSeenvLM", "scmi", None, "seenv", None, None, True)
    second_agent0 = ScmiAgent("second_agent0_id", second_seenv_lm, "SecondAgent0", True)
    second_seenv_lm.add_agent(second_agent0)
    conf.add_lm(first_seenv_lm)
    conf.add_lm(second_seenv_lm)
    return first_seenv_lm, first_agent0, first_agent1, second_seenv_lm, second_agent0


def build_conf_with_lm_and_agent() -> Tuple[ConfigurationData, LM, ScmiAgent]:
    """Build a minimal ConfigurationData with one LM and one SCMI agent.

    Calls :func:`set_up` internally to parse the default resource database.

    Returns:
        Tuple of (conf, lm, agent).
    """
    set_up()
    conf = ConfigurationData()
    lm = LM("id", 0, "name", None, None, None, None, None, True)
    conf.add_lm(lm)
    agent = ScmiAgent("id", lm, "name", True)
    lm.add_agent(agent)
    return conf, lm, agent


def make_validator_and_config(validator_cls: Type[Any]) -> Tuple[Any, ConfigurationData]:
    """Instantiate a validator and an empty ConfigurationData.

    Args:
        validator_cls: The validator class to instantiate.

    Returns:
        Tuple of (validator_instance, ConfigurationData()).
    """
    return validator_cls(), ConfigurationData()


def add_initial_default_permissions(resource: Any, expected_json: Dict[str, Any], begin: Any, size: Any) -> None:
    """Add the first two canonical default-permission entries to *resource*.

    Appends the matching dicts to ``expected_json["default_permissions"]`` so
    callers can continue the JSON-comparison test without repeating this setup.

    Args:
        resource: An MbcResource or MrcResource instance.
        expected_json: The raw-JSON dict being built up by the test.
        begin: FormatedInt begin address.
        size: FormatedInt size value.
    """
    resource.add_default_permission(begin, size, (2, 12), "none", True)
    expected_json["default_permissions"] = []
    expected_json["default_permissions"].append({"begin": begin, "size": size, "domains": {"from": 2, "to": 12}, "permission": "none"})
    resource.add_default_permission(begin, size, (2, 12), "none", False)
    expected_json["default_permissions"].append({"begin": begin, "size": size, "domains": {"from": 2, "to": 12}, "permission": "none", "no_debug": True})
