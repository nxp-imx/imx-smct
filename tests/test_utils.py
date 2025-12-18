#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
import os.path
import subprocess
from typing import List, Tuple

from smct import smct
from smct.parsers.resource_parser import ResourceParser


def execute_cli(capsys, arguments: List[str]) -> Tuple[int, str, str]:
    code = smct.main(arguments)
    out, error = capsys.readouterr()
    return code, out, error


def get_smct_root() -> str:
    folder, file = os.path.split(os.path.realpath(__file__))
    return os.path.abspath(os.path.join(folder, ".."))


def execute_binary(binary_path: str, arguments: List[str], stdin: str | None = None) -> Tuple[int, str, str]:
    process_arguments = [binary_path] + arguments
    process = subprocess.Popen(process_arguments, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if stdin is not None:
        process.stdin.write(stdin.encode("utf-8"))
    code = process.wait()
    stdout = process.stdout.read().decode("utf-8")
    stderr = process.stderr.read().decode("utf-8")
    return code, stdout, stderr

def set_up() -> None:
    rp = ResourceParser("default")
    rp.parse_soc_resources()