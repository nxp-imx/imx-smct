#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Unit tests for smct.model.model_trdc MbcMemModel, MbcModel, and MrcModel.

Split from model_trdc_test.py to keep each file under 400 lines.
"""

from typing import Any, Dict, Iterator

import pytest

from smct.exceptions.cfg_tool_exception import CfgToolException
from smct.model.model_trdc import MbcMemModel, MbcModel, MrcModel
from smct.utils import FormatedInt
from tests import test_utils


@pytest.fixture(autouse=True)
def restore_class_attrs() -> Iterator[None]:
    """Save and restore class-level attributes mutated during tests."""
    with test_utils.restore_trdc_class_attrs(
        permission_types={"none": 0, "all": 0x7777},
    ):
        with test_utils.restore_mbc_mrc_class_attrs():
            yield


# ---------------------------------------------------------------------------
# MbcMemModel tests
# ---------------------------------------------------------------------------


class TestMbcMemModel:
    """Tests for MbcMemModel."""

    def test_default_construction(self) -> None:
        """MbcMemModel starts with origin 0, 0 blocks, and blksize 0."""
        mem = MbcMemModel()

        assert mem.get_origin().get_value() == 0
        assert mem.get_block_count() == 0
        assert mem.get_block_size().get_value() == 0

    def test_set_and_get_origin(self) -> None:
        """set_origin stores and get_origin retrieves the FormatedInt."""
        mem = MbcMemModel()
        origin = FormatedInt("0x1000")

        mem.set_origin(origin)

        assert mem.get_origin().get_value() == 0x1000

    def test_set_and_get_nblks(self) -> None:
        """set_nblks stores and get_block_count retrieves the count."""
        mem = MbcMemModel()

        mem.set_nblks(64)

        assert mem.get_block_count() == 64

    def test_set_and_get_blksize(self) -> None:
        """set_blksize stores and get_block_size retrieves the FormatedInt."""
        mem = MbcMemModel()
        blksize = FormatedInt("0x8000")

        mem.set_blksize(blksize)

        assert mem.get_block_size().get_value() == 0x8000

    def test_get_raw_json_shape(self) -> None:
        """get_raw_json returns a dict with 'origin', 'nblks', 'blksize' keys."""
        mem = MbcMemModel()
        mem.set_origin(FormatedInt("0x2000"))
        mem.set_nblks(8)
        mem.set_blksize(FormatedInt("0x4000"))

        raw = mem.get_raw_json()

        assert isinstance(raw, dict)
        assert "origin" in raw  # type: ignore[operator]
        assert "nblks" in raw  # type: ignore[operator]
        assert "blksize" in raw  # type: ignore[operator]
        assert raw["nblks"] == 8  # type: ignore[index]


# ---------------------------------------------------------------------------
# MbcModel tests
# ---------------------------------------------------------------------------


class TestMbcModel:
    """Tests for MbcModel."""

    def test_construction_stores_index(self) -> None:
        """MbcModel stores the given mbc index in get_raw_json."""
        mbc = MbcModel("TRDC_A", 0)

        raw = mbc.get_raw_json()
        assert raw["mbc"] == 0  # type: ignore[index]

    def test_set_model_mem_creates_entry(self) -> None:
        """set_model_mem creates and populates a MbcMemModel at the given index."""
        mbc = MbcModel("TRDC_A", 0)
        origin = FormatedInt("0x1000")
        blksize = FormatedInt("0x800")

        mbc.set_model_mem(0, origin, 32, blksize)

        mem = mbc.get_model_mem(0)
        assert mem is not None
        assert mem.get_origin().get_value() == 0x1000
        assert mem.get_block_count() == 32
        assert mem.get_block_size().get_value() == 0x800

    def test_get_model_mem_unknown_index_returns_none(self) -> None:
        """get_model_mem returns None for a slot that was never populated."""
        mbc = MbcModel("TRDC_A", 0)

        assert mbc.get_model_mem(0) is None

    def test_set_model_mem_duplicate_raises(self) -> None:
        """set_model_mem raises CfgToolException if the mem slot is already configured."""
        mbc = MbcModel("TRDC_A", 0)
        origin = FormatedInt("0x1000")
        blksize = FormatedInt("0x800")
        mbc.set_model_mem(0, origin, 32, blksize)

        with pytest.raises(CfgToolException):
            mbc.set_model_mem(0, FormatedInt("0x2000"), 16, blksize)

    def test_set_model_mem_with_zero_origin_allows_second_write(self) -> None:
        """set_model_mem with origin==0 does NOT raise on second write.

        The duplicate-detection check is ``if mbc_mem.get_origin().get_value()`` which
        is falsy for origin=0.  This means a zero-origin slot is silently overwritten.
        This test documents the current behavior so regressions are visible.
        """
        mbc = MbcModel("TRDC_A", 0)
        blksize = FormatedInt("0x100")
        # First write with origin=0
        mbc.set_model_mem(0, FormatedInt("0x0"), 8, blksize)
        # Second write: should NOT raise because origin==0 makes check falsy
        mbc.set_model_mem(0, FormatedInt("0x0"), 16, blksize)
        mem = mbc.get_model_mem(0)
        assert mem is not None
        # The second write wins (overwrite without error)
        assert mem.get_block_count() == 16

    def test_get_raw_json_shape(self) -> None:
        """get_raw_json contains 'mbc' and 'mem' keys with correct index."""
        mbc = MbcModel("TRDC_A", 1)

        raw = mbc.get_raw_json()

        assert "mbc" in raw  # type: ignore[operator]
        assert "mem" in raw  # type: ignore[operator]
        assert raw["mbc"] == 1  # type: ignore[index]

    def test_get_raw_json_mem_list_has_empty_dicts_for_unset_slots(self) -> None:
        """get_raw_json mem list contains {} for unset MbcMemModel slots."""
        mbc = MbcModel("TRDC_A", 0)

        raw = mbc.get_raw_json()
        mem_list = raw["mem"]  # type: ignore[index]

        assert isinstance(mem_list, list)
        assert all(m == {} for m in mem_list)


# ---------------------------------------------------------------------------
# MrcModel tests
# ---------------------------------------------------------------------------


class TestMrcModel:
    """Tests for MrcModel."""

    def test_default_construction(self) -> None:
        """MrcModel starts with 0 regions and default offset 14."""
        mrc = MrcModel("TRDC_A", 0)

        assert mrc.get_model_number_of_regions() == 0
        assert mrc.get_model_region_offset() == 14

    def test_set_and_get_number_of_regions(self) -> None:
        """set_model_number_of_regions stores the count."""
        mrc = MrcModel("TRDC_A", 0)

        mrc.set_model_number_of_regions(8)

        assert mrc.get_model_number_of_regions() == 8

    def test_set_number_of_regions_double_call_raises(self) -> None:
        """set_model_number_of_regions raises CfgToolException on second call."""
        mrc = MrcModel("TRDC_A", 0)
        mrc.set_model_number_of_regions(8)

        with pytest.raises(CfgToolException):
            mrc.set_model_number_of_regions(16)

    def test_set_and_get_region_offset(self) -> None:
        """set_model_region_offset changes the memory region address offset."""
        mrc = MrcModel("TRDC_A", 0)

        mrc.set_model_region_offset(10)

        assert mrc.get_model_region_offset() == 10

    def test_add_origin_appends_entry(self) -> None:
        """add_origin appends an origin/size dict to the internal list."""
        mrc = MrcModel("TRDC_A", 0)

        mrc.add_origin("0x8000_0000", "0x0010_0000")
        mrc.add_origin("0x9000_0000", "0x0020_0000")

        raw: Dict[str, Any] = mrc.get_raw_json()  # type: ignore[assignment]
        origins = raw["origins"]
        assert len(origins) == 2
        assert origins[0]["origin"] == "0x8000_0000"
        assert origins[1]["size"] == "0x0020_0000"

    def test_get_raw_json_shape(self) -> None:
        """get_raw_json contains 'mrc', 'nrgns', 'memory_region_offset', 'origins' keys."""
        mrc = MrcModel("TRDC_A", 2)
        mrc.set_model_number_of_regions(4)

        raw: Dict[str, Any] = mrc.get_raw_json()  # type: ignore[assignment]

        assert "mrc" in raw
        assert "nrgns" in raw
        assert "memory_region_offset" in raw
        assert "origins" in raw
        assert raw["mrc"] == 2
        assert raw["nrgns"] == 4
