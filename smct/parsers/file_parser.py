#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Module related to parsing generic files"""
import re
from typing import Dict, List


class FileParser:
    """Generic file parser"""

    def __init__(self) -> None:
        self._patterns: List[str] = []
        self._results: Dict[str, List[re.Match]] = {}

    def add_regex(self, pattern_str: str) -> None:
        """Adds regex that will be parsed from files

        Args:
            pattern_str: The regex pattern string to add for parsing
        """
        self._patterns.append(pattern_str)

    def parse(self, file_path: str) -> None:
        """Parses all added regexes in given file and stores them internally

        Args:
            file_path: Path to the file to parse
        """
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
            for pattern_str in self._patterns:
                pattern = re.compile(pattern_str)
                match = pattern.search(content)
                while match is not None:
                    if pattern_str not in self._results:
                        self._results[pattern_str] = []
                    self._results[pattern_str].append(match)
                    end_position_of_match = match.regs[0][1]
                    match = pattern.search(content, pos=end_position_of_match)

    def get_results(self) -> Dict[str, List[re.Match]]:
        """Returns all the results

        Returns:
            Dictionary mapping pattern strings to lists of regex matches
        """
        return self._results
