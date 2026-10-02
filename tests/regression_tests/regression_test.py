#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause

"""Regression tests for all device configurations.

Tests MX94 and MX95 family configurations against legacy Perl tool output.
Delegates to shared regression test runner in regression_device_test_base.
"""

import os.path
from typing import Any

import pytest

from tests.regression_tests.regression_device_test_base import (
    run_device_regression_test,
    SM_FW_CONFIGS_DIR,
    SMCT_CONFIGS_DIR,
)

FILES = [
    # MX94 — default runs
    pytest.param(os.path.join(SM_FW_CONFIGS_DIR, "mx94evk.cfg"), id="mx94evk.cfg"),
    # MX94 — extended (redundant / longest wall-clock)
    pytest.param(os.path.join(SM_FW_CONFIGS_DIR, "mx94alt.cfg"), id="mx94alt.cfg", marks=pytest.mark.extended),
    pytest.param(os.path.join(SMCT_CONFIGS_DIR, "mx94netc.cfg"), id="mx94netc.cfg", marks=pytest.mark.extended),
    # MX937 — default runs
    pytest.param(os.path.join(SM_FW_CONFIGS_DIR, "mx937frdm.cfg"), id="mx937frdm.cfg"),
    # MX937 — extended
    pytest.param(os.path.join(SM_FW_CONFIGS_DIR, "mx937alt.cfg"), id="mx937alt.cfg", marks=pytest.mark.extended),
    # MX95 — default runs
    pytest.param(os.path.join(SM_FW_CONFIGS_DIR, "mx95evk.cfg"), id="mx95evk.cfg"),
    pytest.param(os.path.join(SMCT_CONFIGS_DIR, "mx95netc.cfg"), id="mx95netc.cfg"),
    # MX95 — extended (identical signature to EVK counterparts; mx952alt is redundant with mx95alt)
    pytest.param(os.path.join(SM_FW_CONFIGS_DIR, "mx95alt.cfg"), id="mx95alt.cfg", marks=pytest.mark.extended),
    pytest.param(os.path.join(SM_FW_CONFIGS_DIR, "mx95frdm.cfg"), id="mx95frdm.cfg", marks=pytest.mark.extended),
    pytest.param(os.path.join(SM_FW_CONFIGS_DIR, "mx952evk.cfg"), id="mx952evk.cfg", marks=pytest.mark.extended),
    pytest.param(os.path.join(SM_FW_CONFIGS_DIR, "mx952alt.cfg"), id="mx952alt.cfg", marks=pytest.mark.extended),
    # Shared / cross-device — default runs
    pytest.param(os.path.join(SMCT_CONFIGS_DIR, "24_12_LM0_no_config.cfg"), id="24_12_LM0_no_config.cfg"),
    pytest.param(os.path.join(SMCT_CONFIGS_DIR, "mx95evk_fusa.cfg"), id="mx95evk_fusa.cfg"),
    # Shared / cross-device — extended (TRDC dedup; Perl diff excluded; correctness covered by unit tests)
    pytest.param(os.path.join(SMCT_CONFIGS_DIR, "mx95_trdc_dedup.cfg"), id="mx95_trdc_dedup.cfg", marks=pytest.mark.extended),
    pytest.param(os.path.join(SMCT_CONFIGS_DIR, "trdc_dup_difftest.cfg"), id="trdc_dup_difftest.cfg", marks=pytest.mark.extended),
]

# Expected differences between Perl configtool and SMCT output.
# These files are skipped in the regression diff comparison because SMCT
# intentionally optimizes TRDC register generation compared to Perl:
#
# mx95_trdc_dedup.cfg → config_trdc.h:
#   SMCT deduplicates identical MRC RGD entries and MDAC writes when multiple
#   agents on the same DID assign the same resource with the same permissions.
#   Perl emits duplicate register writes. Both are functionally equivalent
#   (idempotent hardware writes). Correctness verified by test_trdc_dedup_usecase.py.
#
# trdc_dup_difftest.cfg → config_trdc.h:
#   Same deduplication behavior plus SMCT ORs permissions when agents share a
#   DID but differ in security attributes. Perl emits separate writes.
#   Correctness verified by test_trdc_dup_difftest.py.
#
# TODO: As SMCT TRDC generation reaches full Perl parity, entries here should shrink.
_EXPECTED_DIFFS: dict[str, set[str]] = {
    "mx95_trdc_dedup.cfg": {"config_trdc.h"},
    "trdc_dup_difftest.cfg": {"config_trdc.h"},
}


@pytest.mark.regression
@pytest.mark.parametrize("config", FILES)
def test_regression(capsys: Any, config: str) -> None:
    """Test configuration files against legacy Perl tool output.

    Args:
        capsys: Pytest capsys fixture
        config: Absolute path to the configuration file to test
    """
    expected_diffs = _EXPECTED_DIFFS.get(os.path.basename(config))
    run_device_regression_test(capsys, config, expected_diff_files=expected_diffs)
