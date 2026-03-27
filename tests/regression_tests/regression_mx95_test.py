#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause

"""Regression tests for MX95 configurations."""

import logging
import os.path
from tempfile import TemporaryDirectory
from typing import Any

import pytest

from smct import utils
from tests.test_utils import execute_binary, execute_cli, get_smct_root
from tests.utils.file_diff import FileDiffer

CONFIGS_FOLDER = os.path.abspath(os.path.join(get_smct_root(), "test_resources", "smoke_configs", "configs"))
REGRESSION_FILES_24_12 = [
    os.path.join("24_12_regression", dir_entry.name)
    for dir_entry in os.scandir(os.path.join(CONFIGS_FOLDER, "24_12_regression"))
    if dir_entry.name.endswith(".cfg")
]
BASE_CFG_FILES = ["mx95evk.cfg", "mx95netc.cfg"]
FILES = BASE_CFG_FILES + REGRESSION_FILES_24_12


@pytest.mark.parametrize("configuration_test_file", FILES)
def test_mx95_cfgs(capsys: Any, configuration_test_file: str) -> None:
    """Test MX95 configuration files against legacy Perl tool output.
    
    Args:
        capsys: Pytest capsys fixture
        configuration_test_file: Configuration file to test
    """
    with TemporaryDirectory() as golden, TemporaryDirectory() as test:
        logging.info("Starting regression test for mx95evk configuration")
        logging.info("Golden sample folder: %s", golden)
        logging.info("Test sample folder: %s", test)
        logging.info("SMCT root: %s", get_smct_root())
        firmware_root_temp = utils.find_firmware_root_dir(os.path.join(get_smct_root(), ".."))
        if firmware_root_temp is None:
            pytest.fail("Could not find firmware root directory")
            return
        firmware_root = os.path.abspath(firmware_root_temp)
        config_tool = os.path.join(firmware_root, "configs", "configtool.pl")
        cfg_file_absolute_path = os.path.join(CONFIGS_FOLDER, configuration_test_file)
        diff_folder = os.path.join(get_smct_root(), "test_results", "test_mx95_cfgs", configuration_test_file.replace(".", "_"))

        logging.info("Diff folder: %s", diff_folder)
        logging.info("Firmware path: %s", firmware_root)
        logging.info("Config tool: %s", config_tool)
        logging.info("CFG file: %s", cfg_file_absolute_path)

        # 1. Run Perl
        execute_binary("perl", [config_tool, "-i", cfg_file_absolute_path, "-o", golden])
        logging.info("Finished legacy tool execution for mx95evk configuration")
        # 2. Run SMCT
        code, _, _ = execute_cli(capsys, ["-c", cfg_file_absolute_path, "-o", test, "--sm_dir", firmware_root])
        assert code == 0
        # 3. Run diff

        differ = FileDiffer(FileDiffer.default_c_files_pattern, golden, test, diff_folder)
        if not differ.check_differences():
            different_files = differ.get_error_files()
            difference = []
            for different_file in different_files:
                difference.append(f"File {different_file} differs:")
                difference.append(differ.get_error(different_file))
            pytest.fail("\n".join(difference))
