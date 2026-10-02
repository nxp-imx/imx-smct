#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Unit tests for smct.validation.validators.resources_validator."""

import logging
from unittest.mock import Mock

import pytest

from smct.configuration.confdata import ConfigurationData
from smct.configuration.configuration_provider import ConfigurationProvider
from smct.model.chip_model_provider import ChipModelProvider
from smct.owners.owner_base import AssignedResource
from smct.owners.owner_dom import DOM
from smct.resources.res_mbc import MbcResource
from smct.resources.res_mrc import MrcResource
from smct.resources.resource_database_provider import ResourceDatabaseProvider
from smct.validation.validators.resources_validator import ResourcesValidator


@pytest.fixture(autouse=True)
def clear_providers() -> None:
    """Reset singleton providers around each test."""
    ConfigurationProvider.clear_configuration()
    ResourceDatabaseProvider.clear_database()
    ChipModelProvider.clear_model()


@pytest.fixture(name="validator")
def _validator() -> ResourcesValidator:
    """Create the validator under test."""
    return ResourcesValidator()


def _configuration_with_assignments(assignments: list[AssignedResource], debug_domains: list[DOM] | None = None) -> ConfigurationData:
    configuration = Mock(spec=ConfigurationData)
    configuration.get_all_trdc_assignments.return_value = {Mock(): assignments}
    configuration.get_all_debug_domains.return_value = debug_domains or []
    return configuration


def _assigned_mbc(owner: DOM, resource: MbcResource, params: dict[str, object] | None = None) -> AssignedResource:
    assigned_resource = Mock(spec=AssignedResource)
    assigned_resource.get_trdc_resources.return_value = [resource]
    assigned_resource.get_resource.return_value = resource
    assigned_resource.get_owner.return_value = owner
    assigned_resource.get_params.return_value = params or {}
    return assigned_resource


class TestResourcesValidator:
    """Tests for ResourcesValidator."""

    def test_validate_empty_configuration_returns_no_entries(self, validator: ResourcesValidator) -> None:
        """Test empty TRDC assignments are accepted."""
        configuration = _configuration_with_assignments([])

        result = validator.validate(configuration)

        assert not result

    def test_validate_non_exclusive_duplicate_resource_returns_no_entries(self, validator: ResourcesValidator) -> None:
        """Test same MBC resource can be assigned to multiple domains when not DOM-exclusive."""
        resource = MbcResource({"name": "MBC_TEST", "type": "MBC", "trdc": "A", "mbc": 0, "mem": 0, "blk": 1})
        assignment0 = _assigned_mbc(DOM("DOM0", 0, "Domain0"), resource)
        assignment1 = _assigned_mbc(DOM("DOM1", 1, "Domain1"), resource)
        configuration = _configuration_with_assignments([assignment0, assignment1])

        result = validator.validate(configuration)

        assert not result

    def test_validate_dom_exclusive_debug_domain_returns_no_entries(self, validator: ResourcesValidator) -> None:
        """Test debug domains are allowed to share a DOM-exclusive resource."""
        resource = MbcResource({"name": "MBC_TEST", "type": "MBC", "trdc": "A", "mbc": 0, "mem": 0, "blk": 1})
        exclusive_owner = DOM("DOM1", 1, "Domain1")
        debug_owner = DOM("DOM2", 2, "DebugDomain")
        debug_owner.set_debug()
        exclusive_assignment = _assigned_mbc(exclusive_owner, resource, {"dom_exclusive": True})
        debug_assignment = _assigned_mbc(debug_owner, resource)
        configuration = _configuration_with_assignments([exclusive_assignment, debug_assignment], [debug_owner])

        result = validator.validate(configuration)

        assert not result

    def test_validate_dom_exclusive_other_domain_returns_error_entry(self, validator: ResourcesValidator) -> None:
        """Test DOM-exclusive MBC assignment rejects sharing with a non-debug domain."""
        resource = MbcResource({"name": "MBC_TEST", "type": "MBC", "trdc": "A", "mbc": 0, "mem": 0, "blk": 1})
        exclusive_assignment = _assigned_mbc(DOM("DOM1", 1, "Domain1"), resource, {"dom_exclusive": True})
        conflicting_assignment = _assigned_mbc(DOM("DOM2", 2, "Domain2"), resource)
        configuration = _configuration_with_assignments([exclusive_assignment, conflicting_assignment])

        result = validator.validate(configuration)

        assert len(result) == 1
        assert result[0].get_level() == logging.ERROR
        assert result[0].get_source() == "user_config/Domain2/MBC_TEST"
        assert result[0].get_validation_id() == "DOM2.RESOURCES.MBC_TEST.DOM_EXCLUSIVE"
        assert "Resource MBC_TEST is assigned to domain 2 (Domain2) while marked as domain exclusive" == result[0].get_error_message()

    def test_validate_dom_exclusive_mrc_other_domain_returns_error_entry(self, validator: ResourcesValidator) -> None:
        """Test DOM-exclusive MRC assignment rejects sharing with a non-debug domain.

        This mirrors the MBC test above for the MRC resource type, confirming that
        the validator covers the MRC DOM-exclusive branch as well as the MBC one.
        """
        mrc_resource = MrcResource({"name": "MRC_TEST", "type": "MRC", "trdc": "A", "mrc": 0})

        exclusive_owner = DOM("DOM1", 1, "Domain1")
        conflicting_owner = DOM("DOM3", 3, "Domain3")

        exclusive_ar = Mock(spec=AssignedResource)
        exclusive_ar.get_trdc_resources.return_value = [mrc_resource]
        exclusive_ar.get_resource.return_value = mrc_resource
        exclusive_ar.get_owner.return_value = exclusive_owner
        exclusive_ar.get_params.return_value = {"dom_exclusive": True}

        conflicting_ar = Mock(spec=AssignedResource)
        conflicting_ar.get_trdc_resources.return_value = [mrc_resource]
        conflicting_ar.get_resource.return_value = mrc_resource
        conflicting_ar.get_owner.return_value = conflicting_owner
        conflicting_ar.get_params.return_value = {}

        configuration = _configuration_with_assignments([exclusive_ar, conflicting_ar])

        result = validator.validate(configuration)

        assert len(result) == 1
        assert result[0].get_level() == logging.ERROR
        assert result[0].get_source() == "user_config/Domain3/MRC_TEST"
        assert result[0].get_validation_id() == "DOM3.RESOURCES.MRC_TEST.DOM_EXCLUSIVE"
