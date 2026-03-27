#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Module for generating file config_fusa.h"""

from typing import Any, Dict, List

from smct import utils
from smct.configuration.confdata_fusa import FusaTask
from smct.generation.generator import GeneratorBase, GenHeading, GenMacroList, GenMacroValue, GenStructInit


class GeneratorFusa(GeneratorBase):
    """Generator for config_fusa.h file"""

    def _get_generator_info(self) -> Dict[str, Any]:
        """Get generator information.

        Returns:
            Dict[str, Any]: Dictionary containing generator name and includes.
        """
        # This must be overridden to avoid exception
        return {"name": "fusa", "incl": ["config_user.h"]}

    def _get_doxygen_file_name(self) -> str:
        """Get doxygen file name.

        Returns:
            str: Empty string for doxygen file name.
        """
        return ""

    def _get_doxygen_brief_lines(self) -> List[str]:
        """Get doxygen brief description lines.

        Returns:
            List[str]: List of brief description lines for doxygen.
        """
        return ["", "", " Header file containing FUSA-related configuration."]

    def _print_fusa_defines(self) -> None:
        """Generates fusa defines"""
        all_defines = self._get_configuration().get_fusa_configs()

        if all_defines:
            self.print_generator(GenHeading("FUSA Configuration Constants"))
            for config in self._get_configuration().get_fusa_configs():
                if utils.is_numeric_literal(config.get_value()):
                    config_macro = GenMacroValue(f"FUSA_{config.get_name()}", config.get_value(), config.get_comment())
                else:
                    config_macro = GenMacroValue(f"FUSA_{config.get_name()}", f'"{config.get_value()}"', config.get_comment())
                self.print_generator(config_macro)

    def _print_fusa_task_struct(self, task: FusaTask, def_name: str) -> None:
        """Generate task structure initializer specific task"""

        s = GenStructInit(def_name, "Task configuration" + (f": {task.get_comment()}" if task.get_comment() else ""))
        s["task"] = f"{task.get_name()}"
        s["period"] = f"{task.get_period_ms()}"
        s.print_head()
        s.print_members()
        s.print_tail()
        self._print(s.get_head_string(), end="")
        self._print(s.get_members_string(), end="")
        self._print(s.get_tail_string(), end="")

    def _print_fusa_tasks_for_type(self, tasks: List[FusaTask], task_type: str) -> None:
        """Generates fusa tasks of one type (thread|handler)"""

        # for now it is that easy (e.g. thread->THREAD, handler->HANDLER, but may get more complex later)
        def_word = task_type.upper()

        # taks count
        task_count = len(tasks)
        self.print_generator(GenMacroValue(f"FUSA_NUM_SCHEDULER_{def_word}_TASKS", task_count, f"Config for number of {task_type} tasks"))

        # each task structure
        for t in tasks:
            self._print_fusa_task_struct(t, f"FUSA_SCHEDULER_{def_word}_TASK{tasks.index(t)}_CONFIG")

        s = GenMacroList(f"FUSA_SCHEDULER_{def_word}_CONFIG", f"Config data array for {def_word} SCHEDULER")
        for i in range(0, task_count):
            s.add_value(f"FUSA_SCHEDULER_{def_word}_TASK{i}_CONFIG")
        self.print_generator(s)

    def _print_fusa_tasks(self) -> None:
        """Generates fusa tasks"""
        all_tasks = self._get_configuration().get_fusa_tasks()

        if all_tasks:
            # each type is generated separately
            for task_type in FusaTask.task_types:
                self.print_generator(GenHeading(f"FUSA {task_type.upper()} Tasks Configuration"))
                tasks = [t for t in all_tasks if t.get_task_type() == task_type]
                self._print_fusa_tasks_for_type(tasks, task_type)

    def print_content(self) -> None:
        """Generates content of this file"""
        self._print_fusa_defines()
        self._print_fusa_tasks()

    def __str__(self) -> str:
        """Returns string representation of the generator.

        Returns:
            str: String representation of the generator.
        """
        return "FUSA generator"
