#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause

"""Module related to resources configuration validation."""

import logging
from typing import Dict, List

from smct.configuration.confdata import ConfigurationData
from smct.owners.owner_base import AssignedResource
from smct.resources.res_mbc import MbcResource
from smct.resources.res_mdac import MdacResource
from smct.resources.res_mrc import MrcResource
from smct.validation.validation_entry import ValidationEntry
from smct.validation.validator_base import ValidatorBase


def _collect_trdc_resources(configuration: ConfigurationData) -> Dict[str, List[AssignedResource]]:
    all_resource_assignments: List[AssignedResource] = [item for sublist in configuration.get_all_trdc_assignments().values() for item in sublist]
    separated_resources: Dict[str, List[AssignedResource]] = {
        "MDAC": [],
        "MBC": [],
        "MRC": [],
    }

    for assigned_resource in all_resource_assignments:
        trdc_resources = assigned_resource.get_trdc_resources()
        for trd_resource in trdc_resources:
            resource = trd_resource
            if isinstance(resource, MdacResource):
                separated_resources["MDAC"].append(assigned_resource)
            elif isinstance(resource, MbcResource):
                separated_resources["MBC"].append(assigned_resource)
            elif isinstance(resource, MrcResource):
                separated_resources["MRC"].append(assigned_resource)
    return separated_resources


def _validate_dom_exclusive_resources(configuration: ConfigurationData, resources: List[AssignedResource], result: List[ValidationEntry]) -> None:
    """Validates that DOM-exclusive resources are not assigned to multiple domains.

    Args:
        configuration: The configuration data to validate
        resources: List of resources to validate
        result: List to append validation entries to
    """
    exclusive_resources = [resource for resource in resources if "dom_exclusive" in resource.get_params()]
    for exclusive_resource in exclusive_resources:
        allowed_dids = [exclusive_resource.get_owner().get_did()]
        for debug_domain in configuration.get_all_debug_domains():
            allowed_dids.append(debug_domain.get_did())

        for assigned_resource in resources:
            if assigned_resource.get_resource().get_name() == exclusive_resource.get_resource().get_name():
                assigned_did = assigned_resource.get_owner().get_did()
                if assigned_did not in allowed_dids:
                    validation_id = ".".join(
                        [assigned_resource.get_owner().get_id(), "RESOURCES", assigned_resource.get_resource().get_name(), "DOM_EXCLUSIVE"]
                    )
                    source = "/".join(["user_config", assigned_resource.get_owner().get_name(), assigned_resource.get_resource().get_name()])
                    result.append(
                        ValidationEntry(
                            logging.ERROR,
                            source,
                            f"Resource {assigned_resource.get_resource().get_name()} is assigned to domain {assigned_did} ({assigned_resource.get_owner().get_name()}) while marked as domain exclusive",
                            validation_id,
                        )
                    )


def _validate_trdc_resources(configuration: ConfigurationData, result: List[ValidationEntry]) -> None:
    """Checks validity of resources in configuration.

    Args:
        configuration: The configuration data to validate
        result: List to append validation entries to
    """
    resources = _collect_trdc_resources(configuration)
    for resource_type in ["MBC", "MRC"]:
        _validate_dom_exclusive_resources(configuration, resources[resource_type], result)


class ResourcesValidator(ValidatorBase):
    """Validator of resources."""

    def validate(self, configuration: ConfigurationData) -> List[ValidationEntry]:
        """Validates resource related configuration.

        Args:
            configuration: The configuration data to validate

        Returns:
            List of validation entries containing any validation errors or warnings
        """
        result: List[ValidationEntry] = []
        _validate_trdc_resources(configuration, result)
        return result
