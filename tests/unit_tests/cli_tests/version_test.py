#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
from tests.test_utils import execute_cli


def test_version(capsys):
    code, out, err = execute_cli(capsys, ["-v"])
    assert code == 0
    assert err == ""
    assert out == "1.0.0\n"
    code, out, err = execute_cli(capsys, ["--version"])
    assert code == 0
    assert err == ""
    assert out == "1.0.0\n"
