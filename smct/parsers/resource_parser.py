#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Module related to loading resource database JSONs"""

import json
import logging
import os
from typing import Any, Dict, List

from smct.configuration.confdata_fusa import FusaTask
from smct.model.model_trdc import MbcModel, MrcModel, TrdcModel
from smct.owners.owner_agent import Channel, Mailbox, ScmiChannel, SmtChannel
from smct.owners.owner_base import AssignedResource
from smct.owners.owner_lm import LM
from smct.resources.res_api import ApiResource
from smct.utils import make_enum_int_dictionary, make_enum_str_dictionary

logger = logging.getLogger()


class ResourceParser:
    """Parser of resource database JSONs"""

    soc_directory: str | None = None

    def __init__(self, device: str):
        """Initialize ResourceParser with device configuration.

        Args:
            device: The device name to load configuration for.
        """
        if ResourceParser.soc_directory is None:
            directory, _ = os.path.split(os.path.realpath(__file__))
            self._resources_path = os.path.join(directory, "..", "..", "sm_model")
        elif not os.path.isabs(ResourceParser.soc_directory):
            self._resources_path = os.path.join(ResourceParser.soc_directory, "sm_model")
        else:
            self._resources_path = ResourceParser.soc_directory
        soc_json_path = os.path.join(self._resources_path, "soc.json")
        if not os.path.exists(soc_json_path):
            logger.error("File not found: %s", soc_json_path, extra={"source": soc_json_path})
            return
        with open(soc_json_path, "r", encoding="utf-8") as file:
            soc_json = json.load(file)
            if device not in soc_json:
                device = "simu"
            self._soc_model = soc_json[device]["soc_model"]
            self._sm_model = soc_json[device]["sm_model"]

    def parse_soc_resources(self) -> None:
        """Parses soc_models and sm_models resource files."""
        self._parse_sm_models()
        self._parse_soc_models()

    def _parse_soc_models(self) -> None:
        """Parses soc model - SM DID, MU count and security peripherals."""
        soc_models_path = os.path.join(self._resources_path, self._soc_model)
        if not os.path.exists(soc_models_path):
            logger.error("File not found: %s", soc_models_path, extra={"source": soc_models_path})
            return
        with open(soc_models_path, "r", encoding="utf-8") as file:
            model_json = json.load(file)

            # SM DID
            LM.sm_did = model_json["sm_did"]

            # MU count
            LM.mu_max_count = model_json["MU_count"]

            # Security peripherals
            sec_peripherals = model_json["security_peripherals"]
            for peripheral in sec_peripherals:
                self._parse_sec_peripheral(peripheral)

    def _parse_dfmt0_register(self, bitfields: List[Any]) -> None:
        """Parse DFMT0 register bitfields and set corresponding TrdcModel attributes.

        Args:
            bitfields: List of bitfield dictionaries containing name and offset.
        """
        TrdcModel.DFMT0_register = {}
        for bitfield in bitfields:
            offset = bitfield["offset"]
            width = bitfield["width"]
            name = bitfield["name"]
            TrdcModel.DFMT0_register[name] = {"offset": offset, "width": width}

    def _parse_dfmt1_register(self, bitfields: List[Any]) -> None:
        """Parse DFMT1 register bitfields and set corresponding TrdcModel attributes.

        Args:
            bitfields: List of bitfield dictionaries containing name and offset.
        """
        TrdcModel.DFMT1_register = {}
        for bitfield in bitfields:
            offset = bitfield["offset"]
            width = bitfield["width"]
            name = bitfield["name"]
            TrdcModel.DFMT1_register[name] = {"offset": offset, "width": width}

    def _parse_sec_peripheral(self, peripheral_json: Dict) -> None:
        """Parses security peripheral configuration.

        Args:
            peripheral_json: Dictionary containing peripheral configuration data.
        """
        # only TRDC supported for now
        if peripheral_json["peripheral"] == "TRDC":
            if "debug_domain_permission" in peripheral_json:
                TrdcModel.DEBUG_DOMAIN_PERMISSION = int(peripheral_json["debug_domain_permission"], 0)

            registers = peripheral_json["MDAC"]["registers"] + peripheral_json["MBC"]["registers"] + peripheral_json["MRC"]["registers"]
            for register in registers:
                match (register["name"]):
                    case "DFMT0":
                        self._parse_dfmt0_register(register["bitfields"])
                    case "DFMT1":
                        self._parse_dfmt1_register(register["bitfields"])
                    case "BLK_CFG":
                        MbcModel.register_width = register["width"]
                        MbcModel.block_size = 0
                        for bitfield in register["bitfields"]:
                            MbcModel.block_size += bitfield["width"]
                            if bitfield["name"] == "NSE":
                                MbcModel.nse_bit_offset = bitfield["offset"]
                    case "RGD":
                        for bitfield in register["bitfields"]:
                            if bitfield["name"] == "STRT_ADDR":
                                MrcModel.strt_addr_offset = bitfield["offset"]
                            elif bitfield["name"] == "END_ADDR":
                                MrcModel.end_addr_offset = bitfield["offset"]

            mrc_configurations = peripheral_json["MRC"].get("configurations", [])
            TrdcModel.mrc_configurations = {}
            for configuration in mrc_configurations:
                mrc_index = configuration["memory"]
                if mrc_index not in TrdcModel.mrc_configurations:
                    TrdcModel.mrc_configurations[mrc_index] = [{"origin": configuration["origin"], "size": configuration["size"]}]
                else:
                    TrdcModel.mrc_configurations[mrc_index].append({"origin": configuration["origin"], "size": configuration["size"]})

            types_json = peripheral_json["setting_types"]
            for setting_type in types_json:
                if setting_type["type"] == "enum":
                    items = setting_type["items"]
                    match (setting_type["id"]):
                        case "pa":
                            TrdcModel.pa_types = make_enum_int_dictionary(items)
                        case "sa":
                            TrdcModel.sa_types = make_enum_int_dictionary(items)
                        case "access_templates":
                            TrdcModel.permission_types = make_enum_int_dictionary(items)

    def _parse_sm_models(self) -> None:
        """Parses sm models JSON to class enumerations."""
        sm_models_path = os.path.join(self._resources_path, self._sm_model)
        if not os.path.exists(sm_models_path):
            logger.error("File not found: %s", sm_models_path, extra={"source": sm_models_path})
            return
        with open(sm_models_path, "r", encoding="utf-8") as file:
            model_json = json.load(file)

            # protocols types and tests
            tests_protocols = []
            for protocol in model_json["protocols"]["items"]:
                tests_protocols.append((protocol["prefix"], protocol["test"]))
            LM.protocols = tests_protocols

            types_json = model_json["setting_types"]
            for setting_type in types_json:
                if setting_type["type"] == "enum":
                    items = setting_type["items"]
                    types_dict = make_enum_str_dictionary(items)
                    match (setting_type["id"]):
                        case "fusa_task_type":
                            FusaTask.task_types = types_dict
                        case "lmm_safe_type":
                            LM.safety_types = types_dict
                        case "lmm_ss_type":
                            ApiResource.start_stop_types = types_dict
                        case "lmm_react_types":
                            AssignedResource.react_types = types_dict
                        case "lmm_auto_boot":
                            LM.auto_boot_types = types_dict
                        case "rpc_types":
                            Channel.rpc_types = types_dict
                        case "scmi_channel_types":
                            ScmiChannel.channel_types = types_dict
                        case "scmi_sequence":
                            ScmiChannel.sequence_types = types_dict
                        case "scmi_perms":
                            ApiResource.permission_types = types_dict
                        case "xport_types":
                            Channel.xport_types = types_dict
                        case "smt_crc_types":
                            SmtChannel.smt_crc_types = types_dict
                        case "mailbox_types":
                            Mailbox.mailbox_types = types_dict
                        case "mailbox_np_priority":
                            Mailbox.mailbox_priority_types = types_dict
