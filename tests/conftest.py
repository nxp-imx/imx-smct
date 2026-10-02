#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause

"""Root pytest configuration shared by all test suites."""

import glob
import os
from typing import List

import pytest


def _merge_worker_logs(log_file: str) -> None:
    """Concatenate per-worker log files back into the base log_file path.

    Under pytest-xdist each worker writes to its own file (e.g.
    ``reports/pytest_gw0.log``, ``reports/pytest_gw1.log``).  This helper
    merges them in worker-name order into the canonical base path so that
    CI artifact collection can always read a single, predictable file.

    After a successful merge the per-worker files are removed.  If no
    per-worker files exist (e.g. xdist was disabled with ``-n 0``) this
    function is a no-op.
    """
    root, ext = os.path.splitext(log_file)
    pattern = f"{root}_gw*{ext}"
    worker_files: List[str] = sorted(glob.glob(pattern))
    if not worker_files:
        return

    os.makedirs(os.path.dirname(log_file) or ".", exist_ok=True)
    with open(log_file, "w", encoding="utf-8") as merged:
        for wf in worker_files:
            try:
                with open(wf, "r", encoding="utf-8") as src:
                    merged.write(src.read())
            except OSError:
                # If a worker file cannot be read (locked/missing), skip it
                # rather than crashing the session teardown.
                pass

    # Clean up per-worker files so the artifact directory is tidy.
    for wf in worker_files:
        try:
            os.remove(wf)
        except OSError:
            pass


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config: pytest.Config) -> None:
    """Give each xdist worker its own log file so file logs are not clobbered.

    The ``log_file`` option in ``pytest.ini`` is a single path. Under
    ``pytest-xdist`` every worker opens that path in write mode, so the workers
    overwrite each other and the artifact ends up with only a fraction of the
    log records. Redirect each worker to a per-worker file to keep the full log.

    At session end the controller merges the per-worker files back into the
    base path (see ``pytest_sessionfinish`` below).
    """
    worker_id = os.environ.get("PYTEST_XDIST_WORKER")
    log_file = config.getini("log_file")
    if worker_id and log_file:
        root, ext = os.path.splitext(log_file)
        config.option.log_file = f"{root}_{worker_id}{ext}"


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Merge per-worker log files into the single base log_file path.

    Runs only on the xdist controller (or in a non-xdist run where no
    per-worker files exist).  Workers are identified by the presence of
    the PYTEST_XDIST_WORKER env var -- they skip this hook entirely.
    """
    # Workers must not attempt the merge; only the controller (or a
    # non-xdist main process) should.
    if os.environ.get("PYTEST_XDIST_WORKER"):
        return

    log_file = session.config.getini("log_file")
    if log_file:
        _merge_worker_logs(str(log_file))
