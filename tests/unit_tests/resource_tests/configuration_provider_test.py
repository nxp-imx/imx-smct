#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause

from smct.configuration.confdata import ConfigurationData
from smct.configuration.configuration_provider import ConfigurationProvider


def test_identity() -> None:
    instance = ConfigurationProvider.get_configuration()
    assert isinstance(instance, ConfigurationData)
    instance2 = ConfigurationProvider.get_configuration()
    assert instance == instance2


def test_clear_configuration() -> None:
    configuration = ConfigurationProvider.get_configuration()
    configuration.set_config_name("test_config_name")
    configuration.set_doxygen_name_descr("test_name", "test_description")
    assert configuration.get_config_name() == "test_config_name"
    assert configuration.get_doxygen_name() == "test_name"
    assert configuration.get_doxygen_description() == "test_description"
    configuration = ConfigurationProvider.get_configuration()
    assert configuration.get_config_name() == "test_config_name"
    assert configuration.get_doxygen_name() == "test_name"
    assert configuration.get_doxygen_description() == "test_description"
    ConfigurationProvider.clear_configuration()
    configuration = ConfigurationProvider.get_configuration()
    assert configuration.get_config_name() != "test_config_name"
    assert configuration.get_doxygen_name() != "test_name"
    assert configuration.get_doxygen_description() != "test_description"
