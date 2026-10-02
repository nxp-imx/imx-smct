#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause

"""Regression test: MSEL duplicate-order entries are preserved in config_lmm.h (Perl parity)."""

import logging
import os
import re
from tempfile import TemporaryDirectory
from typing import Any

from tests.test_utils import execute_cli, get_smct_root


def test_msel_duplicate_order_both_entries_in_start_data(capsys: Any, caplog: Any) -> None:
    """Duplicate start-order entries appear in SM_LM_START_DATA in author input order.

    Fixture LM1 has PD_M7@1, PD_M7@2, CPU_M7P@2, PD_M7@3; all four must be emitted in that order
    (Perl parity: Perl accumulates every entry; SMCT must do the same).
    """
    config_file = os.path.join(get_smct_root(), "test_resources", "configs_test", "msel_duplicate_order.cfg")
    root_dir = os.path.join(get_smct_root(), "test_resources")

    with TemporaryDirectory() as output_dir:
        caplog.set_level(logging.WARNING)
        code, _stdout, _stderr = execute_cli(capsys, ["-c", config_file, "-o", output_dir, "--sm_dir", root_dir, "-f"])

        assert code == 0, f"SMCT exited with code {code}"

        lmm_path = os.path.join(output_dir, "config_lmm.h")
        assert os.path.exists(lmm_path), "config_lmm.h was not generated"

        with open(lmm_path, "r", encoding="utf-8") as fh:
            content = fh.read()

        # SM_LM_NUM_START must reflect 4 entries (PD_M7@1, PD_M7@2, CPU_M7P@2, PD_M7@3)
        assert re.search(r"SM_LM_NUM_START\s+4U\b", content), "Expected 4 start entries in SM_LM_NUM_START"

        # SM_LM_NUM_STOP must reflect 3 entries (PD_M7@1, CPU_M7P@3, PD_M7@3)
        assert re.search(r"SM_LM_NUM_STOP\s+3U\b", content), "Expected 3 stop entries in SM_LM_NUM_STOP"

        # Perl-parity core assertion: duplicate slot entries survive AND author input order is preserved.
        # Isolate the SM_LM_START_DATA macro body, then read out the .rsrc identifiers in emission order.
        start_data_match = re.search(r"#define\s+SM_LM_START_DATA(.*?)(?=\n#define\b|\Z)", content, re.DOTALL)
        assert start_data_match is not None, "SM_LM_START_DATA block not found"
        rsrc_sequence = re.findall(r"\.rsrc\s*=\s*(\w+)", start_data_match.group(1))
        assert rsrc_sequence == [
            "DEV_SM_PD_M7",
            "DEV_SM_PD_M7",
            "DEV_SM_CPU_M7P",
            "DEV_SM_PD_M7",
        ], f"SM_LM_START_DATA .rsrc order mismatch: {rsrc_sequence}"

        # Same parity check for the stop side (guards the exporter/generator stop-branch).
        stop_data_match = re.search(r"#define\s+SM_LM_STOP_DATA(.*?)(?=\n#define\b|\Z)", content, re.DOTALL)
        assert stop_data_match is not None, "SM_LM_STOP_DATA block not found"
        stop_rsrc_sequence = re.findall(r"\.rsrc\s*=\s*(\w+)", stop_data_match.group(1))
        assert stop_rsrc_sequence == [
            "DEV_SM_PD_M7",
            "DEV_SM_CPU_M7P",
            "DEV_SM_PD_M7",
        ], f"SM_LM_STOP_DATA .rsrc order mismatch: {stop_rsrc_sequence}"

        # add_start_stop must not emit raw logger.error; ERRORs must go through ValidationEntry.
        raw_owner_errors = [r for r in caplog.records if r.levelno >= logging.ERROR and "owner_lm" in r.pathname]
        assert len(raw_owner_errors) == 0, "add_start_stop must not call logger.error; " f"got: {[r.message for r in raw_owner_errors]}"


def test_msel_duplicate_order_stop_gap_warning_emitted(capsys: Any, caplog: Any) -> None:
    """A gap in the stop sequence (PD_M7@stop=1, nothing at 2, CPU_M7P/PD_M7@stop=3) emits a WARNING."""
    config_file = os.path.join(get_smct_root(), "test_resources", "configs_test", "msel_duplicate_order.cfg")
    root_dir = os.path.join(get_smct_root(), "test_resources")

    with TemporaryDirectory() as output_dir:
        caplog.set_level(logging.WARNING)
        code, _stdout, _stderr = execute_cli(capsys, ["-c", config_file, "-o", output_dir, "--sm_dir", root_dir, "-f"])

        assert code == 0
        warning_records = [r for r in caplog.records if r.levelno == logging.WARNING and "Non-consecutive" in r.message]
        assert warning_records, "Expected a Non-consecutive stop-sequence WARNING in caplog"
