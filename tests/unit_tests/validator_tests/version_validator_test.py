#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause

"""Unit tests for VersionValidator and _validate_sm_fw_compatibility."""

import logging
import pathlib
from unittest.mock import Mock, patch

import pytest

from smct.configuration.confdata import ConfigurationData
from smct.configuration.configuration_provider import ConfigurationProvider
from smct.model.chip_model_provider import ChipModelProvider
from smct.resources.resource_database_provider import ResourceDatabaseProvider
from smct.validation.validators.version_validator import VersionValidator


@pytest.fixture(autouse=True)
def clear_providers() -> None:
    """Reset singleton providers around each test."""
    ConfigurationProvider.clear_configuration()
    ResourceDatabaseProvider.clear_database()
    ChipModelProvider.clear_model()


def _make_conf(tmp_path: pathlib.Path) -> Mock:
    """Return a mock ConfigurationData whose sm_fw_root_directory is tmp_path."""
    mock_conf = Mock(spec=ConfigurationData)
    mock_conf.get_sm_fw_root_directory.return_value = str(tmp_path)
    return mock_conf


def _write_configtool_pl(tmp_path: pathlib.Path, content: str) -> pathlib.Path:
    """Create tmp_path/configs/configtool.pl with the given content and return its path."""
    configs_dir = tmp_path / "configs"
    configs_dir.mkdir(parents=True, exist_ok=True)
    pl_file = configs_dir / "configtool.pl"
    pl_file.write_text(content, encoding="utf-8")
    return pl_file


_PRODUCT_INFO_PATCH = "smct.validation.validators.version_validator.ProductInfo"


class TestVersionValidator:
    """Tests for VersionValidator (and the underlying _validate_sm_fw_compatibility function)."""

    def test_validate_match_returns_empty_list(self, tmp_path: pathlib.Path) -> None:
        """validate() returns [] when the file version matches the tool version."""
        _write_configtool_pl(tmp_path, "my $configVer = 5\n")
        mock_conf = _make_conf(tmp_path)
        with patch(_PRODUCT_INFO_PATCH) as mock_pi:
            mock_pi.get_sm_fw_compatible_version.return_value = 5
            validator = VersionValidator()
            result = validator.validate(mock_conf)
        assert not result

    def test_validate_mismatch_returns_one_error_entry(self, tmp_path: pathlib.Path) -> None:
        """validate() returns one ERROR ValidationEntry when versions differ."""
        _write_configtool_pl(tmp_path, "my $configVer = 4\n")
        mock_conf = _make_conf(tmp_path)
        with patch(_PRODUCT_INFO_PATCH) as mock_pi:
            mock_pi.get_sm_fw_compatible_version.return_value = 5
            validator = VersionValidator()
            result = validator.validate(mock_conf)
        assert len(result) == 1
        assert result[0].get_level() == logging.ERROR

    def test_validate_mismatch_message_contains_both_versions(self, tmp_path: pathlib.Path) -> None:
        """validate() mismatch error message mentions both the file version and tool version."""
        _write_configtool_pl(tmp_path, "my $configVer = 4\n")
        mock_conf = _make_conf(tmp_path)
        with patch(_PRODUCT_INFO_PATCH) as mock_pi:
            mock_pi.get_sm_fw_compatible_version.return_value = 5
            validator = VersionValidator()
            result = validator.validate(mock_conf)
        msg = result[0].get_error_message()
        assert "4" in msg
        assert "5" in msg

    def test_validate_mismatch_source_is_file_path(self, tmp_path: pathlib.Path) -> None:
        """validate() mismatch ValidationEntry source is the configtool.pl path."""
        pl_file = _write_configtool_pl(tmp_path, "my $configVer = 3\n")
        mock_conf = _make_conf(tmp_path)
        with patch(_PRODUCT_INFO_PATCH) as mock_pi:
            mock_pi.get_sm_fw_compatible_version.return_value = 5
            validator = VersionValidator()
            result = validator.validate(mock_conf)
        assert result[0].get_source() == str(pl_file)

    def test_validate_missing_file_returns_empty_list(self, tmp_path: pathlib.Path, caplog: pytest.LogCaptureFixture) -> None:
        """validate() returns [] and logs INFO when configtool.pl is not found."""
        mock_conf = _make_conf(tmp_path)
        with patch(_PRODUCT_INFO_PATCH) as mock_pi:
            mock_pi.get_sm_fw_compatible_version.return_value = 5
            validator = VersionValidator()
            with caplog.at_level(logging.INFO):
                result = validator.validate(mock_conf)
        assert not result
        assert any(r.levelno == logging.INFO for r in caplog.records)

    def test_validate_missing_file_logs_not_found_message(self, tmp_path: pathlib.Path, caplog: pytest.LogCaptureFixture) -> None:
        """validate() logs an INFO message referencing 'configtool.pl' when file is absent."""
        mock_conf = _make_conf(tmp_path)
        with patch(_PRODUCT_INFO_PATCH) as mock_pi:
            mock_pi.get_sm_fw_compatible_version.return_value = 5
            validator = VersionValidator()
            with caplog.at_level(logging.INFO):
                validator.validate(mock_conf)
        info_messages = [r.getMessage() for r in caplog.records if r.levelno == logging.INFO]
        assert any("configtool.pl" in msg or "not found" in msg for msg in info_messages)

    def test_validate_missing_version_line_returns_empty_list(self, tmp_path: pathlib.Path, caplog: pytest.LogCaptureFixture) -> None:
        """validate() returns [] and logs ERROR when configtool.pl has no configVer line."""
        _write_configtool_pl(tmp_path, "# no version here\nsome other content\n")
        mock_conf = _make_conf(tmp_path)
        with patch(_PRODUCT_INFO_PATCH) as mock_pi:
            mock_pi.get_sm_fw_compatible_version.return_value = 5
            validator = VersionValidator()
            with caplog.at_level(logging.DEBUG):
                result = validator.validate(mock_conf)
        assert not result
        assert any(r.levelno == logging.ERROR for r in caplog.records)

    def test_validate_missing_version_line_logs_error_message(self, tmp_path: pathlib.Path, caplog: pytest.LogCaptureFixture) -> None:
        """validate() ERROR log mentions 'Missing SM FW configuration version' when line absent."""
        _write_configtool_pl(tmp_path, "# empty config file\n")
        mock_conf = _make_conf(tmp_path)
        with patch(_PRODUCT_INFO_PATCH) as mock_pi:
            mock_pi.get_sm_fw_compatible_version.return_value = 5
            validator = VersionValidator()
            with caplog.at_level(logging.DEBUG):
                validator.validate(mock_conf)
        error_messages = [r.getMessage() for r in caplog.records if r.levelno == logging.ERROR]
        assert any("Missing SM FW configuration version" in msg for msg in error_messages)

    def test_validate_multiple_version_lines_returns_empty_list(self, tmp_path: pathlib.Path, caplog: pytest.LogCaptureFixture) -> None:
        """validate() returns [] and logs ERROR when more than one configVer line exists."""
        _write_configtool_pl(tmp_path, "my $configVer = 5\nmy $configVer = 5\n")
        mock_conf = _make_conf(tmp_path)
        with patch(_PRODUCT_INFO_PATCH) as mock_pi:
            mock_pi.get_sm_fw_compatible_version.return_value = 5
            validator = VersionValidator()
            with caplog.at_level(logging.DEBUG):
                result = validator.validate(mock_conf)
        assert not result
        assert any(r.levelno == logging.ERROR for r in caplog.records)

    def test_validate_multiple_version_lines_logs_more_than_one_message(self, tmp_path: pathlib.Path, caplog: pytest.LogCaptureFixture) -> None:
        """validate() ERROR log mentions 'more than one line' when duplicate configVer lines exist."""
        _write_configtool_pl(tmp_path, "my $configVer = 5\nmy $configVer = 6\n")
        mock_conf = _make_conf(tmp_path)
        with patch(_PRODUCT_INFO_PATCH) as mock_pi:
            mock_pi.get_sm_fw_compatible_version.return_value = 5
            validator = VersionValidator()
            with caplog.at_level(logging.DEBUG):
                validator.validate(mock_conf)
        error_messages = [r.getMessage() for r in caplog.records if r.levelno == logging.ERROR]
        assert any("more than one line" in msg for msg in error_messages)
