#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause

"""Perl configtool output classifier for known defects."""

import enum
import glob
import os
import re
from typing import Dict


class PerlFileStatus(enum.Enum):
    """Classification status for Perl-generated files."""

    VALID = "valid"
    TRUNCATED = "truncated"
    EMPTY = "empty"
    MISSING = "missing"
    PATH_AS_NAME = "path_as_name"


class PerlOutputClassifier:
    """Detects known Perl configtool defects in golden output.

    The legacy Perl tool has known defects (e.g., error_line() stopping
    mid-file) that cause malformed output. This classifier detects those
    defects so they can be excluded from comparison instead of patching.
    """

    _re_ifndef = re.compile(r"^#ifndef\s+\w+", re.MULTILINE)
    _re_endif = re.compile(r"^#endif", re.MULTILINE)
    _re_cfg_name = re.compile(r'#define\s+SM_LM_CFG_NAME\s+"([^"]*)"')

    def __init__(self, output_dir: str) -> None:
        """Initialize classifier with Perl output directory.

        Args:
            output_dir: Path to Perl golden output directory containing .h files
        """
        self.output_dir = output_dir

    def classify(self) -> Dict[str, PerlFileStatus]:
        """Classify each file in Perl output by defect status.

        Returns:
            Dictionary mapping relative file path to PerlFileStatus
        """
        classifications: Dict[str, PerlFileStatus] = {}
        h_files = glob.glob(os.path.join(self.output_dir, "**", "*.h"), recursive=True)

        for h_file in h_files:
            rel_path = os.path.relpath(h_file, self.output_dir)
            status = self._classify_file(h_file)
            classifications[rel_path] = status

        return classifications

    def _classify_file(self, file_path: str) -> PerlFileStatus:
        """Classify a single Perl output file.

        Args:
            file_path: Absolute path to file

        Returns:
            PerlFileStatus classification
        """
        if not os.path.exists(file_path):
            return PerlFileStatus.MISSING

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except OSError:
            return PerlFileStatus.MISSING

        # Check for empty or whitespace-only files
        if not content.strip():
            return PerlFileStatus.EMPTY

        # Check for truncated files: has #ifndef but missing #endif
        # This is the known Perl error_line() bug
        has_ifndef = self._re_ifndef.search(content) is not None
        has_endif = self._re_endif.search(content) is not None

        if has_ifndef and not has_endif:
            return PerlFileStatus.TRUNCATED

        # Check for path-as-name defect in SM_LM_CFG_NAME
        # MSYS2/Cygwin Perl's fileparse doesn't recognize backslash separators
        cfg_name_match = self._re_cfg_name.search(content)
        if cfg_name_match:
            cfg_name_value = cfg_name_match.group(1)
            # Detect if value looks like a filesystem path
            if "\\" in cfg_name_value or "/" in cfg_name_value or ":" in cfg_name_value:
                return PerlFileStatus.PATH_AS_NAME

        return PerlFileStatus.VALID
