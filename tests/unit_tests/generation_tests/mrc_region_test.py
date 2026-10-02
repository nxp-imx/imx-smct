#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Unit tests for smct.generation.trdc.mrc_region.MrcRegion pure data class."""

from smct.generation.trdc.mrc_region import MrcRegion


class TestMrcRegion:
    """Tests for MrcRegion pure data class."""

    def test_get_domain_returns_constructor_value(self) -> None:
        """get_domain() returns the domain passed to the constructor."""
        region = MrcRegion(domain=2, start_address=0x1000, end_address=0x2000, permission=0x7)

        assert region.get_domain() == 2

    def test_get_start_address_returns_constructor_value(self) -> None:
        """get_start_address() returns the start address passed to the constructor."""
        region = MrcRegion(domain=0, start_address=0x8000, end_address=0x9000, permission=0)

        assert region.get_start_address() == 0x8000

    def test_get_end_address_returns_constructor_value(self) -> None:
        """get_end_address() returns the end address passed to the constructor."""
        region = MrcRegion(domain=0, start_address=0x0000, end_address=0xFFFF, permission=0)

        assert region.get_end_address() == 0xFFFF

    def test_get_permission_returns_constructor_value(self) -> None:
        """get_permission() returns the initial permission."""
        region = MrcRegion(domain=0, start_address=0, end_address=1, permission=0x3F)

        assert region.get_permission() == 0x3F

    # --- merge_permission ---

    def test_merge_permission_ors_bits(self) -> None:
        """merge_permission() ORs new bits into the existing permission."""
        region = MrcRegion(domain=0, start_address=0, end_address=1, permission=0x0F)

        region.merge_permission(0xF0)

        assert region.get_permission() == 0xFF

    def test_merge_permission_idempotent_for_same_bits(self) -> None:
        """Merging already-set bits does not change the permission."""
        region = MrcRegion(domain=0, start_address=0, end_address=1, permission=0xFF)

        region.merge_permission(0x0F)

        assert region.get_permission() == 0xFF

    # --- is_clearing ---

    def test_is_clearing_false_when_permission_is_zero(self) -> None:
        """is_clearing() is False for zero permission."""
        region = MrcRegion(domain=0, start_address=0, end_address=1, permission=0)

        assert region.is_clearing() is False

    def test_is_clearing_false_when_permission_is_positive(self) -> None:
        """is_clearing() is False for positive permissions."""
        region = MrcRegion(domain=0, start_address=0, end_address=1, permission=1)

        assert region.is_clearing() is False

    def test_is_clearing_true_when_permission_is_negative(self) -> None:
        """is_clearing() is True when permission is negative."""
        region = MrcRegion(domain=0, start_address=0, end_address=1, permission=-1)

        assert region.is_clearing() is True

    # --- is_dom_clearing ---

    def test_is_dom_clearing_false_by_default(self) -> None:
        """is_dom_clearing() is False when clearing is not passed."""
        region = MrcRegion(domain=0, start_address=0, end_address=1, permission=0)

        assert region.is_dom_clearing() is False

    def test_is_dom_clearing_true_when_set(self) -> None:
        """is_dom_clearing() returns True when clearing=True is passed."""
        region = MrcRegion(domain=0, start_address=0, end_address=1, permission=0, clearing=True)

        assert region.is_dom_clearing() is True

    # --- overwrites ---

    def test_overwrites_same_domain_start_end_returns_true(self) -> None:
        """Two regions with the same domain/start/end overwrite each other."""
        r1 = MrcRegion(domain=1, start_address=0x1000, end_address=0x2000, permission=1)
        r2 = MrcRegion(domain=1, start_address=0x1000, end_address=0x2000, permission=2)

        assert r1.overwrites(r2) is True

    def test_overwrites_different_domain_returns_false(self) -> None:
        """Differing domain means no overwrite."""
        r1 = MrcRegion(domain=0, start_address=0x1000, end_address=0x2000, permission=0)
        r2 = MrcRegion(domain=1, start_address=0x1000, end_address=0x2000, permission=0)

        assert r1.overwrites(r2) is False

    def test_overwrites_different_start_returns_false(self) -> None:
        """Differing start address means no overwrite."""
        r1 = MrcRegion(domain=0, start_address=0x1000, end_address=0x2000, permission=0)
        r2 = MrcRegion(domain=0, start_address=0x1100, end_address=0x2000, permission=0)

        assert r1.overwrites(r2) is False

    def test_overwrites_different_end_returns_false(self) -> None:
        """Differing end address means no overwrite."""
        r1 = MrcRegion(domain=0, start_address=0x1000, end_address=0x2000, permission=0)
        r2 = MrcRegion(domain=0, start_address=0x1000, end_address=0x3000, permission=0)

        assert r1.overwrites(r2) is False

    def test_overwrites_non_mrc_region_returns_false(self) -> None:
        """Passing a non-MrcRegion object returns False."""
        region = MrcRegion(domain=0, start_address=0, end_address=1, permission=0)

        assert region.overwrites("not a region") is False
        assert region.overwrites(None) is False

    # --- __eq__ ---

    def test_eq_identical_regions_returns_true(self) -> None:
        """Two regions with identical fields compare equal."""
        r1 = MrcRegion(domain=1, start_address=0x100, end_address=0x200, permission=5)
        r2 = MrcRegion(domain=1, start_address=0x100, end_address=0x200, permission=5)

        assert r1 == r2

    def test_eq_different_domain_returns_false(self) -> None:
        """Different domain makes regions unequal."""
        r1 = MrcRegion(domain=0, start_address=0x100, end_address=0x200, permission=5)
        r2 = MrcRegion(domain=1, start_address=0x100, end_address=0x200, permission=5)

        assert r1 != r2

    def test_eq_different_start_address_returns_false(self) -> None:
        """Different start address makes regions unequal."""
        r1 = MrcRegion(domain=0, start_address=0x100, end_address=0x200, permission=5)
        r2 = MrcRegion(domain=0, start_address=0x110, end_address=0x200, permission=5)

        assert r1 != r2

    def test_eq_different_end_address_returns_false(self) -> None:
        """Different end address makes regions unequal."""
        r1 = MrcRegion(domain=0, start_address=0x100, end_address=0x200, permission=5)
        r2 = MrcRegion(domain=0, start_address=0x100, end_address=0x300, permission=5)

        assert r1 != r2

    def test_eq_different_permission_returns_false(self) -> None:
        """Different permission makes regions unequal."""
        r1 = MrcRegion(domain=0, start_address=0x100, end_address=0x200, permission=1)
        r2 = MrcRegion(domain=0, start_address=0x100, end_address=0x200, permission=2)

        assert r1 != r2

    def test_eq_non_mrc_region_returns_false(self) -> None:
        """Comparing against non-MrcRegion returns False."""
        region = MrcRegion(domain=0, start_address=0, end_address=1, permission=0)

        assert region != "other"
        assert region != 42

    # --- __str__ ---

    def test_str_contains_domain_start_end_permission(self) -> None:
        """__str__ includes all four key fields."""
        region = MrcRegion(domain=2, start_address=0x1000, end_address=0x2000, permission=7)

        result = str(region)

        assert "domain:2" in result
        assert "4096" in result or "0x1000" in result or "start:4096" in result
        assert "permission:7" in result
