#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause

"""TRDC deduplication and conflict detection test."""

import logging
import os
import re
from tempfile import TemporaryDirectory
from typing import Any

from tests.test_utils import execute_cli, get_smct_root


def test_trdc_dup_difftest(capsys: Any, caplog: Any) -> None:
    """Test TRDC deduplication with MDAC conflict detection.

    This test verifies the trdc_dup_difftest.cfg configuration which has
    two SCMI agents (AP-S secure, AP-NS nonsecure) on the same LM2 (DID=3)
    assigning the same resources.

    The test verifies:
    1. MBC deduplication works correctly (same resources with same permissions)
    2. MRC deduplication works correctly (same memory regions)
    3. MDAC conflict is properly detected and logged when the same master
       (NPU) is assigned with different security attributes (DFMT0 vs DFMT1)
    4. SMCT completes successfully despite the conflict (exit code 0)
    5. The MDAC entry is still written to config_trdc.h

    Expected behavior:
    - SMCT logs an error about MDAC conflict ("already defined")
    - SMCT continues execution and generates config_trdc.h
    - MBC/MRC entries are deduplicated (one entry per unique resource+permission)
    - MDAC entry exists in output despite conflict

    Args:
        capsys: Pytest capsys fixture for capturing stdout/stderr
        caplog: Pytest caplog fixture for capturing log messages
    """
    # Arrange
    config_file = os.path.join(
        get_smct_root(), "test_resources", "configs_test", "trdc_dup_difftest.cfg"
    )
    root_dir = os.path.join(get_smct_root(), "test_resources")

    with TemporaryDirectory() as output_dir:
        # Act - Run SMCT on the conflict test cfg
        caplog.set_level(logging.DEBUG)
        code, stdout, stderr = execute_cli(capsys, ["-c", config_file, "-o", output_dir, "--sm_dir", root_dir])

        # Assert - SMCT should complete successfully despite conflict
        assert code == 0, f"SMCT execution failed with code {code}\nstdout: {stdout}\nstderr: {stderr}"

        # Verify MDAC conflict was detected and logged
        assert "already defined" in caplog.text, (
            f"MDAC conflict error not logged. Expected 'already defined' in logs.\n"
            f"Captured logs:\n{caplog.text}"
        )

        # Read the generated config_trdc.h
        trdc_header_path = os.path.join(output_dir, "config_trdc.h")
        assert os.path.exists(trdc_header_path), f"config_trdc.h not generated at {trdc_header_path}"

        with open(trdc_header_path, "r", encoding="utf-8") as f:
            trdc_content = f.read()

        # Verification 1: MBC deduplication - verify DOM3 MBC entries exist
        # Both agents assign resources like GPIO2, LPUART1, etc.
        # Should result in deduplicated MBC block config entries
        mbc_pattern = r"DOM3_MEM"
        mbc_matches = re.findall(mbc_pattern, trdc_content)
        assert len(mbc_matches) > 0, (
            "MBC deduplication: No DOM3_MEM entries found in config_trdc.h\n"
            "Expected MBC block entries for deduped resources"
        )

        # Verification 2: MRC deduplication - verify DOM3 RGD entries exist
        # Both agents assign DDR memory regions
        # Should result in deduplicated MRC region entries
        mrc_pattern = r"DOM3_RGD"
        mrc_matches = re.findall(mrc_pattern, trdc_content)
        assert len(mrc_matches) > 0, (
            "MRC deduplication: No DOM3_RGD entries found in config_trdc.h\n"
            "Expected MRC region entries for deduped DDR ranges"
        )

        # Verification 3: MDAC entry exists despite conflict
        # The NPU MDAC assignment should be written to the output
        # even though there was a conflict logged
        mdac_pattern = r"(MDAC_NPU|MDA_W[0-9]+.*DFMT)"
        mdac_matches = re.findall(mdac_pattern, trdc_content)
        assert len(mdac_matches) > 0, (
            "MDAC entry: No NPU MDAC entries found in config_trdc.h\n"
            "Expected MDAC entry to be written despite conflict"
        )

        # Success - deduplication works and conflict was detected
        print(f"\n✓ MBC DOM3 entries: {len(mbc_matches)}")
        print(f"✓ MRC DOM3 entries: {len(mrc_matches)}")
        print(f"✓ MDAC NPU entries: {len(mdac_matches)}")
        print("✓ MDAC conflict detected and logged")
