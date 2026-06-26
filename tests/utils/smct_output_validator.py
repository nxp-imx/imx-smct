#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause

"""SMCT output validator for structural correctness checks."""

import glob
import os
import re
from typing import List, Tuple


class SmctOutputValidator:
    """Validates structural correctness of SMCT-generated C headers.

    Performs independent self-consistency checks on SMCT output without
    relying on Perl golden output comparison.
    """

    _re_define = re.compile(r"^#define\s+(\w+)", re.MULTILINE)
    _re_ifndef = re.compile(r"^#ifndef\s+\w+", re.MULTILINE)
    _re_endif = re.compile(r"^#endif", re.MULTILINE)

    def __init__(self, output_dir: str) -> None:
        """Initialize validator with SMCT output directory.

        Args:
            output_dir: Path to SMCT output directory containing .h files
        """
        self.output_dir = output_dir

    def validate(self) -> Tuple[bool, List[str]]:
        """Validate SMCT output for structural correctness.

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues: List[str] = []
        h_files = glob.glob(os.path.join(self.output_dir, "**", "*.h"), recursive=True)

        if not h_files:
            issues.append("No .h files found in output directory")
            return False, issues

        for h_file in h_files:
            rel_path = os.path.relpath(h_file, self.output_dir)

            try:
                with open(h_file, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception as e:
                issues.append(f"{rel_path}: Failed to read file: {e}")
                continue

            # Check 1: Non-empty file (> 10 bytes minimum)
            if len(content) <= 10:
                issues.append(f"{rel_path}: File is too small (likely empty or malformed)")
                continue

            # Check 2: Header guard presence and closure
            ifndef_matches = self._re_ifndef.findall(content)
            endif_matches = self._re_endif.findall(content)

            if ifndef_matches and not endif_matches:
                issues.append(f"{rel_path}: Has #ifndef but missing closing #endif")
            elif len(ifndef_matches) != len(endif_matches):
                issues.append(
                    f"{rel_path}: Mismatched header guards "
                    f"(#ifndef: {len(ifndef_matches)}, #endif: {len(endif_matches)})"
                )

            # Check 3: No duplicate #define names within a single file
            define_names = self._re_define.findall(content)
            if len(define_names) != len(set(define_names)):
                duplicates = [name for name in define_names if define_names.count(name) > 1]
                unique_duplicates = sorted(set(duplicates))
                issues.append(f"{rel_path}: Duplicate #define names: {', '.join(unique_duplicates)}")

            # Check 4: Balanced braces
            open_braces = content.count("{")
            close_braces = content.count("}")
            if open_braces != close_braces:
                issues.append(
                    f"{rel_path}: Unbalanced braces "
                    f"({{ : {open_braces}, }} : {close_braces})"
                )

        return len(issues) == 0, issues
