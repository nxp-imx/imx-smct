#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause

"""Regression tests for FuSa configuration generation (SMCT-only feature)."""

import os.path
import re
from tempfile import TemporaryDirectory
from typing import Any

import pytest

from smct import utils
from tests.test_utils import execute_cli, get_smct_root


@pytest.mark.regression
def test_fusa_generation_mx95evk(capsys: Any) -> None:
    """Test FuSa configuration generation for MX95 EVK.

    This test validates that SMCT correctly generates config_fusa.h from
    FUSA_DEF and FUSA_TASK directives. The FuSa feature is SMCT-only and
    not present in the legacy Perl configtool.

    Args:
        capsys: Pytest capsys fixture
    """
    config = os.path.join(get_smct_root(), "test_resources", "configs_test", "mx95evk_fusa.cfg")

    with TemporaryDirectory() as test_dir:
        # Find firmware root
        firmware_root_temp = utils.find_firmware_root_dir(os.path.join(get_smct_root(), ".."))
        if firmware_root_temp is None:
            pytest.fail("Could not find firmware root directory")
            return
        firmware_root = os.path.abspath(firmware_root_temp)

        # Run SMCT
        code, _, _ = execute_cli(capsys, ["-c", config, "-o", test_dir, "--sm_dir", firmware_root])
        assert code == 0, "SMCT execution failed"

        # Read generated config_fusa.h
        fusa_file = os.path.join(test_dir, "config_fusa.h")
        assert os.path.exists(fusa_file), f"config_fusa.h not generated at {fusa_file}"

        with open(fusa_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Assertion 1: File exists (already checked above)

        # Assertion 2: Has include guard
        assert "#ifndef CONFIG_FUSA_H" in content, "Missing #ifndef CONFIG_FUSA_H include guard"
        assert "#define CONFIG_FUSA_H" in content, "Missing #define CONFIG_FUSA_H include guard"

        # Assertion 3: Has #include "config_user.h"
        assert '#include "config_user.h"' in content, "Missing #include \"config_user.h\""

        # Assertion 4: Contains expected defines
        assert re.search(r"#define\s+FUSA_WATCHDOG_TIMEOUT\s+5000U", content), "Missing FUSA_WATCHDOG_TIMEOUT define"
        assert re.search(r"#define\s+FUSA_MAX_RECOVERY_ATTEMPTS\s+3U", content), "Missing FUSA_MAX_RECOVERY_ATTEMPTS define"
        assert re.search(r'#define\s+FUSA_SAFETY_LEVEL\s+"SIL2"', content), "Missing FUSA_SAFETY_LEVEL define"

        # Assertion 5: Contains handler task scheduler
        assert re.search(r"#define\s+FUSA_NUM_SCHEDULER_HANDLER_TASKS\s+2U", content), "Missing FUSA_NUM_SCHEDULER_HANDLER_TASKS define"
        assert "FUSA_SCHEDULER_HANDLER_TASK0_CONFIG" in content, "Missing FUSA_SCHEDULER_HANDLER_TASK0_CONFIG"
        assert ".task = FUSA_WATCHDOG_CHECK" in content, "Missing FUSA_WATCHDOG_CHECK task assignment"
        assert ".period = 10" in content, "Missing period = 10 for FUSA_WATCHDOG_CHECK"
        assert "FUSA_SCHEDULER_HANDLER_TASK1_CONFIG" in content, "Missing FUSA_SCHEDULER_HANDLER_TASK1_CONFIG"
        assert ".task = FUSA_MEMORY_SCRUB" in content, "Missing FUSA_MEMORY_SCRUB task assignment"
        assert ".period = 100" in content, "Missing period = 100 for FUSA_MEMORY_SCRUB"

        # Assertion 6: Contains thread task scheduler
        assert re.search(r"#define\s+FUSA_NUM_SCHEDULER_THREAD_TASKS\s+1U", content), "Missing FUSA_NUM_SCHEDULER_THREAD_TASKS define"
        assert "FUSA_SCHEDULER_THREAD_TASK0_CONFIG" in content, "Missing FUSA_SCHEDULER_THREAD_TASK0_CONFIG"
        assert ".task = FUSA_DIAG_REPORT" in content, "Missing FUSA_DIAG_REPORT task assignment"
        assert ".period = 1000" in content, "Missing period = 1000 for FUSA_DIAG_REPORT"
