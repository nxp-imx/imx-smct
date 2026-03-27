#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause

"""File comparison utility for testing"""

import difflib
import glob
import os
import pathlib
import re
import shutil
import sys
from argparse import ArgumentParser
from io import StringIO
from typing import Dict, List, Optional


class FileDiffer:
    """Utility class for comparing files and detecting differences"""

    default_c_files_pattern = "**/*.c;**/*.h"

    section_comment_multiline = r"([\t ]*/\*(?:.|[\n\r\s])*?\*/[\t ]*)"
    section_tabs = r"([\t ]*$)"
    section_trailing_spaces = r"(\s+$)"
    section_multiline_separator = r"([\t ]*//.*?$)"
    patterns_array = [section_comment_multiline, section_tabs, section_trailing_spaces, section_multiline_separator]
    strip_pattern = re.compile(r"|".join(patterns_array), re.MULTILINE)
    space_trimming_pattern = re.compile(r" +")

    def __init__(
        self,
        file_filter: str,
        golden_folder_path: Optional[str] = None,
        test_folder_path: Optional[str] = None,
        diff_folder_path: Optional[str] = None,
        debug: bool = False,
    ) -> None:
        """Initialize FileDiffer with paths and settings.

        Args:
            file_filter: Glob pattern for files to compare
            golden_folder_path: Path to golden reference files
            test_folder_path: Path to test output files
            diff_folder_path: Path to store diff results
            debug: Enable debug output
        """
        self.file_filter = file_filter
        self.test_folder_path = os.getcwd() if test_folder_path is None else test_folder_path
        self.diff_folder_path = diff_folder_path
        self.golden_folder_path = golden_folder_path
        self.debug = debug

        self._missing_in_golden_sample: List[str] = []
        self._missing_in_test_sample: List[str] = []
        self._errors: Dict[str, str] = {}

    def get_error_files(self) -> List[str]:
        """Get list of files with differences.

        Returns:
            List of file paths that have differences
        """
        return list(self._errors.keys())

    def get_error(self, file: str) -> str:
        """Get diff output for a specific file.

        Args:
            file: File path to get error for

        Returns:
            Diff string for the file
        """
        return self._errors[file]

    def store_differences_to_disk(self, diff_folder_path: str) -> None:
        """Store diff results to disk.

        Args:
            diff_folder_path: Directory to store diff files
        """
        for file in self._errors:
            diff_file_path = os.path.join(diff_folder_path, "-".join(pathlib.Path(file).parts)) + ".diff"
            with open(diff_file_path, "w", encoding="utf-8") as f:
                f.write(self._errors[file])

    def check_differences(self) -> bool:
        """Check for differences between golden and test files.

        Returns:
            True if no differences found, False otherwise
        """
        files: List[str] = []
        for file_filter in self.file_filter.split(";"):
            files.extend(os.path.relpath(path, self.test_folder_path) for path in glob.glob(os.path.join(self.test_folder_path, file_filter), recursive=True))

        for file in files:
            self._check_file(file)

        # Copy files that are different
        error_file_names = self._errors.keys()
        if len(error_file_names) != 0:
            diff_folder_path = self.diff_folder_path
            if diff_folder_path is not None:
                if os.path.exists(diff_folder_path):
                    shutil.rmtree(diff_folder_path)
                os.makedirs(os.path.join(diff_folder_path, "golden"), exist_ok=True)
                os.makedirs(os.path.join(diff_folder_path, "test"), exist_ok=True)
                os.makedirs(os.path.join(diff_folder_path, "diff"), exist_ok=True)
                for error_file_name in error_file_names:
                    file_golden_folder = os.path.join(self.golden_folder_path, error_file_name)
                    file_test_folder = os.path.join(self.test_folder_path, error_file_name)
                    diff_golden_file = os.path.join(diff_folder_path, "golden", error_file_name)
                    diff_test_file = os.path.join(diff_folder_path, "test", error_file_name)
                    diff_file = os.path.join(diff_folder_path, "diff", error_file_name)
                    shutil.copy(file_golden_folder, diff_golden_file)
                    shutil.copy(file_test_folder, diff_test_file)
                    with open(diff_file, "w", encoding="utf-8") as file_handle:
                        file_handle.write(self._errors[error_file_name])

        return len(self._errors) == 0

    def _check_file(self, file: str) -> bool:
        """Check a single file for differences.

        Args:
            file: Relative path to file to check

        Returns:
            True if files match, False otherwise
        """
        result = True
        old_lines: List[str] = []
        new_lines: List[str] = []
        perform_diff_of_files = True

        try:
            with open(os.path.join(self.golden_folder_path, file), "r", encoding="utf-8") as golden_sample_file:
                golden_content = golden_sample_file.read()
                golden_content = re.sub(self.strip_pattern, "", golden_content)
                golden_content = re.sub(self.space_trimming_pattern, " ", golden_content)
                old_lines = [ln for ln in golden_content.splitlines() if ln not in ("", "\r\n", "\n", "\r")]
        except FileNotFoundError:
            self._missing_in_golden_sample.append(file)
            perform_diff_of_files = False

        try:
            with open(os.path.join(self.test_folder_path, file), "r", encoding="utf-8") as test_file:
                test_content = test_file.read()
                test_content = re.sub(self.strip_pattern, "", test_content)
                test_content = re.sub(self.space_trimming_pattern, " ", test_content)
                new_lines = [ln for ln in test_content.splitlines() if ln not in ("", "\r\n", "\n", "\r")]
        except FileNotFoundError:
            self._missing_in_test_sample.append(file)

        if perform_diff_of_files:
            diff = difflib.unified_diff(old_lines, new_lines)
            diff_list = list(diff)
            if len(diff_list) > 0:
                diff_str = "\n".join(diff_list)
                self._errors[file] = diff_str
                result = False
        return result

    def get_string_result(self) -> str:
        """Get formatted string of all differences.

        Returns:
            Formatted string containing all differences
        """
        buffer = StringIO()
        for file_path, error in self._errors.items():
            print(f"Difference in file {file_path}", file=buffer)
            print(error, file=buffer)

        for missing_file in self._missing_in_test_sample:
            print(f"File {missing_file} was not found in test sample", file=buffer)

        buffer.seek(0)
        return buffer.read()

    def get_status(self) -> str:
        """Get status summary of diff operation.

        Returns:
            Status string with summary of differences
        """
        return (
            f"INFO: diff ended, {len(self._missing_in_golden_sample)} files were not found in golden sample archive, "
            f"{len(self._errors)} files were different"
        )


if __name__ == "__main__":
    parser = ArgumentParser(description="Diffs the current build with the last archived in artifactory")
    parser.add_argument("filefilter", metavar="filefilter", help="path to files in glob wildcard format. Multiple can be given separated in semicolons")
    parser.add_argument("-b", "--basepath", help="Basepath from which the filter is considered. Working directory is default", default=None)
    parser.add_argument("-g", "--goldenpath", help="Path with golden samples directory", default=None)
    parser.add_argument("-d", "--diffdir", help="Save the results into the following directory", default=None)
    parser.add_argument("--debug", action="store_const", const=True, default=False, help="print extra debug info")
    args = parser.parse_args()
    differ = FileDiffer(args.filefilter, golden_folder_path=args.goldenpath, test_folder_path=args.basepath, diff_folder_path=args.diffdir, debug=args.debug)
    differences = differ.check_differences()
    if not differences and args.diffdir is not None:
        differ.store_differences_to_disk(args.diffdir)
    sys.exit(0 if differences else 1)
