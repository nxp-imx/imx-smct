#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause

from typing import Any

from smct._version import __version__
from tests.test_utils import execute_cli


def test_version(capsys: Any) -> None:
    code, out, err = execute_cli(capsys, ["-v"])
    assert code == 0
    assert err == ""
    assert out == __version__ + "\n"
    code, out, err = execute_cli(capsys, ["--version"])
    assert code == 0
    assert err == ""
    assert out == __version__ + "\n"
