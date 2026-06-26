#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause

"""Smoke tests for SMCT CLI functionality."""

import logging
import os.path
from tempfile import TemporaryDirectory
from typing import Any, List

import pytest

from smct import utils
from tests.test_utils import execute_cli, get_smct_root
from tests.utils.file_diff import FileDiffer

SM_FW_CONFIGS_DIR = os.path.join(get_smct_root(), "test_resources", "configs")
SMCT_CONFIGS_DIR = os.path.join(get_smct_root(), "test_resources", "configs_test")

# Configs excluded from smoke tests: crash or are stale artifacts
_EXCLUDED_CONFIGS = {
    "simu.cfg",
    "generated.cfg",
}
# Configs excluded from export/consistency tests: use user-level includes which produce non-dirty
# assignments that are commented out in export (by design for configtool GUI round-trip).
_CONSISTENCY_EXCLUDED = {
    "mx95_trdc_dedup.cfg",
    "trdc_dup_difftest.cfg",
    "mx95evk_fusa.cfg",
}


def _discover_configs(directory: str) -> List[str]:
    """Discover all .cfg files in a flat directory as sorted absolute paths."""
    return sorted(
        os.path.join(directory, f) for f in os.listdir(directory) if f.endswith(".cfg") and os.path.isfile(os.path.join(directory, f))
    )


all_configs = [c for c in _discover_configs(SM_FW_CONFIGS_DIR) + _discover_configs(SMCT_CONFIGS_DIR) if os.path.basename(c) not in _EXCLUDED_CONFIGS]
consistency_configs = [c for c in all_configs if os.path.basename(c) not in _CONSISTENCY_EXCLUDED]


@pytest.mark.parametrize("config", all_configs, ids=[os.path.basename(c) for c in all_configs])
def test_config(capsys: Any, config: str) -> None:
    """Test configuration file processing and consistency.

    Args:
        capsys: Pytest capsys fixture
        config: Absolute path to the configuration file to test
    """
    # Arrange
    with TemporaryDirectory() as dest_first, TemporaryDirectory() as dest_second, TemporaryDirectory() as dest_diff:
        logging.info("Temporary folders: %s, %s, %s", dest_first, dest_second, dest_diff)
        root_dir = os.path.join(get_smct_root(), "test_resources")

        # Act
        args = ["--sm_dir", root_dir, "-c", config, "--store_conf", dest_first, "--store_db", dest_first, "-o", dest_first, "-f"]
        code, _, err = execute_cli(capsys, args)
        assert code == 0
        assert err == ""

        args = ["-i", dest_first, "-o", dest_second, "--store_conf", dest_second, "--store_db", dest_second, "-f"]
        code, _, err = execute_cli(capsys, args)
        assert code == 0
        assert err == ""

        # Assert
        assert os.path.exists(os.path.join(dest_first, "atomic_resources.json"))
        assert os.path.exists(os.path.join(dest_first, "chip_data.json"))
        assert os.path.exists(os.path.join(dest_first, "macro_resources.json"))
        assert os.path.exists(os.path.join(dest_first, "user_configuration.json"))
        files_first = utils.get_all_files_in_folder(dest_first)
        files_second = utils.get_all_files_in_folder(dest_second)
        assert files_first == files_second
        differ = FileDiffer(FileDiffer.default_c_files_pattern + ";**/*.json", dest_first, dest_second, dest_diff)
        if not differ.check_differences():
            pytest.fail(differ.get_string_result())


@pytest.mark.parametrize("config", consistency_configs, ids=[os.path.basename(c) for c in consistency_configs])
def test_exported_config(capsys: Any, config: str) -> None:
    """Test exported configuration file consistency.

    Args:
        capsys: Pytest capsys fixture
        config: Absolute path to the configuration file to test
    """
    # Arrange
    with TemporaryDirectory() as dest_first, TemporaryDirectory() as dest_second, TemporaryDirectory() as dest_diff:
        logging.info("Temporary folders: %s, %s, %s", dest_first, dest_second, dest_diff)
        root_dir = os.path.join(get_smct_root(), "test_resources")
        config_name = os.path.basename(config)

        # Act
        dest_first_cfg = os.path.join(dest_first, config_name)
        args = [
            "--sm_dir",
            root_dir,
            "-c",
            config,
            "--store_conf",
            dest_first,
            "--store_db",
            dest_first,
            "--store_cfg_file",
            dest_first_cfg,
            "-o",
            dest_first,
            "-f",
        ]
        code, _, err = execute_cli(capsys, args)
        assert code == 0
        assert err == ""

        dest_second_cfg = os.path.join(dest_second, config_name)
        args = ["-c", dest_first_cfg, "-o", dest_second, "--store_conf", dest_second, "--store_db", dest_second, "--store_cfg_file", dest_second_cfg, "-f"]
        code, _, err = execute_cli(capsys, args)
        assert code == 0
        assert err == ""

        # Assert
        assert os.path.exists(os.path.join(dest_first, "atomic_resources.json"))
        assert os.path.exists(os.path.join(dest_first, "chip_data.json"))
        assert os.path.exists(os.path.join(dest_first, "macro_resources.json"))
        assert os.path.exists(os.path.join(dest_first, "user_configuration.json"))
        files_first = utils.get_all_files_in_folder(dest_first)
        files_second = utils.get_all_files_in_folder(dest_second)
        assert files_first == files_second
        differ = FileDiffer(FileDiffer.default_c_files_pattern + ";**/*.json", dest_first, dest_second, dest_diff)
        if not differ.check_differences():
            pytest.fail(differ.get_string_result())


@pytest.mark.parametrize("config", consistency_configs, ids=[os.path.basename(c) for c in consistency_configs])
def test_consistency(capsys: Any, config: str) -> None:
    """Test configuration consistency across multiple processing cycles.

    Args:
        capsys: Pytest capsys fixture
        config: Absolute path to the configuration file to test
    """
    with (
        TemporaryDirectory() as output,
        TemporaryDirectory() as output_ext,
        TemporaryDirectory() as output_import,
        TemporaryDirectory() as output_ext_import,
        TemporaryDirectory() as tmp_diff,
    ):
        logging.info("Temporary folders: %s, %s, %s, %s", output, output_ext, output_import, output_ext_import)
        root_dir = os.path.join(get_smct_root(), "test_resources")
        config_name = os.path.basename(config)

        # smct.py -c %CFG% -o output -f --store_db output --store_conf output --store_log output --store_cfg_file output/%CFG%
        output_path_cfg = os.path.join(output, config_name)
        args = [
            "--sm_dir",
            root_dir,
            "-c",
            config,
            "-o",
            output,
            "-f",
            "--store_db",
            output,
            "--store_log",
            output,
            "--store_conf",
            output,
            "--store_cfg_file",
            output_path_cfg,
        ]
        code, _, err = execute_cli(capsys, args)
        assert code == 0
        assert err == ""

        # smct.py -c output/%CFG% -o output_ext -f --store_db output_ext --store_conf output_ext --store_log output_ext
        args = [
            "--sm_dir",
            root_dir,
            "-c",
            output_path_cfg,
            "-o",
            output_ext,
            "-f",
            "--store_db",
            output_ext,
            "--store_conf",
            output_ext,
            "--store_log",
            output_ext,
        ]
        code, _, err = execute_cli(capsys, args)
        assert code == 0
        assert err == ""

        # smct.py -i output -f -o output_import --store_log output_import
        args = ["--sm_dir", root_dir, "-i", output, "-f", "-o", output_import, "--store_log", output_import]
        code, _, err = execute_cli(capsys, args)
        assert code == 0
        assert err == ""

        # smct.py -i output_ext -f -o output_ext_import --store_log output_ext_import
        args = ["--sm_dir", root_dir, "-i", output_ext, "-f", "-o", output_ext_import, "--store_log", output_ext_import]
        code, _, err = execute_cli(capsys, args)
        assert code == 0
        assert err == ""

        # Run the diff tool to all directory files, output, output_ext and output_ext_import - it should be the same
        compared_jsons = ["atomic_resources.json", "chip_data.json", "macro_resources.json", "user_configuration.json"]
        files_pattern = FileDiffer.default_c_files_pattern + ";" + (";".join(["**/" + x for x in compared_jsons]))
        differ = FileDiffer(files_pattern, output, output_ext, tmp_diff)
        if not differ.check_differences():
            pytest.fail(differ.get_string_result())
        differ = FileDiffer(files_pattern, output_ext, output_ext_import, tmp_diff)
        if not differ.check_differences():
            pytest.fail(differ.get_string_result())
        differ = FileDiffer(files_pattern, output, output_ext_import, tmp_diff)
        if not differ.check_differences():
            pytest.fail(differ.get_string_result())
