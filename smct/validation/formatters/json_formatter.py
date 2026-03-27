#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Module related to formatting logs into JSON output"""

import json
import logging
import os
import sys
from logging import LogRecord
from logging.handlers import MemoryHandler
from typing import Dict, List


class JsonFormatter:
    """Formatter of LogRecords to JSON format"""

    def format_logs(self, records: list[LogRecord]) -> str:
        """Formats list of LogRecord to dictionary form with log level as key.

        Args:
            records: List of LogRecord objects to format.

        Returns:
            JSON string representation of formatted log records organized by level.
        """
        record_dict: Dict[str, List] = {"DEBUG": [], "INFO": [], "WARNING": [], "ERROR": [], "CRITICAL": []}
        for record in records:
            record_dict[record.levelname].append(self._format_log(record))
        return json.dumps(record_dict, indent=2)

    @classmethod
    def _format_log(cls, record: logging.LogRecord) -> Dict[str, object]:
        """Formats a single LogRecord to JSON format.

        Args:
            record: LogRecord object to format.

        Returns:
            Dictionary containing formatted log record data.
        """
        record_dict: Dict[str, object] = {
            "description": record.getMessage(),
        }
        if hasattr(record, "validation_id"):
            record_dict["validation_id"] = record.validation_id
        else:
            record_dict["validation_id"] = "None"
        if hasattr(record, "source"):
            record_dict["source"] = record.source
        else:
            record_dict["source"] = "unknown source"
        record_dict["filename"] = record.filename
        record_dict["line"] = record.lineno
        record_dict["function"] = record.funcName
        return record_dict


class JsonMemoryHandler(logging.handlers.MemoryHandler):
    """MemoryHandler used to buffer LogRecords and flush them into output file"""

    def __init__(self, formatter: JsonFormatter, output_folder: str, mode: str):
        """Initialize JsonMemoryHandler.

        Args:
            formatter: JsonFormatter instance for formatting log records.
            output_folder: Directory path where log file will be created.
            mode: File mode for writing the log file.
        """
        MemoryHandler.__init__(self, capacity=sys.maxsize, flushOnClose=True, target=None)
        self.log_file: str = os.path.join(output_folder, "error_log.json")
        self.mode: str = mode
        self.log_formatter: JsonFormatter = formatter

    def shouldFlush(self, _: LogRecord) -> bool:
        """Returns true if the buffer is up to capacity. This method is
        overridden to implement custom flushing strategy.

        Args:
            _: LogRecord (unused parameter).

        Returns:
            Always returns False to implement custom flushing strategy.
        """
        return False

    def flush(self) -> None:
        """Flushes LogRecords to specified output file."""
        self.acquire()
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        with open(self.log_file, self.mode, encoding="utf-8") as file:
            file.write(self.log_formatter.format_logs(self.buffer))
        self.release()
