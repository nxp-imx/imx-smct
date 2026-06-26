#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause

"""Test utility functions for SMCT testing framework."""

import os.path
import subprocess
from typing import Any, List, Tuple

from smct import smct
from smct.parsers.resource_parser import ResourceParser


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
