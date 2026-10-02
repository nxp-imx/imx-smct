#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Unit tests for smct.configuration.confdata_fusa FuSa data structures."""

# pylint: disable=missing-function-docstring

import logging
from typing import Iterator

import pytest

from smct.configuration.confdata_fusa import FusaConfigurationData, FusaDefine, FusaTask
from smct.configuration.configuration_provider import ConfigurationProvider
from smct.model.chip_model_provider import ChipModelProvider
from smct.resources.resource_database_provider import ResourceDatabaseProvider


@pytest.fixture(autouse=True)
def clear_providers() -> Iterator[None]:
    """Reset global providers and FuSa class state between tests."""
    ConfigurationProvider.clear_configuration()
    ResourceDatabaseProvider.clear_database()
    ChipModelProvider.clear_model()
    original_task_types = getattr(FusaTask, "task_types", None)
    FusaTask.task_types = {"handler": "handler", "thread": "thread"}
    yield
    if original_task_types is None:
        delattr(FusaTask, "task_types")
    else:
        FusaTask.task_types = original_task_types


class TestFusaDefine:
    """Tests for FusaDefine."""

    def test_construction_without_comment_uses_empty_comment(self) -> None:
        define = FusaDefine("WATCHDOG_TIMEOUT", 100)

        assert define.get_name() == "WATCHDOG_TIMEOUT"
        assert define.get_value() == 100
        assert define.get_comment() == ""
        assert define.get_assignment_json() == {"name": "WATCHDOG_TIMEOUT", "value": 100, "comment": ""}

    def test_construction_with_comment_exports_json(self) -> None:
        define = FusaDefine("CHECK_ENABLED", "true", "Enable check")

        assert define.get_assignment_json() == {"name": "CHECK_ENABLED", "value": "true", "comment": "Enable check"}


class TestFusaTask:
    """Tests for FusaTask."""

    def test_valid_task_keeps_period_type_and_comment(self) -> None:
        task = FusaTask("TASK_A", "2s", "thread", "Periodic task")

        assert task.get_name() == "TASK_A"
        assert task.get_period() == "2s"
        assert task.get_period_ms() == 2000
        assert task.get_task_type() == "thread"
        assert task.get_comment() == "Periodic task"
        assert task.get_assignment_json() == {"name": "TASK_A", "period": "2s", "type": "thread", "comment": "Periodic task"}

    def test_invalid_period_and_type_use_defaults(self, caplog: pytest.LogCaptureFixture) -> None:
        with caplog.at_level(logging.WARNING):
            task = FusaTask("TASK_BAD", "invalid", "bad_type")

        assert task.get_period() == 0
        assert task.get_period_ms() == 0
        assert task.get_task_type() == "handler"
        assert task.get_comment() == ""
        assert any("Invalid or missing period" in record.message for record in caplog.records)
        assert any("Invalid FUSA periodic task type" in record.message for record in caplog.records)


class TestFusaConfigurationData:
    """Tests for FusaConfigurationData."""

    def test_add_and_get_config_and_task_returns_stored_objects(self) -> None:
        data = FusaConfigurationData()
        define = FusaDefine("DEF_A", 1, "Definition")
        task = FusaTask("TASK_A", "10ms", "handler", "Task")

        data.add_config(define)
        data.add_task(task)

        assert data.get_config("DEF_A") == define
        assert data.get_task("TASK_A") == task
        assert data.get_all_configs() == [define]
        assert data.get_all_tasks() == [task]

    def test_get_assignment_json_exports_defines_and_tasks(self) -> None:
        data = FusaConfigurationData()
        data.add_config(FusaDefine("DEF_A", "VALUE", "Definition"))
        data.add_task(FusaTask("TASK_A", "10ms", "handler", "Task"))

        assert data.get_assignment_json() == {
            "defines": [{"name": "DEF_A", "value": "VALUE", "comment": "Definition"}],
            "tasks": [{"name": "TASK_A", "period": "10ms", "type": "handler", "comment": "Task"}],
        }

    def test_duplicate_names_keep_original_entries(self, caplog: pytest.LogCaptureFixture) -> None:
        data = FusaConfigurationData()
        first_define = FusaDefine("DUP", 1)
        first_task = FusaTask("TASK_DUP", "1ms", "handler")

        data.add_config(first_define)
        data.add_task(first_task)
        with caplog.at_level(logging.ERROR):
            data.add_config(FusaDefine("DUP", 2))
            data.add_task(FusaTask("TASK_DUP", "2ms", "thread"))

        assert data.get_config("DUP") == first_define
        assert data.get_task("TASK_DUP") == first_task
        assert data.get_all_configs() == [first_define]
        assert data.get_all_tasks() == [first_task]
        assert any("Duplicate name for FUSA_DEF" in record.message for record in caplog.records)
        assert any("Duplicate task for FUSA_TASK" in record.message for record in caplog.records)
