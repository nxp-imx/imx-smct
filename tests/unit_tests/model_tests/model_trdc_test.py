#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Unit tests for smct.model.model_trdc TrdcModel."""

from typing import Iterator

import pytest

from smct.exceptions.cfg_tool_exception import CfgToolException
from smct.model.model_trdc import MbcModel, MrcModel, TrdcModel
from tests import test_utils


@pytest.fixture(autouse=True)
def restore_class_attrs() -> Iterator[None]:
    """Save and restore all class-level attributes mutated in tests."""
    with test_utils.restore_trdc_class_attrs(
        permission_types={"none": 0, "ro": 0x4444, "all": 0x7777},
        pa_types={"secure": 2, "nonsecure": 3},
        sa_types={"priv": 2, "user": 3},
        dfmt0_register={},
        dfmt1_register={},
    ):
        with test_utils.restore_mbc_mrc_class_attrs():
            yield


# ---------------------------------------------------------------------------
# TrdcModel tests
# ---------------------------------------------------------------------------


class TestTrdcModel:
    """Tests for TrdcModel."""

    def test_construction_default_name(self) -> None:
        """TrdcModel with no explicit name defaults to 'TRDC_<letter>'."""
        trdc = TrdcModel("A")

        assert trdc.get_id() == "A"
        assert trdc.get_name() == "TRDC_A"

    def test_construction_explicit_name(self) -> None:
        """TrdcModel stores the provided name verbatim."""
        trdc = TrdcModel("B", "MY_TRDC")

        assert trdc.get_name() == "MY_TRDC"

    def test_construction_multi_char_id_raises(self) -> None:
        """TrdcModel raises CfgToolException for multi-character id_letter."""
        with pytest.raises(CfgToolException):
            TrdcModel("AB")

    def test_set_model_params_and_getters(self) -> None:
        """set_model_params populates ndid/kpaen/sidsz accessible via getters."""
        trdc = TrdcModel("A")

        trdc.set_model_params(ndid=4, nmstr=8, nmbc=2, nmrc=1, kpaen=1, sidsz=6)

        assert trdc.get_domains_count() == 4
        assert trdc.get_kpaen() == 1
        assert trdc.get_sidsz() == 6

    def test_set_model_params_double_call_logs_error(self, caplog: pytest.LogCaptureFixture) -> None:
        """set_model_params on an already-configured TrdcModel logs an error."""
        trdc = TrdcModel("A")
        trdc.set_model_params(ndid=4, nmstr=8, nmbc=2, nmrc=1, kpaen=1, sidsz=6)

        trdc.set_model_params(ndid=5, nmstr=8, nmbc=2, nmrc=1, kpaen=0, sidsz=4)

        assert "cannot be re-configured" in caplog.text
        # original values remain unchanged
        assert trdc.get_domains_count() == 4

    def test_get_perm_value_and_string_coverage(self, caplog: pytest.LogCaptureFixture) -> None:
        """get_perm_value/get_perm_string: known names, error branch, round-trip, edge cases."""
        trdc = TrdcModel("A")

        # known permission values
        assert trdc.get_perm_value("none") == 0
        assert trdc.get_perm_value("all") == 0x7777

        # unknown → error logged, returns 0
        assert trdc.get_perm_value("bogus") == 0
        assert "bogus" in caplog.text

        # get_perm_string: known, negative, unknown positive
        assert trdc.get_perm_string(0x7777) == "all"
        assert trdc.get_perm_string(0x4444) == "ro"
        assert trdc.get_perm_string(-1) == "clearing"
        assert trdc.get_perm_string(0x1234) == "4660"

        # round-trip
        assert trdc.get_perm_string(trdc.get_perm_value("ro")) == "ro"

    def test_get_mbc_creates_when_create_if_needed_true(self) -> None:
        """get_mbc creates a new MbcModel for an unseen index when create_if_needed=True."""
        trdc = TrdcModel("A")
        trdc.set_model_params(ndid=4, nmstr=8, nmbc=3, nmrc=1, kpaen=1, sidsz=6)

        mbc = trdc.get_mbc(0, create_if_needed=True)

        assert mbc is not None
        assert isinstance(mbc, MbcModel)

    def test_get_mbc_returns_none_when_not_creating(self) -> None:
        """get_mbc returns None for an unseen index when create_if_needed=False."""
        trdc = TrdcModel("A")
        trdc.set_model_params(ndid=4, nmstr=8, nmbc=3, nmrc=1, kpaen=1, sidsz=6)

        result = trdc.get_mbc(0, create_if_needed=False)

        assert result is None

    def test_get_mbc_insane_index_logs_error_and_returns_none(self, caplog: pytest.LogCaptureFixture) -> None:
        """get_mbc returns None and logs error for an out-of-range index."""
        trdc = TrdcModel("A")
        trdc.set_model_params(ndid=4, nmstr=8, nmbc=2, nmrc=1, kpaen=1, sidsz=6)

        result = trdc.get_mbc(99, create_if_needed=True)

        assert result is None
        assert "MBC" in caplog.text

    def test_get_mbc_at_nmbc_boundary_is_allowed_by_current_implementation(self) -> None:
        """get_mbc allows mbc==nmbc (boundary at first-invalid) due to strict '>' check.

        Source uses ``if mbc > maximum`` not ``>=``, so index==nmbc passes through.
        This test documents the current boundary behavior to catch off-by-one regressions.
        """
        trdc = TrdcModel("A")
        trdc.set_model_params(ndid=4, nmstr=8, nmbc=2, nmrc=1, kpaen=1, sidsz=6)

        # mbc == nmbc == 2: strictly-greater check means this is NOT rejected
        result = trdc.get_mbc(2, create_if_needed=True)

        assert result is not None  # boundary passes under current '>' semantics

    def test_get_mbc_one_past_nmbc_logs_error_and_returns_none(self, caplog: pytest.LogCaptureFixture) -> None:
        """get_mbc returns None and logs error for mbc == nmbc + 1."""
        trdc = TrdcModel("A")
        trdc.set_model_params(ndid=4, nmstr=8, nmbc=2, nmrc=1, kpaen=1, sidsz=6)

        result = trdc.get_mbc(3, create_if_needed=True)

        assert result is None
        assert "MBC" in caplog.text

    def test_get_mrc_creates_when_create_if_needed_true(self) -> None:
        """get_mrc creates a new MrcModel for an unseen index when create_if_needed=True."""
        trdc = TrdcModel("A")
        trdc.set_model_params(ndid=4, nmstr=8, nmbc=2, nmrc=2, kpaen=1, sidsz=6)

        mrc = trdc.get_mrc(0, create_if_needed=True)

        assert mrc is not None
        assert isinstance(mrc, MrcModel)

    def test_get_mrc_returns_none_when_not_creating(self) -> None:
        """get_mrc returns None for an unseen index when create_if_needed=False."""
        trdc = TrdcModel("A")
        trdc.set_model_params(ndid=4, nmstr=8, nmbc=2, nmrc=2, kpaen=1, sidsz=6)

        result = trdc.get_mrc(0, create_if_needed=False)

        assert result is None

    def test_get_mrc_insane_index_logs_error_and_returns_none(self, caplog: pytest.LogCaptureFixture) -> None:
        """get_mrc returns None and logs error for an out-of-range index."""
        trdc = TrdcModel("A")
        trdc.set_model_params(ndid=4, nmstr=8, nmbc=2, nmrc=2, kpaen=1, sidsz=6)

        result = trdc.get_mrc(99, create_if_needed=True)

        assert result is None
        assert "MRC" in caplog.text

    def test_get_mrc_at_nmrc_boundary_logs_error_and_returns_none(self, caplog: pytest.LogCaptureFixture) -> None:
        """get_mrc returns None and logs error for mrc == nmrc (first invalid index).

        Source uses ``if mrc >= maximum`` so index == nmrc is the first rejected value.
        This test documents the boundary behavior to catch off-by-one regressions.
        """
        trdc = TrdcModel("A")
        trdc.set_model_params(ndid=4, nmstr=8, nmbc=2, nmrc=2, kpaen=1, sidsz=6)

        result = trdc.get_mrc(2, create_if_needed=True)

        assert result is None
        assert "MRC" in caplog.text

    def test_ordering_lt_and_gt(self) -> None:
        """TrdcModel comparison operators: lt/gt by id_letter; False for non-TrdcModel."""
        trdc_a = TrdcModel("A")
        trdc_b = TrdcModel("B")

        assert trdc_a < trdc_b
        assert (trdc_b < trdc_a) is False
        assert trdc_b > trdc_a
        assert (trdc_a > trdc_b) is False
        assert (trdc_a < "string") is False
        assert (trdc_a > 42) is False

    def test_str_representation(self) -> None:
        """__str__ includes the id letter, domain count, and mbc/mrc counts."""
        trdc = TrdcModel("A")
        trdc.set_model_params(ndid=3, nmstr=5, nmbc=2, nmrc=1, kpaen=1, sidsz=6)

        text = str(trdc)

        assert "A" in text
        assert "3" in text  # domain count
        assert "2" in text  # mbc count

    # -----------------------------------------------------------------------
    # get_register_offset — 5 regex forms
    # -----------------------------------------------------------------------

    def test_get_register_offset_mdac(self) -> None:
        """get_register_offset MDAC form: TRDC_<X>_MDA_W<w>_<mda>_DFMT<d>.

        Formula: 0x800 + (0x20 * mda) + (0x4 * w)
        Example: w=1, mda=2 → 0x800 + 0x40 + 0x4 = 0x844
        """
        trdc = TrdcModel("A")
        trdc.set_model_params(ndid=4, nmstr=8, nmbc=2, nmrc=1, kpaen=1, sidsz=6)

        reg_name = "TRDC_A_MDA_W1_2_DFMT0"
        expected = 0x800 + (0x20 * 2) + (0x4 * 1)  # 0x844

        offset = trdc.get_register_offset(reg_name)

        assert offset == expected

    def test_get_register_offset_mbc_glbac(self) -> None:
        """get_register_offset MBC_GLBAC form: TRDC_<X>_MBC<mbc>_MEMN_GLBAC<g>.

        Formula: 0x10020 + (0x2000 * mbc) + (0x4 * glbac)
        Example: mbc=1, glbac=3 → 0x10020 + 0x2000 + 0xC = 0x1202C
        """
        trdc = TrdcModel("A")
        trdc.set_model_params(ndid=4, nmstr=8, nmbc=2, nmrc=1, kpaen=1, sidsz=6)

        reg_name = "TRDC_A_MBC1_MEMN_GLBAC3"
        expected = 0x10020 + (0x2000 * 1) + (0x4 * 3)  # 0x1202C

        offset = trdc.get_register_offset(reg_name)

        assert offset == expected

    def test_get_register_offset_mbc_dom_mem0(self) -> None:
        """get_register_offset MBC_DOM form with mem=0.

        Formula (mem==0): 0x10040 + (0x2000 * mbc) + (0x200 * dom) + (0x4 * w)
        Example: mbc=0, dom=1, mem=0, w=2 → 0x10040 + 0 + 0x200 + 0x8 = 0x10248
        """
        trdc = TrdcModel("A")
        trdc.set_model_params(ndid=4, nmstr=8, nmbc=2, nmrc=1, kpaen=1, sidsz=6)

        reg_name = "TRDC_A_MBC0_DOM1_MEM0_BLK_CFG_W2"
        expected = 0x10040 + (0x2000 * 0) + (0x200 * 1) + (0x4 * 2)  # 0x10248

        offset = trdc.get_register_offset(reg_name)

        assert offset == expected

    def test_get_register_offset_mbc_dom_mem_nonzero(self) -> None:
        """get_register_offset MBC_DOM form with mem>0 adds extra offset.

        Formula (mem>0): base + 0x140 + (0x28 * (mem - 1))
        Example: mbc=0, dom=0, mem=1, w=0 → 0x10040 + 0 + 0 + 0 + 0x140 + 0 = 0x10180
        """
        trdc = TrdcModel("A")
        trdc.set_model_params(ndid=4, nmstr=8, nmbc=2, nmrc=1, kpaen=1, sidsz=6)

        reg_name = "TRDC_A_MBC0_DOM0_MEM1_BLK_CFG_W0"
        expected = 0x10040 + (0x2000 * 0) + (0x200 * 0) + (0x4 * 0) + 0x140 + (0x28 * 0)  # 0x10180

        offset = trdc.get_register_offset(reg_name)

        assert offset == expected

    def test_get_register_offset_mrc_glbac(self) -> None:
        """get_register_offset MRC_GLBAC form: TRDC_<X>_MRC<mrc>_GLBAC<g>.

        Formula: 0x10020 + (0x2000 * nmbc) + (0x1000 * mrc) + (0x4 * glbac)
        With nmbc=2, mrc=0, glbac=1: 0x10020 + 0x4000 + 0 + 0x4 = 0x14024
        """
        trdc = TrdcModel("A")
        trdc.set_model_params(ndid=4, nmstr=8, nmbc=2, nmrc=1, kpaen=1, sidsz=6)

        reg_name = "TRDC_A_MRC0_GLBAC1"
        expected = 0x10020 + (0x2000 * 2) + (0x1000 * 0) + (0x4 * 1)  # 0x14024

        offset = trdc.get_register_offset(reg_name)

        assert offset == expected

    def test_get_register_offset_mrc_dom(self) -> None:
        """get_register_offset MRC_DOM form: TRDC_<X>_MRC<mrc>_DOM<dom>_RGD<rgn>_W<w>.

        Formula: 0x10040 + (0x2000*nmbc) + (0x1000*mrc) + (0x100*dom) + (0x8*rgn) + (0x4*w)
        With nmbc=2, mrc=0, dom=1, rgn=2, w=0: 0x10040+0x4000+0+0x100+0x10+0 = 0x14150
        """
        trdc = TrdcModel("A")
        trdc.set_model_params(ndid=4, nmstr=8, nmbc=2, nmrc=1, kpaen=1, sidsz=6)

        reg_name = "TRDC_A_MRC0_DOM1_RGD2_W0"
        expected = 0x10040 + (0x2000 * 2) + (0x1000 * 0) + (0x100 * 1) + (0x8 * 2) + (0x4 * 0)  # 0x14150

        offset = trdc.get_register_offset(reg_name)

        assert offset == expected

    def test_get_register_offset_unknown_raises_key_error(self) -> None:
        """get_register_offset raises KeyError for an unrecognised register name."""
        trdc = TrdcModel("A")

        with pytest.raises(KeyError):
            trdc.get_register_offset("TRDC_A_UNKNOWN_REG")

    def test_get_raw_json_shape(self) -> None:
        """TrdcModel.get_raw_json returns a dict with expected top-level keys."""
        trdc = TrdcModel("A")
        trdc.set_model_params(ndid=3, nmstr=5, nmbc=1, nmrc=1, kpaen=1, sidsz=6)

        raw = trdc.get_raw_json()

        assert isinstance(raw, dict)
        assert raw["trdc"] == "A"  # type: ignore[index]
        assert raw["name"] == "TRDC_A"  # type: ignore[index]
        assert raw["ndid"] == 3  # type: ignore[index]
        assert "MBCs" in raw  # type: ignore[operator]
        assert "MRCs" in raw  # type: ignore[operator]

    def test_set_model_params_mbc_out_of_range_logs_error(self, caplog: pytest.LogCaptureFixture) -> None:
        """set_model_params logs error when existing MBC list exceeds nmbc."""
        trdc = TrdcModel("A")
        # Pre-populate _mbc by requesting index 3 (grows list to length 4)
        trdc.get_mbc(3, create_if_needed=True)

        # Now set nmbc=1 which is less than 4 → should log error
        trdc.set_model_params(ndid=3, nmstr=5, nmbc=1, nmrc=1, kpaen=1, sidsz=6)

        assert "MBC" in caplog.text

    def test_set_model_params_mrc_out_of_range_logs_error(self, caplog: pytest.LogCaptureFixture) -> None:
        """set_model_params logs error when existing MRC list exceeds nmrc."""
        trdc = TrdcModel("A")
        # Pre-populate _mrc by requesting index 3 (grows list to length 4)
        trdc.get_mrc(3, create_if_needed=True)

        # Now set nmrc=1 which is less than 4 → should log error
        trdc.set_model_params(ndid=3, nmstr=5, nmbc=1, nmrc=1, kpaen=1, sidsz=6)

        assert "MRC" in caplog.text

    def test_get_mbc_grows_list_via_while_loop(self) -> None:
        """get_mbc grows the internal list when requesting index beyond current length."""
        trdc = TrdcModel("A")
        # No set_model_params → _mbc is [] and nmbc=0 → maximum=10
        mbc = trdc.get_mbc(5, create_if_needed=True)

        assert mbc is not None
        assert isinstance(mbc, MbcModel)

    def test_get_mrc_grows_list_via_while_loop(self) -> None:
        """get_mrc grows the internal list when requesting index beyond current length."""
        trdc = TrdcModel("A")
        # No set_model_params → _mrc is [] and nmrc=0 → maximum=10
        mrc = trdc.get_mrc(3, create_if_needed=True)

        assert mrc is not None
        assert isinstance(mrc, MrcModel)
