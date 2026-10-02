#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Unit tests for smct.model.model_chip ChipModel and ChipModelImx9."""

from typing import Any, Dict, Iterator
from unittest.mock import MagicMock, patch

import pytest

from smct.model.model_bctrl import BctrlModel
from smct.model.model_chip import ChipModel, ChipModelImx9
from smct.model.model_trdc import TrdcModel
from tests import test_utils


@pytest.fixture(autouse=True)
def trdc_permission_types() -> Iterator[None]:
    """Provide minimal permission_types so TrdcModel construction works."""
    with test_utils.restore_trdc_class_attrs(permission_types={"none": 0, "all": 0x7777}):
        yield


class TestChipModel:
    """Tests for ChipModel base class."""

    def test_add_mix_and_get_mixes(self) -> None:
        """add_mix appends a mix; get_mixes returns the full list."""
        chip = ChipModel()

        chip.add_mix("MIX_A")
        chip.add_mix("MIX_B")

        mixes = chip.get_mixes()
        assert mixes == ["MIX_A", "MIX_B"]

    def test_get_mixes_initially_empty(self) -> None:
        """A fresh ChipModel has no mixes."""
        chip = ChipModel()

        assert not chip.get_mixes()


class TestChipModelImx9:
    """Tests for ChipModelImx9."""

    def test_get_trdc_creates_when_create_if_needed_true(self) -> None:
        """get_trdc with create_if_needed=True creates and returns a TrdcModel."""
        chip = ChipModelImx9()

        trdc = chip.get_trdc("A", create_if_needed=True)

        assert trdc is not None
        assert isinstance(trdc, TrdcModel)
        assert trdc.get_id() == "A"

    def test_get_trdc_returns_same_instance(self) -> None:
        """get_trdc returns the same TrdcModel on repeated calls."""
        chip = ChipModelImx9()
        first = chip.get_trdc("A", create_if_needed=True)
        second = chip.get_trdc("A", create_if_needed=True)

        assert first is second

    def test_get_trdc_returns_none_when_not_found_and_not_creating(self) -> None:
        """get_trdc with create_if_needed=False returns None for unknown letter."""
        chip = ChipModelImx9()

        result = chip.get_trdc("Z", create_if_needed=False)

        assert result is None

    def test_get_trdc_invalid_letter_logs_error_and_returns_none(self, caplog: pytest.LogCaptureFixture) -> None:
        """get_trdc logs an error and returns None for a multi-char id_letter."""
        chip = ChipModelImx9()

        result = chip.get_trdc("AB", create_if_needed=True)

        assert result is None
        assert "AB" in caplog.text

    def test_get_all_trdcs_empty_initially(self) -> None:
        """get_all_trdcs returns an empty list on a fresh instance."""
        chip = ChipModelImx9()

        assert chip.get_all_trdcs() == []

    def test_get_all_trdcs_returns_created_trdcs(self) -> None:
        """get_all_trdcs returns all created TrdcModel instances."""
        chip = ChipModelImx9()
        chip.get_trdc("A", create_if_needed=True)
        chip.get_trdc("B", create_if_needed=True)

        trdcs = chip.get_all_trdcs()

        assert len(trdcs) == 2
        ids = {t.get_id() for t in trdcs}
        assert ids == {"A", "B"}

    def test_get_bctrl_creates_when_create_if_needed_true(self) -> None:
        """get_bctrl with create_if_needed=True creates and returns a BctrlModel."""
        chip = ChipModelImx9()

        bctrl = chip.get_bctrl("A", create_if_needed=True)

        assert bctrl is not None
        assert isinstance(bctrl, BctrlModel)
        assert bctrl.get_letter_id() == "A"

    def test_get_bctrl_returns_same_instance(self) -> None:
        """get_bctrl returns the same BctrlModel on repeated calls."""
        chip = ChipModelImx9()
        first = chip.get_bctrl("A", create_if_needed=True)
        second = chip.get_bctrl("A", create_if_needed=True)

        assert first is second

    def test_get_bctrl_returns_none_when_not_found_and_not_creating(self) -> None:
        """get_bctrl with create_if_needed=False returns None for unknown letter."""
        chip = ChipModelImx9()

        result = chip.get_bctrl("Z", create_if_needed=False)

        assert result is None

    def test_get_bctrl_invalid_letter_logs_error_and_returns_none(self, caplog: pytest.LogCaptureFixture) -> None:
        """get_bctrl logs an error and returns None for multi-char id_letter."""
        chip = ChipModelImx9()

        result = chip.get_bctrl("AB", create_if_needed=True)

        assert result is None
        assert "AB" in caplog.text

    def test_get_all_bctrls_empty_initially(self) -> None:
        """get_all_bctrls returns an empty list on a fresh instance."""
        chip = ChipModelImx9()

        assert chip.get_all_bctrls() == []

    def test_get_all_bctrls_returns_created_bctrls(self) -> None:
        """get_all_bctrls returns all created BctrlModel instances."""
        chip = ChipModelImx9()
        chip.get_bctrl("A", create_if_needed=True)
        chip.get_bctrl("B", create_if_needed=True)

        bctrls = chip.get_all_bctrls()

        assert len(bctrls) == 2
        ids = {b.get_letter_id() for b in bctrls}
        assert ids == {"A", "B"}

    def test_get_raw_json_has_required_top_level_keys(self) -> None:
        """get_raw_json contains 'TRDCs', 'BCTRLs', and 'Mixes' keys."""
        chip = ChipModelImx9()

        raw = chip.get_raw_json()

        assert isinstance(raw, dict)
        assert "TRDCs" in raw  # type: ignore[operator]
        assert "BCTRLs" in raw  # type: ignore[operator]
        assert "Mixes" in raw  # type: ignore[operator]

    def test_get_raw_json_includes_mixes(self) -> None:
        """get_raw_json Mixes list matches added mixes."""
        chip = ChipModelImx9()
        chip.add_mix("MIX_A")

        raw = chip.get_raw_json()

        assert raw["Mixes"] == ["MIX_A"]  # type: ignore[index]

    def test_load_from_json_missing_file_returns_false(self, caplog: pytest.LogCaptureFixture) -> None:
        """load_from_json returns False and logs an error when file does not exist."""
        chip = ChipModelImx9()

        result = chip.load_from_json("/nonexistent/path/that/does/not/exist")

        assert result is False
        assert "not found" in caplog.text.lower() or "File not found" in caplog.text

    def test_load_from_json_parses_chip_dict(self) -> None:
        """load_from_json returns True and populates TRDCs/BCTRLs/Mixes from a valid dict."""
        chip_data: Dict[str, Any] = {
            "TRDCs": [
                {
                    "trdc": "A",
                    "name": "TRDC_A",
                    "ndid": 3,
                    "nmstr": 5,
                    "nmbc": 1,
                    "nmrc": 1,
                    "kpaen": 1,
                    "sidsz": 6,
                    "MBCs": [{"mbc": "0", "mem": [{}]}],
                    "MRCs": [{"mrc": "0", "nrgns": 8, "memory_region_offset": 14}],
                }
            ],
            "BCTRLs": [
                {
                    "bctrl": "A",
                    "name": "BCTRL_A",
                    "regs": {"IPG_DEBUG": [{"cpu": "CPU_M33P", "offset": [0x100]}]},
                }
            ],
            "Mixes": ["MIX_WAKEUP", "MIX_DISPLAY"],
        }

        chip = ChipModelImx9()
        with (
            patch("os.path.exists", return_value=True),
            patch("builtins.open", MagicMock()),
            patch("json.load", return_value=chip_data),
            patch("smct.model.model_chip.validate_json"),
        ):
            result = chip.load_from_json("/fake/path")

        assert result is True
        assert len(chip.get_all_trdcs()) == 1
        assert len(chip.get_all_bctrls()) == 1
        assert "MIX_WAKEUP" in chip.get_mixes()
        assert "MIX_DISPLAY" in chip.get_mixes()

    def test_load_from_json_returns_false_when_json_load_returns_none(self) -> None:
        """load_from_json returns False when json.load yields None."""
        chip = ChipModelImx9()

        with (
            patch("os.path.exists", return_value=True),
            patch("builtins.open", MagicMock()),
            patch("json.load", return_value=None),
            patch("smct.model.model_chip.validate_json"),
        ):
            result = chip.load_from_json("/fake/path")

        assert result is False

    def test_load_from_json_logs_warning_for_invalid_trdc_letter(self, caplog: pytest.LogCaptureFixture) -> None:
        """load_from_json logs a warning when a TRDC entry has a multi-char letter."""
        chip_data: Dict[str, Any] = {
            "TRDCs": [
                {
                    "trdc": "AB",  # multi-char triggers get_trdc to return None
                    "name": "TRDC_AB",
                    "ndid": 3,
                    "nmstr": 5,
                    "nmbc": 1,
                    "nmrc": 1,
                    "kpaen": 1,
                    "sidsz": 6,
                    "MBCs": [],
                    "MRCs": [],
                }
            ],
            "BCTRLs": [],
            "Mixes": [],
        }
        chip = ChipModelImx9()

        with (
            patch("os.path.exists", return_value=True),
            patch("builtins.open", MagicMock()),
            patch("json.load", return_value=chip_data),
            patch("smct.model.model_chip.validate_json"),
        ):
            result = chip.load_from_json("/fake/path")

        assert result is True
        assert len(chip.get_all_trdcs()) == 0
        assert "not known" in caplog.text

    def test_load_from_json_logs_warning_for_invalid_bctrl_letter(self, caplog: pytest.LogCaptureFixture) -> None:
        """load_from_json logs a warning when a BCTRL entry has a multi-char letter."""
        chip_data: Dict[str, Any] = {
            "TRDCs": [],
            "BCTRLs": [
                {
                    "bctrl": "AB",  # multi-char triggers get_bctrl to return None
                    "name": "BCTRL_AB",
                    "regs": {"IPG_DEBUG": []},
                }
            ],
            "Mixes": [],
        }
        chip = ChipModelImx9()

        with (
            patch("os.path.exists", return_value=True),
            patch("builtins.open", MagicMock()),
            patch("json.load", return_value=chip_data),
            patch("smct.model.model_chip.validate_json"),
        ):
            result = chip.load_from_json("/fake/path")

        assert result is True
        assert len(chip.get_all_bctrls()) == 0
        assert "not known" in caplog.text

    def test_load_from_json_parses_trdc_with_populated_mem(self) -> None:
        """load_from_json parses a TRDC MBC mem entry with non-empty origin/nblks/blksize."""
        chip_data: Dict[str, Any] = {
            "TRDCs": [
                {
                    "trdc": "A",
                    "name": "TRDC_A",
                    "ndid": 3,
                    "nmstr": 5,
                    "nmbc": 1,
                    "nmrc": 1,
                    "kpaen": 1,
                    "sidsz": 6,
                    "MBCs": [
                        {
                            "mbc": "0",
                            "mem": [{"origin": "0x1000", "nblks": 8, "blksize": "0x800"}],
                        }
                    ],
                    "MRCs": [
                        {
                            "mrc": "0",
                            "nrgns": 4,
                            "memory_region_offset": 14,
                            "origins": [{"origin": "0x8000_0000", "size": "0x0010_0000"}],
                        }
                    ],
                }
            ],
            "BCTRLs": [],
            "Mixes": [],
        }
        chip = ChipModelImx9()

        with (
            patch("os.path.exists", return_value=True),
            patch("builtins.open", MagicMock()),
            patch("json.load", return_value=chip_data),
            patch("smct.model.model_chip.validate_json"),
        ):
            result = chip.load_from_json("/fake/path")

        assert result is True
        trdc = chip.get_trdc("A", create_if_needed=False)
        assert trdc is not None
        mbc = trdc.get_mbc(0, create_if_needed=False)
        assert mbc is not None
        mem = mbc.get_model_mem(0)
        assert mem is not None
        assert mem.get_block_count() == 8
