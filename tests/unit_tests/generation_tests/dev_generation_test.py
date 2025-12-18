#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
import os
from tempfile import TemporaryDirectory

from smct.configuration.confdata import ConfigurationData
from smct.generation.gen_dev import GeneratorDev
from smct.owners.owner_lm import LM
from smct.parsers.resource_parser import ResourceParser
from smct.resources.res_api import ApiResource
from tests import test_utils

def _generate_and_read(conf: ConfigurationData, generator: GeneratorDev, directory: TemporaryDirectory) -> str:
    generator.generate(conf, directory.name)
    file_name = os.path.join(directory.name, "config_dev.h")
    content = ""
    with open(file_name, "r") as file:
        content = file.read()
    return content


def test_dev_structures_empty() -> None:
    """Test DEV generation with empty configuration data"""
    # Arrange
    directory = TemporaryDirectory()
    generator = GeneratorDev()
    conf = ConfigurationData()

    # Act
    content = _generate_and_read(conf, generator, directory)

    # Assert
    empty_content = ('#define SM_DEV_CONFIG_DATA \\\n' +
                     '    { \\\n' +
                     '    }\n')
    assert '#include "config_user.h"' in content
    assert empty_content in content
    assert ".cpuSemaAddr" not in content


def test_dev_structures_single() -> None:
    """Test DEV generation with a single CPU resource configuration"""
    # Arrange
    directory = TemporaryDirectory()
    generator = GeneratorDev()
    conf = ConfigurationData()
    test_utils.set_up()
    lm = LM("id", 0, "name", None,
            None, None, None, None, True)
    conf.add_lm(lm)
    res_name = 'CPU_M33P'
    sema_val_hex = '0x442313F8'
    res = ApiResource({'api': 'CPU', 'cat': 'DEV', 'name': res_name, 'type': 'API'})
    lm.assign_resource(res, ["api=all", f"sema={sema_val_hex}"])

    # Act
    content = _generate_and_read(conf, generator, directory)

    # Assert
    empty_content = ('#define SM_DEV_CONFIG_DATA \\\n' +
                     '    { \\\n' +
                     '    }\n')
    assert empty_content not in content
    assert f".cpuSemaAddr[DEV_SM_{res_name}] = {sema_val_hex}U" in content


def test_dev_structures_only_cpu() -> None:
    """Test DEV generation with multiple CPU resources and filtering of non-CPU resources"""
    # Arrange
    directory = TemporaryDirectory()
    generator = GeneratorDev()
    conf = ConfigurationData()
    test_utils.set_up()
    lm = LM("id", 0, "name", None,
            None, None, None, None, True)
    conf.add_lm(lm)

    cpu1_res_name = 'CPU_M33P'
    cpu1_sema_val_hex = '0x442313F8'
    res = ApiResource({'api': 'CPU', 'cat': 'DEV', 'name': cpu1_res_name, 'type': 'API'})
    lm.assign_resource(res, ["api=all", f"sema={cpu1_sema_val_hex}"])
    cpu2_res_name = 'CPU_A55P'
    cpu2_sema_val_hex = '0x6292A8FC'
    res = ApiResource({'api': 'CPU', 'cat': 'DEV', 'name': cpu2_res_name, 'type': 'API'})
    lm.assign_resource(res, ["api=all", f"sema={cpu2_sema_val_hex}"])
    non_cpu_res_name = 'GPIO1'
    non_cpu_sema_val_hex = '0x6292A8FC'
    res = ApiResource({'api': 'API', 'cat': 'DEV', 'name': non_cpu_res_name, 'type': 'API'})
    lm.assign_resource(res, ["api=all", f"sema={non_cpu_sema_val_hex}"])

    # Act
    content = _generate_and_read(conf, generator, directory)

    # Assert
    empty_content = ('#define SM_DEV_CONFIG_DATA \\\n' +
                     '    { \\\n' +
                     '    }\n')
    assert empty_content not in content
    assert f".cpuSemaAddr[DEV_SM_{cpu1_res_name}] = {cpu1_sema_val_hex}U" in content
    assert f".cpuSemaAddr[DEV_SM_{cpu2_res_name}] = {cpu2_sema_val_hex}U" in content
    assert f".cpuSemaAddr[DEV_SM_{non_cpu_res_name}] = {non_cpu_sema_val_hex}U" not in content
