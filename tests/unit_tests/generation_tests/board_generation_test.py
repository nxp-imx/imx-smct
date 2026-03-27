#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause

import os
from tempfile import TemporaryDirectory

from smct.configuration.confdata import ConfigurationData
from smct.generation.gen_board import GeneratorBoard
from smct.utils import FormatedInt


def test_board_defines() -> None:
    # Arrange
    directory = TemporaryDirectory()
    generator = GeneratorBoard()
    conf = ConfigurationData()

    uart_instance = 2
    uart_baudrate = 4000000
    i2c_instance = 1
    i2c_baudrate = 4000000
    board_configs = [
        ("CONFIG_NAME", "42"),
        ("CONFIG_MEMORY_SIZE", "1024"),
        ("CONFIG_CPU_FREQ", "800000000"),
        ("CONFIG_ENABLE_CACHE", "1"),
        ("CONFIG_GPIO_COUNT", "32"),
    ]

    for config_name, config_val in board_configs:
        conf.add_board_config(config_name, config_val)
    conf.set_debug_uart_instance(FormatedInt(uart_instance))
    conf.set_debug_uart_baudrate(FormatedInt(uart_baudrate))
    conf.set_pmic_i2c_instance(FormatedInt(i2c_instance))
    conf.set_pmic_i2c_baudrate(FormatedInt(i2c_baudrate))

    # Act
    generator.generate(conf, directory.name)
    file_name = os.path.join(directory.name, "config_board.h")
    content = ""
    with open(file_name, "r") as file:
        content = file.read()

    # Assert
    assert '#include "config_user.h"' in content
    for config_name, config_val in board_configs:
        assert f"#define BOARD_{config_name}  {config_val}" in content
    assert f"#define BOARD_DEBUG_UART_INSTANCE  {uart_instance}U" in content
    assert f"#define BOARD_DEBUG_UART_BAUDRATE  {uart_baudrate}U" in content
    assert f"#define BOARD_I2C_INSTANCE  {i2c_instance}U" in content
    assert f"#define BOARD_I2C_BAUDRATE  {i2c_baudrate}U" in content
