#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause

"""Module related to parsing header files."""

import copy
import logging
import os.path
import re
from typing import Any, Dict, List, Tuple

from smct.resources.resfactory import atomic_resource_from_raw
from smct.resources.resource_database_provider import ResourceDatabaseProvider

logger = logging.getLogger()


class HeaderParser:
    """Parser of .h files."""

    _patterns: Dict[re.Pattern, Dict[str, Any]] = {}

    def add_pattern(self, pattern: str, template: Dict[str, Any]) -> None:
        """Adds pattern to the parser.

        Args:
            pattern: Regular expression pattern to match
            template: Template dictionary for matched patterns
        """
        self._patterns[re.compile(pattern)] = copy.deepcopy(template)

    def _parse_file(self, file_path: str) -> None:
        """Parses the given file by registered patterns.

        Args:
            file_path: Path to the file to parse
        """
        absolute_file_path = os.path.abspath(file_path)
        if not os.path.isfile(absolute_file_path):
            logger.error("Cannot parse file '%s'", absolute_file_path, extra={"source": file_path})
            return
        logger.info("Parsing %s", absolute_file_path, extra={"source": file_path})
        with open(absolute_file_path, "r", encoding="utf-8") as f:
            for line in f.readlines():
                for pattern, template in self._patterns.items():
                    match = pattern.match(line)
                    if match:
                        raw = copy.deepcopy(template)
                        raw["name"] = match.group(1)
                        atom = atomic_resource_from_raw(raw)
                        if atom:
                            ResourceDatabaseProvider.get_database().add_atomic_resource(atom)

    def parse_dir_or_file(self, file_path: str, file_name_pattern: str = r".*\.h$") -> bool:
        """Parses files in the given directory if they match the file name pattern.

        Args:
            file_path: Path to file or directory to parse
            file_name_pattern: Regular expression pattern for matching file names

        Returns:
            True if parsing completed successfully
        """
        if os.path.isfile(file_path):
            self._parse_file(file_path)
        elif os.path.isdir(file_path):
            for file_name in os.listdir(file_path):
                absolute_path_of_file_in_directory = os.path.join(file_path, file_name)
                if os.path.isdir(absolute_path_of_file_in_directory):
                    self.parse_dir_or_file(absolute_path_of_file_in_directory, file_name_pattern)
                elif re.match(file_name_pattern, file_name):
                    self._parse_file(absolute_path_of_file_in_directory)
        return True


class ApiResourceParser:
    """API resource parser. Parses all API resources in given file/directory."""

    _apiResTypes: List[Tuple[str, str | None]] = [
        # permission,   header-parsing prefix
        ("pdPerms", "PD"),
        ("clkPerms", "CLK"),
        ("perfPerms", "PERF"),
        ("cpuPerms", "CPU"),
        ("buttonPerms", "BUTTON"),
        ("sensorPerms", "SENSOR"),
        ("pinPerms", "PIN"),
        ("daisyPerms", "DAISY"),
        ("rstPerms", "RST"),
        ("voltPerms", "VOLT"),
        ("gprPerms", "GPR"),
        ("rtcPerms", "RTC"),
        ("perlpiPerms", "PERLPI"),
        ("faultPerms", "FAULT"),
        ("ctrlPerms", "CTRL"),
        ("basePerms", None),
        ("sysPerms", None),
        ("lmmPerms", None),
        ("fusaPerms", None),
    ]

    def parse_device(self, root_directory: str, device_name: str) -> bool:
        """Parses files of given device.

        Args:
            root_directory: Root directory path containing device files
            device_name: Name of the device to parse

        Returns:
            True if parsing completed successfully, False if device path doesn't exist
        """
        header_parser = HeaderParser()

        for _, api in self._apiResTypes:
            if api is not None:  # parse-able from header?
                header_parser.add_pattern(f"#define\\s+DEV_SM_({api}_\\w+)\\s+\\S", {"name": None, "type": "API", "cat": "DEV", "api": api})

        path = os.path.join(root_directory, "devices", device_name, "sm")
        if not os.path.exists(path):
            logging.error("Invalid device name '%s', path '%s' does not exist", device_name, os.path.abspath(path), extra={"source": path})
            return False
        return header_parser.parse_dir_or_file(path, r"dev_sm_.*\.h$")

    def parse_board(self, root_directory: str, board_name: str) -> bool:
        """Parses files of given board.

        Args:
            root_directory: Root directory path containing board files
            board_name: Name of the board to parse

        Returns:
            True if parsing completed successfully, False if board path doesn't exist
        """
        header_parser = HeaderParser()

        for resource_type in self._apiResTypes:
            api = resource_type[1]
            if api:  # parse-able from header?
                header_parser.add_pattern(f"#define\\s+(BRD_SM_{api}_\\w+)\\s+\\S", {"name": None, "type": "API", "cat": "BRD", "api": api})

        path = os.path.join(root_directory, "boards", board_name, "sm")
        if not os.path.exists(path):
            logging.error("Invalid board name '%s', path '%s' does not exist", board_name, os.path.abspath(path), extra={"source": path})
            return False
        return header_parser.parse_dir_or_file(path, r"brd_sm_.*\.h$")
