#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Unit tests for smct.generation.trdc.mbc_block.MbcBlock pure data class."""

from unittest.mock import Mock

from smct.generation.trdc.mbc_block import MbcBlock
from smct.resources.res_mbc import MbcResource


def _make_resource(index: int = 0, mem: int = 1, name: str = "RES_A", reg_name: str = "REG_W0") -> Mock:
    """Build a lightweight MbcResource mock."""
    res: Mock = Mock(spec=MbcResource)
    res.get_index.return_value = index
    res.get_mem.return_value = mem
    res.get_name.return_value = name
    res.get_register_name.return_value = reg_name
    return res


class TestMbcBlock:
    """Tests for MbcBlock pure data class."""

    def test_get_domain_returns_constructor_value(self) -> None:
        """get_domain() returns the domain passed to the constructor."""
        res = _make_resource()
        block = MbcBlock(domain=3, resource=res, block_range=(0, 4), permission=0xFF)

        assert block.get_domain() == 3

    def test_get_mbc_delegates_to_resource_get_index(self) -> None:
        """get_mbc() delegates to resource.get_index()."""
        res = _make_resource(index=2)
        block = MbcBlock(domain=0, resource=res, block_range=(0, 1), permission=0)

        assert block.get_mbc() == 2
        res.get_index.assert_called_once()

    def test_get_mem_delegates_to_resource_get_mem(self) -> None:
        """get_mem() delegates to resource.get_mem()."""
        res = _make_resource(mem=3)
        block = MbcBlock(domain=0, resource=res, block_range=(0, 1), permission=0)

        assert block.get_mem() == 3
        res.get_mem.assert_called_once()

    def test_get_block_range_returns_constructor_value(self) -> None:
        """get_block_range() returns the block_range passed to the constructor."""
        res = _make_resource()
        block = MbcBlock(domain=0, resource=res, block_range=(5, 10), permission=0)

        assert block.get_block_range() == (5, 10)

    def test_get_permission_returns_constructor_value(self) -> None:
        """get_permission() returns the initial permission."""
        res = _make_resource()
        block = MbcBlock(domain=1, resource=res, block_range=(0, 1), permission=0xAB)

        assert block.get_permission() == 0xAB

    def test_get_name_delegates_to_resource_get_name(self) -> None:
        """get_name() delegates to resource.get_name()."""
        res = _make_resource(name="MY_RES")
        block = MbcBlock(domain=0, resource=res, block_range=(0, 1), permission=0)

        assert block.get_name() == "MY_RES"
        res.get_name.assert_called_once()

    def test_get_register_name_delegates_to_resource(self) -> None:
        """get_register_name() delegates to resource.get_register_name(domain, word)."""
        res = _make_resource(reg_name="TRDC_A_MBC0_DOM1_MEM0_BLK_CFG_W0")
        block = MbcBlock(domain=1, resource=res, block_range=(0, 1), permission=0)

        result = block.get_register_name(word=0)

        assert result == "TRDC_A_MBC0_DOM1_MEM0_BLK_CFG_W0"
        res.get_register_name.assert_called_once_with(1, 0)

    def test_merge_permission_ors_bits(self) -> None:
        """merge_permission() ORs new bits into existing permission."""
        res = _make_resource()
        block = MbcBlock(domain=0, resource=res, block_range=(0, 1), permission=0x0F)

        block.merge_permission(0xF0)

        assert block.get_permission() == 0xFF

    def test_merge_permission_idempotent_for_same_bits(self) -> None:
        """Merging already-set bits does not change the permission."""
        res = _make_resource()
        block = MbcBlock(domain=0, resource=res, block_range=(0, 1), permission=0xFF)

        block.merge_permission(0x0F)

        assert block.get_permission() == 0xFF

    def test_is_dom_clearing_false_by_default(self) -> None:
        """is_dom_clearing() is False when clearing is not passed."""
        res = _make_resource()
        block = MbcBlock(domain=0, resource=res, block_range=(0, 1), permission=0)

        assert block.is_dom_clearing() is False

    def test_is_dom_clearing_true_when_set(self) -> None:
        """is_dom_clearing() returns True when clearing=True is passed."""
        res = _make_resource()
        block = MbcBlock(domain=0, resource=res, block_range=(0, 1), permission=0, clearing=True)

        assert block.is_dom_clearing() is True

    # --- overwrites ---

    def test_overwrites_same_domain_name_range_returns_true(self) -> None:
        """Two blocks with the same domain, name, and range overwrite each other."""
        res = _make_resource(name="R")
        b1 = MbcBlock(domain=1, resource=res, block_range=(0, 2), permission=0x01)
        b2 = MbcBlock(domain=1, resource=res, block_range=(0, 2), permission=0x02)

        assert b1.overwrites(b2) is True

    def test_overwrites_different_domain_returns_false(self) -> None:
        """Differing domain means no overwrite."""
        res = _make_resource(name="R")
        b1 = MbcBlock(domain=0, resource=res, block_range=(0, 2), permission=0)
        b2 = MbcBlock(domain=1, resource=res, block_range=(0, 2), permission=0)

        assert b1.overwrites(b2) is False

    def test_overwrites_different_name_returns_false(self) -> None:
        """Differing resource name means no overwrite."""
        res_a = _make_resource(name="RES_A")
        res_b = _make_resource(name="RES_B")
        b1 = MbcBlock(domain=0, resource=res_a, block_range=(0, 2), permission=0)
        b2 = MbcBlock(domain=0, resource=res_b, block_range=(0, 2), permission=0)

        assert b1.overwrites(b2) is False

    def test_overwrites_different_range_returns_false(self) -> None:
        """Differing block range means no overwrite."""
        res = _make_resource(name="R")
        b1 = MbcBlock(domain=0, resource=res, block_range=(0, 2), permission=0)
        b2 = MbcBlock(domain=0, resource=res, block_range=(3, 5), permission=0)

        assert b1.overwrites(b2) is False

    def test_overwrites_non_mbc_block_returns_false(self) -> None:
        """Passing a non-MbcBlock object returns False."""
        res = _make_resource()
        block = MbcBlock(domain=0, resource=res, block_range=(0, 1), permission=0)

        assert block.overwrites("not a block") is False
        assert block.overwrites(None) is False

    # --- __eq__ ---

    def test_eq_identical_blocks_returns_true(self) -> None:
        """Two blocks with identical fields compare equal."""
        res = _make_resource()
        b1 = MbcBlock(domain=1, resource=res, block_range=(0, 3), permission=7)
        b2 = MbcBlock(domain=1, resource=res, block_range=(0, 3), permission=7)

        assert b1 == b2

    def test_eq_different_domain_returns_false(self) -> None:
        """Different domain makes blocks unequal."""
        res = _make_resource()
        b1 = MbcBlock(domain=0, resource=res, block_range=(0, 1), permission=1)
        b2 = MbcBlock(domain=1, resource=res, block_range=(0, 1), permission=1)

        assert b1 != b2

    def test_eq_different_resource_returns_false(self) -> None:
        """Different resource object makes blocks unequal."""
        res_a = _make_resource()
        res_b = _make_resource()
        b1 = MbcBlock(domain=0, resource=res_a, block_range=(0, 1), permission=1)
        b2 = MbcBlock(domain=0, resource=res_b, block_range=(0, 1), permission=1)

        assert b1 != b2

    def test_eq_different_block_range_returns_false(self) -> None:
        """Different block range makes blocks unequal."""
        res = _make_resource()
        b1 = MbcBlock(domain=0, resource=res, block_range=(0, 1), permission=1)
        b2 = MbcBlock(domain=0, resource=res, block_range=(2, 3), permission=1)

        assert b1 != b2

    def test_eq_different_permission_returns_false(self) -> None:
        """Different permission makes blocks unequal."""
        res = _make_resource()
        b1 = MbcBlock(domain=0, resource=res, block_range=(0, 1), permission=1)
        b2 = MbcBlock(domain=0, resource=res, block_range=(0, 1), permission=2)

        assert b1 != b2

    def test_eq_non_mbc_block_returns_false(self) -> None:
        """Comparing against non-MbcBlock returns False."""
        res = _make_resource()
        block = MbcBlock(domain=0, resource=res, block_range=(0, 1), permission=0)

        assert block != "other"
        assert block != 42

    # --- __str__ ---

    def test_str_contains_mbc_domain_mem_range(self) -> None:
        """__str__ includes mbc, domain, mem, and range fields."""
        res = _make_resource(index=2, mem=1)
        block = MbcBlock(domain=3, resource=res, block_range=(4, 8), permission=0)

        result = str(block)

        assert "mbc:2" in result
        assert "domain:3" in result
        assert "mem:1" in result
        assert "(4, 8)" in result
