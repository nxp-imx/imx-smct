#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Unit tests for smct.resources.res_trdc TRDC/MBC/MRC resource types."""

from typing import Any, Dict, Iterator

import pytest

from smct.resources.res_trdc import MbcMrcResource, TrdcResource
from smct.utils import FormatedInt
from tests import test_utils


@pytest.fixture(autouse=True)
def trdc_permission_types() -> Iterator[None]:
    """Provide minimal permission names used by assignment parsing."""
    with test_utils.restore_trdc_class_attrs(permission_types={"none": 0, "all": 0x7777}):
        yield


class TestTrdcResource:
    """Tests for TrdcResource."""

    def test_construction_sets_name_and_empty_trdc_id(self) -> None:
        """Test base TRDC resource stores atomic data and starts with no TRDC ID."""
        raw: Dict[str, Any] = {"name": "TRDC_BASE", "type": "TRDC"}

        resource = TrdcResource(raw)

        assert resource.get_name() == "TRDC_BASE"
        assert resource.get_trdc_id() == ""
        assert resource.get_raw_json() == raw


class TestMbcMrcResource:
    """Tests for MbcMrcResource."""

    def test_constructor_loads_valid_default_permissions(self) -> None:
        """Test default permissions from raw JSON are converted into DefaultPermission objects."""
        resource = MbcMrcResource(
            {
                "name": "MBC_MRC_BASE",
                "type": "MBC",
                "mbc": 0,
                "default_permissions": [{"begin": "0x1000", "size": "0x100", "domains": {"from": 2, "to": 3}, "permission": "all"}],
            }
        )

        permissions = resource.get_default_permissions()

        assert len(permissions) == 1
        assert permissions[0].get_begin().get_value() == 0x1000
        assert permissions[0].get_size().get_value() == 0x100
        assert permissions[0].get_dids() == (2, 3)
        assert permissions[0].get_permission() == "all"
        assert permissions[0].should_generate_debug_access() is True

    def test_add_default_permission_deduplicates_equal_entries(self) -> None:
        """Test adding the same default permission twice keeps one entry."""
        resource = MbcMrcResource({"name": "MBC_MRC_BASE", "type": "MBC"})
        begin = FormatedInt(0x2000)
        size = FormatedInt(0x80)

        resource.add_default_permission(begin, size, (1, 1), "none", True)
        resource.add_default_permission(FormatedInt(0x2000), FormatedInt(0x80), (1, 1), "none", True)

        assert len(resource.get_default_permissions()) == 1

    def test_get_raw_json_includes_debug_suppression(self) -> None:
        """Test serialized default permissions include no_debug only when debug generation is disabled."""
        resource = MbcMrcResource({"name": "MBC_MRC_BASE", "type": "MRC"})
        begin = FormatedInt(0)
        size = FormatedInt(0x10)

        resource.add_default_permission(begin, size, (0, 0), "none", True)
        resource.add_default_permission(begin, size, (1, 1), "all", False)

        assert resource.get_raw_json()["default_permissions"] == [
            {"begin": begin, "size": size, "domains": {"from": 0, "to": 0}, "permission": "none"},
            {"begin": begin, "size": size, "domains": {"from": 1, "to": 1}, "permission": "all", "no_debug": True},
        ]

    def test_assignment_parameters_with_did_add_default_permission_and_skip_assignment(self) -> None:
        """Test DID override creates a default permission instead of an owner assignment."""
        resource = MbcMrcResource({"name": "MBC_MRC_BASE", "type": "MRC"})

        result = resource.get_assignment_parameters(["begin=0x3000", "size=0x20", "did=4-5", "perm=all", "nodbg"])

        assert result is None
        permissions = resource.get_default_permissions()
        assert len(permissions) == 1
        assert permissions[0].get_begin().get_value() == 0x3000
        assert permissions[0].get_size().get_value() == 0x20
        assert permissions[0].get_dids() == (4, 5)
        assert permissions[0].should_generate_debug_access() is False

    def test_assignment_parameters_without_did_return_assignment_data(self) -> None:
        """Test regular assignment parameters preserve permission, range, clr, and flags."""
        resource = MbcMrcResource({"name": "MBC_MRC_BASE", "type": "MRC"})

        result = resource.get_assignment_parameters(["begin=0x4000", "end=0x40ff", "perm=none", "clr=6", "dom_clr_unused", "dom_exclusive"])

        assert result is not None
        assert result["perm"] == "none"
        assert result["begin"].get_value() == 0x4000
        assert result["size"].get_value() == 0x100
        assert result["clr"] == "6"
        assert result["dom_clr_unused"] is True
        assert result["dom_exclusive"] is True
