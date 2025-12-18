#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
import os
from tempfile import TemporaryDirectory
from smct.configuration.confdata import ConfigurationData
from smct.configuration.confdata_fusa import FusaDefine, FusaTask
from smct.generation.gen_fusa import GeneratorFusa

def _generate_and_read(conf: ConfigurationData, generator: GeneratorFusa, directory: TemporaryDirectory) -> str:
    generator.generate(conf, directory.name)
    file_name = os.path.join(directory.name, "config_fusa.h")
    content = ""
    with open(file_name, "r") as file:
        content = file.read()
    return content


def test_basic_fusa_def() -> None:
    """Test basic FUSA definition generation."""
    # Arrange
    directory = TemporaryDirectory()
    generator = GeneratorFusa()
    conf = ConfigurationData()
    
    # Act
    conf.add_fusa_config("FUSA_DEF_1", 1, "Test FUSA definition")
    content = _generate_and_read(conf, generator, directory)
    
    # Assert
    expected_fusa_def = "/*! Test FUSA definition */\n#define FUSA_FUSA_DEF_1  1U"
    assert expected_fusa_def in content

    expected_fusa_object = FusaDefine("FUSA_DEF_1", 1, "Test FUSA definition")
    assert len(conf.get_fusa_configs()) == 1

    actual_fusa_object = conf.get_fusa_configs()[0]
    assert actual_fusa_object.get_name() == expected_fusa_object.get_name()
    assert actual_fusa_object.get_value() == expected_fusa_object.get_value()
    assert actual_fusa_object.get_comment() == expected_fusa_object.get_comment()


def test_various_fusa_def_types() -> None:
    """Test various FUSA definition value types."""
    # Arrange
    directory = TemporaryDirectory()
    generator = GeneratorFusa()
    conf = ConfigurationData()
    
    # Act
    conf.add_fusa_config("FUSA_DEF_NUMBER", 42, "Number definition")
    conf.add_fusa_config("FUSA_DEF_COMMENT", "100", "Commented number")
    conf.add_fusa_config("FUSA_DEF_STRING", "TEST_VALUE", "String definition")
    conf.add_fusa_config("FUSA_DEF_ULL", "200ULL", "C style ULL number")
    content = _generate_and_read(conf, generator, directory)
    
    # Assert
    expected_number = '/*! Number definition */\n#define FUSA_FUSA_DEF_NUMBER  42U'
    expected_comment = '/*! Commented number */\n#define FUSA_FUSA_DEF_COMMENT  "100"'
    expected_string = '/*! String definition */\n#define FUSA_FUSA_DEF_STRING  "TEST_VALUE"'
    expected_ull = '/*! C style ULL number */\n#define FUSA_FUSA_DEF_ULL  200ULL'
    
    assert expected_number in content
    assert expected_comment in content
    assert expected_string in content
    assert expected_ull in content


def test_basic_fusa_task() -> None:
    """Test basic FUSA task generation."""
    # Arrange
    directory = TemporaryDirectory()
    generator = GeneratorFusa()
    conf = ConfigurationData()
    FusaTask.task_types = {
        "handler": "handler",
        "thread": "thread"
    }
    
    # Act
    conf.add_fusa_task("FUSA_TASK_1", 1, "handler", "Test FUSA task")
    content = _generate_and_read(conf, generator, directory)
    
    # Assert
    expected_fusa_task = (
        "/*! Task configuration: Test FUSA task */\n"
        "#define FUSA_SCHEDULER_HANDLER_USER_TASK0_CONFIG \\\n"
        "    { \\\n"
        "        .task = FUSA_TASK_1, \\\n"
        "        .period = 1, \\\n"
        "    }"
    )
    assert expected_fusa_task in content
    expected_handler_tasks = '#define FUSA_NUM_SCHEDULER_HANDLER_USER_TASKS  1U'
    assert expected_handler_tasks in content
    expected_thread_tasks = '#define FUSA_NUM_SCHEDULER_THREAD_USER_TASKS  0U'
    assert expected_thread_tasks in content
    expected_fusa_object = FusaTask("FUSA_TASK_1", 1, "handler", "Test FUSA task")
    assert len(conf.get_fusa_tasks()) == 1

    actual_fusa_object = conf.get_fusa_tasks()[0]
    assert actual_fusa_object.get_name() == expected_fusa_object.get_name()
    assert actual_fusa_object.get_period() == expected_fusa_object.get_period()
    assert actual_fusa_object.get_comment() == expected_fusa_object.get_comment()

def test_various_fusa_task_types() -> None:
    """Test various FUSA task types (handler and thread)."""
    # Arrange
    directory = TemporaryDirectory()
    generator = GeneratorFusa()
    conf = ConfigurationData()
    FusaTask.task_types = {
        "handler": "handler",
        "thread": "thread"
    }

    # Act
    conf.add_fusa_task("FUSA_HANDLER_TASK_1", 10, "handler", "First handler task")
    conf.add_fusa_task("FUSA_HANDLER_TASK_2", 20, "handler", "Second handler task")
    conf.add_fusa_task("FUSA_THREAD_TASK_1", 30, "thread", "First thread task")
    conf.add_fusa_task("FUSA_THREAD_TASK_2", 40, "thread", "Second thread task")
    content = _generate_and_read(conf, generator, directory)

    # Assert
    # Handler tasks
    expected_handler_count = "/*! Config for number of handler user tasks */\n#define FUSA_NUM_SCHEDULER_HANDLER_USER_TASKS  2U"
    assert expected_handler_count in content

    expected_handler_task1 = (
        "/*! Task configuration: First handler task */\n"
        "#define FUSA_SCHEDULER_HANDLER_USER_TASK0_CONFIG \\\n"
        "    { \\\n"
        "        .task = FUSA_HANDLER_TASK_1, \\\n"
        "        .period = 10, \\\n"
        "    }"
    )
    assert expected_handler_task1 in content

    expected_handler_task2 = (
        "/*! Task configuration: Second handler task */\n"
        "#define FUSA_SCHEDULER_HANDLER_USER_TASK1_CONFIG \\\n"
        "    { \\\n"
        "        .task = FUSA_HANDLER_TASK_2, \\\n"
        "        .period = 20, \\\n"
        "    }"
    )
    assert expected_handler_task2 in content

    expected_handler_config = (
        "/*! Config data array for HANDLER SCHEDULER */\n"
        "#define FUSA_SCHEDULER_HANDLER_USER_CONFIG \\\n"
        "    FUSA_SCHEDULER_HANDLER_USER_TASK0_CONFIG, \\\n"
        "    FUSA_SCHEDULER_HANDLER_USER_TASK1_CONFIG"
    )
    assert expected_handler_config in content

    # Thread tasks
    expected_thread_count = "/*! Config for number of thread user tasks */\n#define FUSA_NUM_SCHEDULER_THREAD_USER_TASKS  2U"
    assert expected_thread_count in content

    expected_thread_task1 = (
        "/*! Task configuration: First thread task */\n"
        "#define FUSA_SCHEDULER_THREAD_USER_TASK0_CONFIG \\\n"
        "    { \\\n"
        "        .task = FUSA_THREAD_TASK_1, \\\n"
        "        .period = 30, \\\n"
        "    }"
    )
    assert expected_thread_task1 in content

    expected_thread_task2 = (
        "/*! Task configuration: Second thread task */\n"
        "#define FUSA_SCHEDULER_THREAD_USER_TASK1_CONFIG \\\n"
        "    { \\\n"
        "        .task = FUSA_THREAD_TASK_2, \\\n"
        "        .period = 40, \\\n"
        "    }"
    )
    assert expected_thread_task2 in content

    expected_thread_config = (
        "/*! Config data array for THREAD SCHEDULER */\n"
        "#define FUSA_SCHEDULER_THREAD_USER_CONFIG \\\n"
        "    FUSA_SCHEDULER_THREAD_USER_TASK0_CONFIG, \\\n"
        "    FUSA_SCHEDULER_THREAD_USER_TASK1_CONFIG"
    )
    assert expected_thread_config in content

    # Verify all tasks were added
    assert len(conf.get_fusa_tasks()) == 4

def test_fusa_scheduler_time_conversion() -> None:
    """Test FUSA scheduler generation with different time suffixes and invalid periods."""
    # Arrange
    directory = TemporaryDirectory()
    generator = GeneratorFusa()
    conf = ConfigurationData()
    FusaTask.task_types = {
        "handler": "handler",
        "thread": "thread"
    }
    
    # Act
    conf.add_fusa_task("FUSA_HANDLER_TASK_1", "10ms", "handler", "First handler task")
    conf.add_fusa_task("FUSA_HANDLER_TASK_2", "2s", "handler", "Second handler task")
    conf.add_fusa_task("FUSA_THREAD_TASK_1", None, "thread", "First thread task")
    conf.add_fusa_task("FUSA_THREAD_TASK_2", "invalid_period", "thread", "Second thread task")
    content = _generate_and_read(conf, generator, directory)
    
    # Assert
    # Handler tasks with time suffixes
    expected_handler_task1 = (
        "/*! Task configuration: First handler task */\n"
        "#define FUSA_SCHEDULER_HANDLER_USER_TASK0_CONFIG \\\n"
        "    { \\\n"
        "        .task = FUSA_HANDLER_TASK_1, \\\n"
        "        .period = 10, \\\n"
        "    }"
    )
    assert expected_handler_task1 in content
    
    expected_handler_task2 = (
        "/*! Task configuration: Second handler task */\n"
        "#define FUSA_SCHEDULER_HANDLER_USER_TASK1_CONFIG \\\n"
        "    { \\\n"
        "        .task = FUSA_HANDLER_TASK_2, \\\n"
        "        .period = 2000, \\\n"
        "    }"
    )
    assert expected_handler_task2 in content
    
    # Thread tasks with time suffixes and invalid period
    expected_thread_task1 = (
        "/*! Task configuration: First thread task */\n"
        "#define FUSA_SCHEDULER_THREAD_USER_TASK0_CONFIG \\\n"
        "    { \\\n"
        "        .task = FUSA_THREAD_TASK_1, \\\n"
        "        .period = 0, \\\n"
        "    }"
    )
    assert expected_thread_task1 in content
    
    expected_thread_task2 = (
        "/*! Task configuration: Second thread task */\n"
        "#define FUSA_SCHEDULER_THREAD_USER_TASK1_CONFIG \\\n"
        "    { \\\n"
        "        .task = FUSA_THREAD_TASK_2, \\\n"
        "        .period = 0, \\\n"
        "    }"
    )
    assert expected_thread_task2 in content
