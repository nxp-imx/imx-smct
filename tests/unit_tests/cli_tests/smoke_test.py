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
from typing import Any

import pytest

from smct import utils
from tests.test_utils import execute_cli, get_smct_root
from tests.utils.file_diff import FileDiffer

configs = ["mx95alt.cfg", "mx95netc.cfg", "mx95evk.cfg", "mx952alt.cfg", "mx952evk.cfg", "mx94alt.cfg", "mx94netc.cfg", "mx94evk.cfg", "generated.cfg"]
configs_consistency = ["mx95alt.cfg", "mx95netc.cfg", "mx95evk.cfg", "mx952alt.cfg", "mx952evk.cfg", "mx94alt.cfg", "mx94netc.cfg", "mx94evk.cfg"]


@pytest.mark.parametrize("config", configs)
def test_config(capsys: Any, config: str) -> None:
    """Test configuration file processing and consistency.

    Args:
        capsys: Pytest capsys fixture
        config: Configuration file name to test
    """
    # Arrange
    with TemporaryDirectory() as dest_first, TemporaryDirectory() as dest_second, TemporaryDirectory() as dest_diff:
        logging.info("Temporary folders: %s, %s, %s", dest_first, dest_second, dest_diff)
        root_dir = os.path.join(get_smct_root(), "test_resources", "smoke_configs")
        config_path = os.path.join(root_dir, "configs", config)

        # Act
        args = ["--sm_dir", root_dir, "-c", config_path, "--store_conf", dest_first, "--store_db", dest_first, "-o", dest_first, "-f"]
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


@pytest.mark.parametrize("config", configs_consistency)
def test_exported_config(capsys: Any, config: str) -> None:
    """Test exported configuration file consistency.

    Args:
        capsys: Pytest capsys fixture
        config: Configuration file name to test
    """
    # Arrange
    with TemporaryDirectory() as dest_first, TemporaryDirectory() as dest_second, TemporaryDirectory() as dest_diff:
        logging.info("Temporary folders: %s, %s, %s", dest_first, dest_second, dest_diff)
        root_dir = os.path.join(get_smct_root(), "test_resources", "smoke_configs")
        config_path = os.path.join(root_dir, "configs", config)

        # Act
        dest_first_cfg = os.path.join(dest_first, config)
        args = [
            "--sm_dir",
            root_dir,
            "-c",
            config_path,
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

        dest_second_cfg = os.path.join(dest_second, config)
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


@pytest.mark.parametrize("config", configs_consistency)
def test_consistency(capsys: Any, config: str) -> None:
    """Test configuration consistency across multiple processing cycles.

    Args:
        capsys: Pytest capsys fixture
        config: Configuration file name to test
    """
    with (
        TemporaryDirectory() as output,
        TemporaryDirectory() as output_ext,
        TemporaryDirectory() as output_import,
        TemporaryDirectory() as output_ext_import,
        TemporaryDirectory() as tmp_diff,
    ):
        logging.info("Temporary folders: %s, %s, %s, %s", output, output_ext, output_import, output_ext_import)
        root_dir = os.path.join(get_smct_root(), "test_resources", "smoke_configs")
        config_path = os.path.join(root_dir, "configs", config)

        # smct.py -c %CFG% -o output -f --store_db output --store_conf output --store_log output --store_cfg_file output/%CFG%
        output_path_cfg = os.path.join(output, config)
        args = [
            "--sm_dir",
            root_dir,
            "-c",
            config_path,
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
