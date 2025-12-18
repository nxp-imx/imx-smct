#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Module implementing FUSA-related subset of user configuration"""

import logging
from typing import Any, Dict, List

from smct import utils

logger = logging.getLogger()


class FusaDefine:
    """Object representing FUSA macro value"""

    def __init__(self, name: str, value: Any, comment: str | None = None) -> None:
        self._name: str = name
        self._value: Any = value
        self._comment: str = comment if comment else ""

    def get_name(self) -> str:
        """Returns Define Name"""
        return self._name

    def get_value(self) -> Any:
        """Returns Define value"""
        return self._value

    def get_comment(self) -> str:
        """Returns Define comment"""
        return self._comment

    def get_assignment_json(self) -> object:
        """Returns dictionary representing this object as JSON."""
        ret = {"name": self._name, "value": self._value, "comment": self._comment}
        return ret


class FusaTask:
    """Object representing FUSA periodic task"""

    # dict of allowed fusa task types assignment
    task_types: Dict[str, str]

    def __init__(self, name: str, period: Any | None, task_type: str | None = None, comment: str | None = None) -> None:
        self._name: str = name
        self._period: Any = 0  # Default initialization
        if period and utils.parse_time_to_ms(str(period)) is not None:
            self._period = period
        else:
            source = "/".join(["user_config", self._name])
            validation_id = ".".join(["FUSA_TASK", self._name, "period"])
            logger.warning("Invalid or missing period specification for FUSA task '%s'", name, extra={"source": source, "validation_id": validation_id})
        self._type: str = "handler"  # default task type
        if task_type in FusaTask.task_types:
            self._type = task_type
        elif task_type is not None:
            source = "/".join(["user_config", self._name])
            validation_id = ".".join(["FUSA_TASK", self._name, "type"])
            logger.warning("Invalid FUSA periodic task type '%s' for FUSA task '%s'", task_type, name, extra={"source": source, "validation_id": validation_id})
        self._comment: str = comment if comment else ""

    def get_name(self) -> str:
        """Returns Task name"""
        return self._name

    def get_period(self) -> Any:
        """Returns Task period string specification (known to be valid)"""
        return self._period

    def get_period_ms(self) -> int:
        """Returns Task period in milliseconds"""
        ms = utils.parse_time_to_ms(str(self._period), throw=True)
        return ms if ms else 0

    def get_task_type(self) -> str:
        """Returns Task type string (one of FusaTask.Types)"""
        return self._type

    def get_comment(self) -> str:
        """Returns Task's comment"""
        return self._comment

    def get_assignment_json(self) -> object:
        """Returns dictionary representing this object as JSON."""
        ret = {
            "name": self._name,
            "period": self._period,
            "type": self._type,
            "comment": self._comment,
        }
        return ret


class FusaConfigurationData:
    """FUSA-related user configuration data"""

    def __init__(self) -> None:
        self._config: Dict[str, FusaDefine] = {}
        self._tasks: Dict[str, FusaTask] = {}

    def add_config(self, config: FusaDefine) -> None:
        """Add a FUSA configuration define to the configuration list.

        Args:
            config: FusaDefine object to be added to the configuration
        """
        if config.get_name() not in self._config:
            self._config[config.get_name()] = config
        else:
            source = "/".join(["FUSA_DEF", config.get_name()])
            validation_id = ".".join(["FUSA_DEF", config.get_name(), "name"])
            logger.error("Duplicate name for FUSA_DEF define '%s'", config.get_name(), extra={"source": source, "validation_id": validation_id})

    def get_all_configs(self) -> List[FusaDefine]:
        """Returns all FUSA configuration defines.

        Returns:
            List of FusaDefine objects.
        """
        return list(self._config.values())

    def add_task(self, task: FusaTask) -> None:
        """Add a FUSA task.

        Args:
            task: FusaTask object to be added to the configuration
        """
        if task.get_name() not in self._tasks:
            self._tasks[task.get_name()] = task
        else:
            source = "/".join(["FUSA_TASK", task.get_name()])
            validation_id = ".".join(["FUSA_TASK", task.get_name(), "name"])
            logger.error("Duplicate task for FUSA_TASK define '%s'", task.get_name(), extra={"source": source, "validation_id": validation_id})

    def get_all_tasks(self) -> List[FusaTask]:
        """Returns all FUSA tasks.

        Returns:
            List of FusaTask objects.
        """
        return list(self._tasks.values())

    def get_config(self, name: str) -> FusaDefine | None:
        """Returns FUSA Define by name or None if it does not exist"""
        return self._config.get(name)

    def get_task(self, name: str) -> FusaTask | None:
        """Returns FUSA Task by name or None if it does not exist"""
        return self._tasks.get(name)

    def get_assignment_json(self) -> object:
        """Returns dictionary representing this object as JSON.

        Returns:
            Dictionary containing all parameters important for serialization.
        """
        ret = {
            "defines": [self._config[c].get_assignment_json() for c in self._config],
            "tasks": [self._tasks[t].get_assignment_json() for t in self._tasks],
        }
        return ret
