#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Unit tests for smct.resources.default_permission DefaultPermission."""

import pytest

from smct.configuration.configuration_provider import ConfigurationProvider
from smct.model.chip_model_provider import ChipModelProvider
from smct.resources.default_permission import DefaultPermission
from smct.resources.resource_database_provider import ResourceDatabaseProvider
from smct.utils import FormatedInt


@pytest.fixture(autouse=True)
def clear_providers() -> None:
    """Reset singleton providers around each test."""
    ConfigurationProvider.clear_configuration()
    ResourceDatabaseProvider.clear_database()
    ChipModelProvider.clear_model()


def _make_perm(
    begin: int = 0x1000,
    size: int = 0x100,
    dids: tuple[int, int] = (0, 1),
    permission: str = "all",
    should_generate_debug_access: bool = True,
) -> DefaultPermission:
    """Return a DefaultPermission with the given arguments."""
    return DefaultPermission(
        FormatedInt(begin),
        FormatedInt(size),
        dids,
        permission,
        should_generate_debug_access,
    )


class TestDefaultPermission:
    """Tests for DefaultPermission."""

    def test_get_begin_returns_formated_int_with_correct_value(self) -> None:
        """Test get_begin returns a FormatedInt matching the constructor argument."""
        perm = _make_perm(begin=0x2000)
        begin = perm.get_begin()
        assert isinstance(begin, FormatedInt)
        assert begin.get_value() == 0x2000

    def test_get_size_returns_formated_int_with_correct_value(self) -> None:
        """Test get_size returns a FormatedInt matching the constructor argument."""
        perm = _make_perm(size=0x80)
        size = perm.get_size()
        assert isinstance(size, FormatedInt)
        assert size.get_value() == 0x80

    def test_get_dids_returns_tuple(self) -> None:
        """Test get_dids returns the exact tuple passed to the constructor."""
        perm = _make_perm(dids=(2, 5))
        assert perm.get_dids() == (2, 5)

    def test_get_permission_returns_string(self) -> None:
        """Test get_permission returns the permission string."""
        perm = _make_perm(permission="none")
        assert perm.get_permission() == "none"

    def test_should_generate_debug_access_defaults_true(self) -> None:
        """Test should_generate_debug_access is True when not explicitly set."""
        perm = DefaultPermission(FormatedInt(0), FormatedInt(0x10), (0, 0), "all")
        assert perm.should_generate_debug_access() is True

    def test_should_generate_debug_access_explicit_false(self) -> None:
        """Test should_generate_debug_access returns False when explicitly set to False."""
        perm = _make_perm(should_generate_debug_access=False)
        assert perm.should_generate_debug_access() is False

    def test_should_generate_debug_access_explicit_true(self) -> None:
        """Test should_generate_debug_access returns True when explicitly set to True."""
        perm = _make_perm(should_generate_debug_access=True)
        assert perm.should_generate_debug_access() is True

    def test_eq_identical_permissions_are_equal(self) -> None:
        """Test __eq__ returns True for two permissions with the same field values."""
        perm1 = _make_perm()
        perm2 = _make_perm()
        assert perm1 == perm2

    def test_eq_different_begin_is_not_equal(self) -> None:
        """Test __eq__ returns False when begin values differ."""
        perm1 = _make_perm(begin=0x1000)
        perm2 = _make_perm(begin=0x2000)
        assert perm1 != perm2

    def test_eq_different_size_is_not_equal(self) -> None:
        """Test __eq__ returns False when size values differ."""
        perm1 = _make_perm(size=0x100)
        perm2 = _make_perm(size=0x200)
        assert perm1 != perm2

    def test_eq_different_dids_is_not_equal(self) -> None:
        """Test __eq__ returns False when did tuples differ."""
        perm1 = _make_perm(dids=(0, 1))
        perm2 = _make_perm(dids=(0, 2))
        assert perm1 != perm2

    def test_eq_different_permission_is_not_equal(self) -> None:
        """Test __eq__ returns False when permission strings differ."""
        perm1 = _make_perm(permission="all")
        perm2 = _make_perm(permission="none")
        assert perm1 != perm2

    def test_eq_different_debug_flag_is_not_equal(self) -> None:
        """Test __eq__ returns False when should_generate_debug_access differs."""
        perm1 = _make_perm(should_generate_debug_access=True)
        perm2 = _make_perm(should_generate_debug_access=False)
        assert perm1 != perm2

    def test_eq_non_default_permission_type_returns_false(self) -> None:
        """Test __eq__ returns False when compared against a non-DefaultPermission object."""
        perm = _make_perm()
        assert perm != "not_a_permission"
        assert perm != 42
        assert perm is not None
