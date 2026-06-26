#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Module related to TRDC model."""

import logging
import re
from typing import Any, Dict, List, Optional

from smct.exceptions.cfg_tool_exception import CfgToolException
from smct.utils import FormatedInt

logger = logging.getLogger()


class MbcMemModel:
    """One MBC.MEM region definition."""

    def __init__(self) -> None:
        self._origin: FormatedInt = FormatedInt("0")  # base address of this MBC (if used for memory check)
        self._nblks: int = 0  # number of memory blocks  (if used for memory check)
        self._blksize: FormatedInt = FormatedInt("0")  # size of one memory block (if used for memory check)

    def get_raw_json(self) -> object:
        """Returns JSON object with raw data.

        Returns:
            JSON object with raw data
        """
        return {
            "origin": self._origin,
            "nblks": self._nblks,
            "blksize": self._blksize,
        }

    def get_origin(self) -> FormatedInt:
        """Returns origin of the MEM.

        Returns:
            Origin of the MEM
        """
        return self._origin

    def get_block_count(self) -> int:
        """Returns amount of blocks in the MEM.

        Returns:
            Amount of blocks in the MEM
        """
        return self._nblks

    def get_block_size(self) -> FormatedInt:
        """Returns size of the MEM.

        Returns:
            Size of the MEM
        """
        return self._blksize

    def set_origin(self, origin: FormatedInt) -> None:
        """Set origin of the MEM.

        Args:
            origin: Origin of the MEM
        """
        self._origin = origin

    def set_nblks(self, nblks: int) -> None:
        """Set amount of blocks in the MEM.

        Args:
            nblks: Amount of blocks in the MEM
        """
        self._nblks = nblks

    def set_blksize(self, blksize: FormatedInt) -> None:
        """Set size of the MEM.

        Args:
            blksize: Size of the MEM
        """
        self._blksize = blksize


class MbcModel:
    """One Memory Block Checker unit. Each TRDC has multiple MBCs."""

    block_size: int
    register_width: int
    nse_bit_offset: int

    def __init__(self, trdc_name: str, mbc: int) -> None:
        self._mbc: int = mbc  # index of self MBC unit within parent TRDC model
        self._name: str = f"{trdc_name}.MBC{mbc}"  # mostly for debugging purposes
        self._mem: List[MbcMemModel | None] = [None] * 4  # MBC sub-MEM configuration
        self._glbac: List[int] = [0x0000, 0x6666, 0x7777]  # default always-used GLBAC, extended as needed later

    def set_model_mem(self, mem: int, origin: FormatedInt, nblks: int, blksize: FormatedInt) -> None:
        """Sets MEM model based on given information.

        Args:
            mem: MEM index
            origin: Base address of the MEM
            nblks: Number of blocks
            blksize: Size of one block
        """
        if not self._mem[mem]:
            self._mem[mem] = MbcMemModel()
        mbc_mem = self._mem[mem]
        if mbc_mem is None:
            return

        if mbc_mem.get_origin().get_value():
            raise CfgToolException(f"{self._name}.MEM{mem} cannot be re-configured once defined")
        mbc_mem.set_origin(origin)
        mbc_mem.set_nblks(nblks)
        mbc_mem.set_blksize(blksize)

    def get_model_mem(self, index: int) -> None | MbcMemModel:
        """Returns MEM model based on index.

        Args:
            index: Index of the MEM model

        Returns:
            MEM model or None if not found
        """
        return self._mem[index]

    def get_raw_json(self) -> object:
        """Returns JSON object with raw data.

        Returns:
            JSON object with raw data
        """
        return {
            "mbc": self._mbc,
            "mem": [m.get_raw_json() if m else {} for m in self._mem],
        }


class MrcModel:
    """One MRC Region Checker unit. Each TRDC has multiple MRCs."""

    strt_addr_offset: int
    end_addr_offset: int

    def __init__(self, trdc_name: str, mrc: int):  # type: ignore
        self._mrc: int = mrc  # Index of self MRC unit within parent TRDC model
        self._name: str = f"{trdc_name}.MRC{mrc}"  # Name of the MRC - mostly for debugging purposes
        self._number_of_regions: int = 0  # number of regions need to be set before first use of this object
        self._memory_region_address_offset: int = 14  # 14 or 10 (if big=1) bits on mx95
        self._origins: List[Any] = []

    def add_origin(self, origin: str, size: str) -> None:
        """Adds origin address and size of the region.

        Args:
            origin: origin address to set
            size: size of the region
        """
        self._origins.append({"origin": origin, "size": size})

    def set_model_number_of_regions(self, number_of_regions: int) -> None:
        """Sets number of regions in the MRC model.

        Args:
            number_of_regions: Number of regions to set
        """
        if self._number_of_regions > 0:  # already set?
            raise CfgToolException(f"{self._name} cannot be re-configured once defined")
        self._number_of_regions = number_of_regions

    def set_model_region_offset(self, offset: int) -> None:
        """Sets memory region offset in the MRC model.

        Args:
            offset: Memory region offset to set
        """
        self._memory_region_address_offset = offset

    def get_model_region_offset(self) -> int:
        """Returns memory region offset.

        Returns:
            Memory region offset
        """
        return self._memory_region_address_offset

    def get_model_number_of_regions(self) -> int:
        """Returns number of regions in this MRC.

        Returns:
            Number of regions in this MRC
        """
        return self._number_of_regions

    def get_raw_json(self) -> object:
        """Returns JSON object with raw data.

        Returns:
            JSON object with raw data
        """
        return {
            "mrc": self._mrc,
            "nrgns": self._number_of_regions,
            "memory_region_offset": self._memory_region_address_offset,
            "origins": self._origins,
        }


class TrdcModel:
    """TRDC unit model."""

    # named perm values
    permission_types: Dict[str, int]
    # named privilege values
    pa_types: Dict[str, int]
    # named security values
    sa_types: Dict[str, int]

    # MRC configurations
    mrc_configurations: Dict[str, List[Any]]

    # DFMT registers
    DFMT0_register: Dict[str, Dict[str, Any]]
    DFMT1_register: Dict[str, Dict[str, Any]]

    DEBUG_DOMAIN_PERMISSION: int

    def __init__(self, id_letter: str, name: Optional[str | None] = None) -> None:
        if len(id_letter) > 1:
            raise CfgToolException(f"The '{id_letter} is invalid TRDC identifier, use single letter ID")

        self._id_letter: str = id_letter  # single-letter identifier of the TRDC module
        self._name: str = name if name else f"TRDC_{id_letter}"  # friendly name of the TRDC module
        self._ndid: int = 0  # number of DIDs
        self._nmrc: int = 0  # number of MRCs
        self._nmbc: int = 0  # number of MBCs
        self._nmstr: int = 0  # number of masters
        self._kpaen: int = 1  # KPA enable
        self._sidsz: int = 6  # SID size
        self._mbc: List[MbcModel | None] = []  # list of all MBCs
        self._mrc: List[MrcModel | None] = []  # list of all MRCs
        self._model_already_set: bool = False  # flag that this model has been fully set

    def __lt__(self, other: object) -> bool:
        if isinstance(other, TrdcModel):
            return self._id_letter < other._id_letter
        return False

    def __gt__(self, other: object) -> bool:
        if isinstance(other, TrdcModel):
            return self._id_letter > other._id_letter
        return False

    def __str__(self) -> str:
        return f"TRDC_{self._id_letter}[domains={self._ndid}, mbcs={self._nmbc}. mrcs={self._nmrc}]"

    def set_model_params(self, ndid: int, nmstr: int, nmbc: int, nmrc: int, kpaen: int, sidsz: int) -> None:
        """Sets TRDC model parameters.

        Args:
            ndid: Number of DIDs
            nmstr: Number of masters
            nmbc: Number of MBCs
            nmrc: Number of MRCs
            kpaen: KPA enable
            sidsz: SID size
        """
        if self._model_already_set:
            logger.error("%s cannot be re-configured", self._name)
            return
        self._ndid = ndid
        self._nmstr = nmstr
        self._nmbc = nmbc
        self._nmrc = nmrc
        self._kpaen = kpaen
        self._sidsz = sidsz
        if len(self._mbc) > nmbc:
            logger.error("%s MBC unit exists out of 'nmbc' range", self._name)
            return
        while nmbc > len(self._mbc):
            self._mbc.append(None)
        if len(self._mrc) > nmrc:
            logger.error("%s MRC unit exists out of 'nmrc' range", self._name)
            return
        while nmrc > len(self._mrc):
            self._mrc.append(None)
        self._model_already_set = True

    def get_id(self) -> str:
        """Returns letter id of the TRDC.

        Returns:
            Letter id of the TRDC
        """
        return self._id_letter

    def get_name(self) -> str:
        """Returns name of the TRDC.

        Returns:
            Name of the TRDC
        """
        return self._name

    def get_kpaen(self) -> int:
        """Returns KPA enable value.

        Returns:
            KPA enable value
        """
        return self._kpaen

    def get_sidsz(self) -> int:
        """Returns SID size value.

        Returns:
            SID size value
        """
        return self._sidsz

    def get_perm_value(self, permission: str) -> int:
        """Returns value of the given permission.

        Args:
            permission: Permission name

        Returns:
            Value of the given permission
        """
        if permission in self.permission_types:
            return self.permission_types[permission]
        logger.error("Invalid TRDC permission value '%s' requested", permission)
        return 0

    def get_perm_string(self, permission: int) -> str:
        """Returns value of the given permission.

        Args:
            permission: Permission name

        Returns:
            Value of the given permission
        """
        for permission_str in self.permission_types:
            if self.permission_types[permission_str] == permission:
                return permission_str if permission_str else "0 (default)"
        if permission < 0:
            return "clearing"
        return str(permission)

    def get_mbc(self, mbc: int, create_if_needed: bool = True) -> MbcModel | None:
        """Returns MBC model based on given index.

        Args:
            mbc: MBC index
            create_if_needed: Whether to create MBC if it doesn't exist

        Returns:
            MBC model or None if not found
        """
        maximum = self._nmbc if self._nmbc else 10
        if mbc > maximum:
            logger.error("Insane MBC module requested MBC%s", mbc)
            return None
        while mbc >= len(self._mbc):
            self._mbc.append(None)
        if self._mbc[mbc] is None and create_if_needed:
            self._mbc[mbc] = MbcModel(self.get_name(), mbc)
        return self._mbc[mbc]

    def get_mrc(self, mrc: int, create_if_needed: bool = True) -> MrcModel | None:
        """Returns MRC model based on given index.

        Args:
            mrc: MRC index
            create_if_needed: Whether to create MRC if it doesn't exist

        Returns:
            MRC model or None if not found
        """
        maximum = self._nmrc if self._nmrc else 10
        if mrc >= maximum:
            logger.error("Insane MRC module requested MRC%s", mrc)
            return None
        while mrc >= len(self._mrc):
            self._mrc.append(None)
        if self._mrc[mrc] is None and create_if_needed:
            self._mrc[mrc] = MrcModel(self.get_name(), mrc)
        return self._mrc[mrc]

    def get_domains_count(self) -> int:
        """Returns amount of domains in this TRDC.

        Returns:
            Amount of domains in this TRDC
        """
        return self._ndid

    @classmethod
    def _get_register_offset_mdac(cls, m: re.Match) -> int:
        """Returns offset of given MDAC register.

        Args:
            m: Regular expression match object

        Returns:
            Offset of given MDAC register
        """
        w = int(m[2])
        mda = int(m[3])
        addr = 0x800 + (0x20 * mda) + (0x4 * w)
        return addr

    @classmethod
    def _get_register_offset_mbc_glbac(cls, m: re.Match) -> int:
        """Returns offset of given MBC_GLBAC register.

        Args:
            m: Regular expression match object

        Returns:
            Offset of given MBC_GLBAC register
        """
        mbc = int(m[2])
        glbac = int(m[3])
        addr = 0x10020 + (0x2000 * mbc) + (0x4 * glbac)
        return addr

    @classmethod
    def _get_register_offset_mbc_dom(cls, m: re.Match) -> int:
        """Returns offset of given MBC register.

        Args:
            m: Regular expression match object

        Returns:
            Offset of given MBC register
        """
        mbc = int(m[2])
        dom = int(m[3])
        mem = int(m[4])
        w = int(m[5])
        addr = 0x10040 + (0x2000 * mbc) + (0x200 * dom) + (0x4 * w)
        if mem > 0:
            addr = addr + 0x140 + (0x28 * (mem - 1))
        return addr

    def _get_register_offset_mrc_glbac(self, m: re.Match) -> int:
        """Returns offset of given MRC_GLBAC register.

        Args:
            m: Regular expression match object

        Returns:
            Offset of given MRC_GLBAC register
        """
        mrc = int(m[2])
        glbac = int(m[3])
        addr = 0x10020 + (0x2000 * self._nmbc) + (0x1000 * mrc) + (0x4 * glbac)
        return addr

    def _get_register_offset_mrc_dom(self, m: re.Match) -> int:
        """Returns offset of given MRC register.

        Args:
            m: Regular expression match object

        Returns:
            Offset of given MRC register
        """
        mrc = int(m[2])
        domain = int(m[3])
        region = int(m[4])
        word = int(m[5])
        addr = 0x10040 + (0x2000 * self._nmbc) + (0x1000 * mrc) + (0x100 * domain) + (0x8 * region) + (0x4 * word)
        return addr

    def get_register_offset(self, reg: str) -> int:
        """Returns offset of given register.

        Args:
            reg: Register name

        Returns:
            Offset of given register
        """
        supported_registers = [
            (re.compile(r"TRDC_([A-Z]+)_MDA_W(\d+)_(\d+)_DFMT(\d+)"), self._get_register_offset_mdac),
            (re.compile(r"TRDC_([A-Z]+)_MBC(\d+)_MEMN_GLBAC(\d+)"), self._get_register_offset_mbc_glbac),
            (re.compile(r"TRDC_([A-Z]+)_MBC(\d+)_DOM(\d+)_MEM(\d+)_BLK_CFG_W(\d+)"), self._get_register_offset_mbc_dom),
            (re.compile(r"TRDC_([A-Z]+)_MRC(\d+)_GLBAC(\d+)"), self._get_register_offset_mrc_glbac),
            (re.compile(r"TRDC_([A-Z]+)_MRC(\d+)_DOM(\d+)_RGD(\d+)_W(\d+)"), self._get_register_offset_mrc_dom),
        ]

        for supported_register in supported_registers:
            pattern, function = supported_register
            match = pattern.match(reg)
            if match is not None:
                return function(match)
        raise KeyError(f"Invalid TRDC register name '{reg}'")

    def get_raw_json(self) -> object:
        """Returns JSON object with raw data.

        Returns:
            JSON object with raw data
        """
        return {
            "trdc": self._id_letter,
            "name": self._name,
            "ndid": self._ndid,
            "nmbc": self._nmbc,
            "nmrc": self._nmrc,
            "nmstr": self._nmstr,
            "kpaen": self._kpaen,
            "sidsz": self._sidsz,
            "MBCs": [i.get_raw_json() for i in self._mbc if i is not None],
            "MRCs": [i.get_raw_json() for i in self._mrc if i is not None],
        }
