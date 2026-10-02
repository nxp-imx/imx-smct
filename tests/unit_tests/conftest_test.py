#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause

"""Tests for tests/conftest.py log-merge helper."""

import os
import pathlib

from tests.conftest import _merge_worker_logs


class TestMergeWorkerLogs:
    """Unit tests for _merge_worker_logs."""

    def test_merge_two_workers_in_order(self, tmp_path: pathlib.Path) -> None:
        """Per-worker files are concatenated in worker-name order."""
        base = str(tmp_path / "pytest.log")
        (tmp_path / "pytest_gw0.log").write_text("line-from-gw0\n", encoding="utf-8")
        (tmp_path / "pytest_gw1.log").write_text("line-from-gw1\n", encoding="utf-8")

        _merge_worker_logs(base)

        merged = (tmp_path / "pytest.log").read_text(encoding="utf-8")
        assert merged == "line-from-gw0\nline-from-gw1\n"

    def test_merge_removes_per_worker_files(self, tmp_path: pathlib.Path) -> None:
        """After merge the per-worker files are cleaned up."""
        base = str(tmp_path / "pytest.log")
        (tmp_path / "pytest_gw0.log").write_text("data\n", encoding="utf-8")

        _merge_worker_logs(base)

        assert not (tmp_path / "pytest_gw0.log").exists()

    def test_no_worker_files_is_noop(self, tmp_path: pathlib.Path) -> None:
        """When no per-worker files exist nothing is created."""
        base = str(tmp_path / "pytest.log")

        _merge_worker_logs(base)

        assert not (tmp_path / "pytest.log").exists()

    def test_merge_creates_output_directory(self, tmp_path: pathlib.Path) -> None:
        """If the target directory does not exist it is created."""
        nested = tmp_path / "sub" / "dir"
        base = str(nested / "pytest.log")
        nested.mkdir(parents=True)
        (nested / "pytest_gw0.log").write_text("ok\n", encoding="utf-8")

        _merge_worker_logs(base)

        assert (nested / "pytest.log").read_text(encoding="utf-8") == "ok\n"

    def test_merge_skips_unreadable_file(self, tmp_path: pathlib.Path) -> None:
        """An unreadable worker file is skipped without raising."""
        base = str(tmp_path / "pytest.log")
        gw0 = tmp_path / "pytest_gw0.log"
        gw1 = tmp_path / "pytest_gw1.log"
        gw0.write_text("gw0-data\n", encoding="utf-8")
        gw1.write_text("gw1-data\n", encoding="utf-8")

        # Make gw0 unreadable (on Windows, remove read permission via os.chmod)
        # On some Windows CIs os.chmod may not actually restrict reading;
        # simulate by replacing with a directory of the same name (open() will fail).
        os.remove(str(gw0))
        os.mkdir(str(gw0))  # opening a directory as a file raises OSError

        _merge_worker_logs(base)

        merged = (tmp_path / "pytest.log").read_text(encoding="utf-8")
        assert "gw1-data" in merged
