#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Module related to chip model."""

import json
import logging
import os
from typing import Any, Dict, List

from ..utils import FormatedInt, UInt64Constraints, validate_json
from .model_bctrl import BctrlModel
from .model_trdc import TrdcModel

logger = logging.getLogger()


class ChipModel:
    """Base class for all models of chips."""

    def __init__(self) -> None:
        self._mixes: List[str] = []

    def add_mix(self, mix: str) -> None:
        """Adds mix to the chip model.

        Args:
            mix: The mix to add to the chip model.
        """
        self._mixes.append(mix)

    def get_mixes(self) -> List[str]:
        """Returns list of all mixes on the chip.

        Returns:
            List of all mixes on the chip.
        """
        return self._mixes


class ChipModelImx9(ChipModel):
    """A chip model singleton (named 'CHIP') maintains global chip modules such as TRDCs etc."""

    def __init__(self) -> None:
        super().__init__()

        self._trdc: Dict[str, TrdcModel] = {}
        self._bctrl: Dict[str, BctrlModel] = {}

    def get_trdc(self, id_letter: str, create_if_needed: bool = True) -> TrdcModel | None:
        """Returns TRDC model instance by its letter.

        Args:
            id_letter: The letter identifier for the TRDC.
            create_if_needed: Whether to create the TRDC if it doesn't exist.

        Returns:
            TRDC model instance or None if not found and not created.
        """
        if len(id_letter) > 1:
            source = "/".join(["cfg", "mixes", "TRDC" + id_letter])
            logger.error("The '%s' is invalid TRDC identifier, use single letter ID", id_letter, extra={"source": source})
            return None
        if id_letter not in self._trdc and create_if_needed:
            self._trdc[id_letter] = TrdcModel(id_letter)
        return self._trdc[id_letter] if id_letter in self._trdc else None

    def get_all_trdcs(self) -> List[TrdcModel]:
        """Returns all TRDC instances in the chip.

        Returns:
            List of all TRDC instances in the chip.
        """
        return [self._trdc[trdc_letter] for trdc_letter in self._trdc]

    def get_bctrl(self, id_letter: str, create_if_needed: bool = True) -> BctrlModel | None:
        """Returns block control model instance by its letter.

        Args:
            id_letter: The letter identifier for the block control.
            create_if_needed: Whether to create the block control if it doesn't exist.

        Returns:
            Block control model instance or None if not found and not created.
        """
        if len(id_letter) > 1:
            source = "/".join(["user_config", "BCTRL" + id_letter])
            logger.error("The '%s' is invalid BCTRL identifier, use single letter ID", id_letter, extra={"source": source})
            return None
        if id_letter not in self._bctrl and create_if_needed:
            self._bctrl[id_letter] = BctrlModel(id_letter)
        return self._bctrl[id_letter] if id_letter in self._bctrl else None

    def get_all_bctrls(self) -> List[BctrlModel]:
        """Returns all block control units in the chip.

        Returns:
            List of all block control units in the chip.
        """
        return [self._bctrl[id_letter] for id_letter in self._bctrl]

    def get_raw_json(self) -> object:
        """Returns JSON object with all the data.

        Returns:
            JSON object containing all chip data including TRDCs, BCTRLs, and Mixes.
        """
        return {
            "TRDCs": [i.get_raw_json() for i in self.get_all_trdcs()],
            "BCTRLs": [i.get_raw_json() for i in self.get_all_bctrls()],
            "Mixes": self.get_mixes(),
        }

    def _parse_trdcs(self, trdcs: Any) -> None:
        """Parses information about TRDCs from the JSON object.

        Args:
            trdcs: JSON object containing TRDC information to parse.
        """
        for trdc_json in trdcs:
            trdc_letter = trdc_json["trdc"]
            trdc_model = self.get_trdc(trdc_letter)
            if trdc_model is None:
                source = "/".join(["json", "trdc", "TRDC_" + trdc_letter])
                logger.warning("TRDC model for TRDC %s is not known", trdc_letter, extra={"source": source})
                continue
            ndid = trdc_json["ndid"]
            nmstr = trdc_json["nmstr"]
            nmbc = trdc_json["nmbc"]
            nmrc = trdc_json["nmrc"]
            kpaen = trdc_json["kpaen"]
            sidsz = trdc_json["sidsz"]
            trdc_model.set_model_params(ndid, nmstr, nmbc, nmrc, kpaen, sidsz)
            for mbc_json in trdc_json["MBCs"]:
                mbc_index = int(mbc_json["mbc"])
                mbc_model = trdc_model.get_mbc(mbc_index)
                if mbc_model is None:
                    source = "/".join(["json", "trdc", "TRDC_" + trdc_letter, "MBC" + str(mbc_index)])
                    logger.warning("MBC%i model for TRDC %s is not known", mbc_index, trdc_letter, extra={"source": source})
                    continue
                mems_json = mbc_json["mem"]
                counter = -1
                for mem_json in mems_json:
                    counter += 1
                    if mem_json == {}:
                        continue
                    mem_origin = FormatedInt(mem_json["origin"])
                    if mem_origin.get_value() > UInt64Constraints.MAX_VALUE:
                        source = "/".join(["chip_data", trdc_json["name"], "MBC", mbc_json["mbc"], "MEM", str(counter), "ORIGIN"])
                        logger.error("Origin address %s exceeds maximum 64-bit value.", mem_origin, extra={"source": source})
                        mem_origin = FormatedInt(UInt64Constraints.DEFAULT_VALUE)

                    mem_blksize = FormatedInt(mem_json["blksize"])
                    mbc_model.set_model_mem(counter, mem_origin, mem_json["nblks"], mem_blksize)

            for mrc_json in trdc_json["MRCs"]:
                mrc_index = int(mrc_json["mrc"])
                mrc_model = trdc_model.get_mrc(mrc_index)
                if mrc_model is None:
                    source = "/".join(["json", "trdc", "TRDC_" + trdc_letter, "MRC" + str(mrc_index)])
                    logger.warning("MRC%i model for TRDC %s is not known", mrc_index, trdc_letter, extra={"source": source})
                    continue
                mrc_model.set_model_number_of_regions(int(mrc_json["nrgns"]))
                mrc_model.set_model_region_offset(int(mrc_json["memory_region_offset"]))
                origins = mrc_json.get("origins")
                if origins:
                    for origin in origins:
                        mrc_model.add_origin(origin["origin"], origin["size"])

    def _parse_block_controls(self, block_controls: Any) -> None:
        """Parses information about block control from the JSON object.

        Args:
            block_controls: JSON object containing block control information to parse.
        """
        for bctrl_json in block_controls:
            bctrl_letter = bctrl_json["bctrl"]
            bctrl = self.get_bctrl(bctrl_letter)
            if bctrl is None:
                source = "/".join(["json", "bctrl", "BCTRL" + bctrl_letter])
                logger.warning("BCTRL%s model is not known", bctrl_letter, extra={"source": source})
                continue
            ipg_debug_regs_json = bctrl_json["regs"]["IPG_DEBUG"]
            for ipg_debug_reg in ipg_debug_regs_json:
                cpu = ipg_debug_reg["cpu"]
                counter = 0
                for offset in ipg_debug_reg["offset"]:
                    if offset is not None:
                        bctrl.add_register_ipg_debug(cpu, counter, int(offset))
                    counter += 1

    def load_from_json(self, smct_configs_folder: str) -> bool:
        """Loads chip specific information from JSON file.

        Args:
            smct_configs_folder: Path to the folder containing SMCT configuration files.

        Returns:
            True if loading was successful, False otherwise.
        """
        file_name = os.path.join(smct_configs_folder, "chip_data.json")
        if not os.path.exists(file_name):
            logger.error("File not found: %s", file_name, extra={"source": file_name})
            return False
        with open(file_name, "r", encoding="utf-8") as file:
            json_object = json.load(file)
        if json_object is None:
            return False
        validate_json(json_object, file_name, "chip_schema.json", "warning")
        self._parse_trdcs(json_object["TRDCs"])
        self._parse_block_controls(json_object["BCTRLs"])
        mixes = json_object["Mixes"]
        for mix in mixes:
            self.add_mix(mix)
        return True
