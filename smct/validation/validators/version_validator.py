#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause

"""Module with version related validations"""

import logging
import os
from typing import List

from smct.configuration.confdata import ConfigurationData
from smct.parsers.file_parser import FileParser
from smct.product_info import ProductInfo
from smct.validation.validation_entry import ValidationEntry
from smct.validation.validator_base import ValidatorBase

logger = logging.getLogger()


def _validate_sm_fw_compatibility(configuration: ConfigurationData, result: List[ValidationEntry]) -> None:
    """Checks validity of SM FW compatibility version.

    Args:
        configuration: The configuration data to validate.
        result: List to append validation entries to.
    """
    configuration_sm_fw_compatibility_version = ProductInfo.get_sm_fw_compatible_version()

    parser = FileParser()
    regex_str = r"my \$configVer\s=\s(\d+)"
    parser.add_regex(regex_str)
    file_path = os.path.join(configuration.get_sm_fw_root_directory(), "configs", "configtool.pl")
    if os.path.exists(file_path):
        parser.parse(file_path)
        parser_results = parser.get_results()
        if regex_str not in parser_results:
            logger.error("Missing SM FW configuration version in sources", extra={"source": file_path})
            return
        lines = parser_results[regex_str]
        if len(lines) > 1:
            logger.error("There is more than one line with SM FW configuration version", extra={"source": file_path})
            return
        perl_sm_fw_compatibility_version = lines[0].group(1)
        if str(configuration_sm_fw_compatibility_version) != str(perl_sm_fw_compatibility_version):
            msg = (
                f"Incompatible versions of configuration files. "
                f"SM FW supports version {perl_sm_fw_compatibility_version}"
                f", but this tool supports version {configuration_sm_fw_compatibility_version}"
            )
            result.append(ValidationEntry(logging.ERROR, file_path, msg))
    else:
        logger.info("SM FW configuration tool (configtool.pl) not found", extra={"source": file_path})


class VersionValidator(ValidatorBase):
    """Validator of versions"""

    def validate(self, configuration: ConfigurationData) -> List[ValidationEntry]:
        """Validates versions in the configuration.

        Args:
            configuration: The configuration data to validate.

        Returns:
            List of validation entries containing any validation errors or warnings.
        """
        result: List[ValidationEntry] = []
        _validate_sm_fw_compatibility(configuration, result)
        return result
