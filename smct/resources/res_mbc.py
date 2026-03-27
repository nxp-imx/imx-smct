#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause

"""Module related to TRDC MBC resources"""

import logging
from enum import Enum
from typing import Any, Dict

from smct.exceptions.cfg_tool_exception import CfgToolException

from ..model.chip_model_provider import ChipModelProvider
from .res_trdc import MbcMrcResource

logger = logging.getLogger()


class MbcResourceWriteType(Enum):
    """Enumeration of write types into MBC registers"""

    UNKNOWN = 0  # Fallback value when the write type is not decided
    BLOCK = 1  # Write to one block
    RANGE = 2  # Write to range of blocks (block + block count)
    MEM = 3  # Write to all blocks in the MEM

    @classmethod
    def from_name(cls, name: str) -> "MbcResourceWriteType":
        """Returns enumeration value by its name

        Args:
            name: The name of the enumeration value

        Returns:
            The corresponding MbcResourceWriteType enumeration value
        """
        if name == "block":
            return cls.BLOCK
        if name == "range":
            return cls.RANGE
        if name == "mem":
            return cls.MEM
        return cls.UNKNOWN


class MbcResource(MbcMrcResource):
    """MBC resource object"""

    def __init__(self, raw: Dict[str, Any]):
        super().__init__(raw)

        try:
            self._write_type: MbcResourceWriteType = MbcResourceWriteType.from_name(self["write_type"] if "write_type" in self else "unknown")
            self._trdc_id: str = self["trdc"]
            self._mbc: int = self["mbc"]
            self._mem: int = self["mem"]
            self._blk: int = self["blk"] if "blk" in self else 0
            self._bcnt: int = self["bcnt"] if "bcnt" in self else 1
        except KeyError as exc:
            raise CfgToolException(f"Missing required MBC attributes in database object {raw}") from exc

    def get_index(self) -> int:
        """Returns MBC index of the MBC

        Returns:
            The MBC index
        """
        return self._mbc

    def get_mem(self) -> int:
        """Returns MEM index of the MBC

        Returns:
            The MEM index
        """
        return self._mem

    def get_write_type(self) -> MbcResourceWriteType:
        """Returns the write type of this MBC resource. Possible values can be found in enum MbcResourceWriteType

        Returns:
            The write type of this MBC resource
        """
        return self._write_type

    def get_block_range(self) -> range:
        """Returns range of blocks to be set by the MBC resource. Returns range(0,0) in case of error.

        Returns:
            Range of blocks to be set by the MBC resource
        """
        # Default block range for one block or range of blocks
        block_range = range(self._blk, self._blk + self._bcnt)

        # Block range for the whole MEM assignment
        if self._write_type == MbcResourceWriteType.MEM:
            trdc = ChipModelProvider.get_model().get_trdc(self.get_trdc_id())
            if trdc is None:
                raise CfgToolException(f"TRDC {self.get_trdc_id()} does not exist")
            mbc_model = trdc.get_mbc(self._mbc, False)
            if mbc_model is None:
                source = "/".join(["model", "chip", trdc.get_name()])
                logger.error("MBC assignment to whole MEM did not found model for %s", str(self), extra={"source": source})
                return range(0, 0)
            mem_model = mbc_model.get_model_mem(self._mem)
            if mem_model is None:
                source = "/".join(["model", "chip", trdc.get_name(), "MBC" + str(self._mbc), "MEM" + str(self._mem)])
                logger.error("MBC assignment to whole MEM did not found model for %s", str(self), extra={"source": source})
                return range(0, 0)
            block_count = mem_model.get_block_count()
            block_range = range(0, block_count)
        return block_range

    def get_register_name(self, domain_id: int, word: int) -> str:
        """Returns register name for given domain and word

        Args:
            domain_id: The domain ID
            word: The word number

        Returns:
            The register name
        """
        return f"TRDC_{self._trdc_id}_MBC{self._mbc}_DOM{domain_id}_MEM{self._mem}_BLK_CFG_W{word}"

    def __str__(self) -> str:
        return f"TRDC_{self._trdc_id} MBC{self._mbc} MEM{self._mem}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._raw})"
