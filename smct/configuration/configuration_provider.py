#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause

"""Module with user configuration provider"""

from smct.configuration.confdata import ConfigurationData


class ConfigurationProvider:
    """Provider of the configuration singleton"""

    _singleton: ConfigurationData = ConfigurationData()

    @classmethod
    def get_configuration(cls) -> ConfigurationData:
        """Returns singleton of the configuration object

        Returns:
            ConfigurationData: The singleton configuration object
        """
        return cls._singleton

    @classmethod
    def clear_configuration(cls) -> None:
        """Clears the configuration singleton by creating new one

        Returns:
            None
        """
        conf = ConfigurationData()
        conf.set_sm_fw_root_directory(conf.get_sm_fw_root_directory())
        cls._singleton = conf
