#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Module related to parser of the CFG files"""
import logging
import re
from typing import Any, Dict, List

from smct import utils
from smct.resources.res_bctrl import BctrlResource, BctrlResourceIpgDebug
from smct.resources.res_mbc import MbcResource
from smct.resources.res_mdac import MdacResource
from smct.resources.res_mrc import MrcResource
from smct.resources.resource_base import AtomicResource

from ..model.chip_model_provider import ChipModelProvider
from ..resources.resource_database_provider import ResourceDatabaseProvider
from ..utils import FormatedInt, UInt64Constraints

logger = logging.getLogger()

_re__bctrl_a_ipg_debug = re.compile(r"\bBCTRL_(\w)_IPG_DEBUG(_(\d+))?=((0x[0-9A-Fa-f]+)|(0b[0-1]+)|(\d+))")
# MDAC_am=r1-r2 - TRDC a, MDA_Wr_m, m is the master, r is register range r1-r2 (e.g. MDAC_N0C=0-3)
_re_MDAC_am_range = re.compile(r"MDAC_(\w)(\d+)(\w?)=(\d+)-(\d+)")
# MDAC_am=r - TRDC a, MDA_Wr_m, m is the master, r is register
_re_MDAC_am_one = re.compile(
    r"MDAC_(\w)(\d+)(\w?)=(\d+)",
)
# MBC_am=s.b - TRDC a, MBCm_MEMs, m is the MBC instance, s is the memory,
# and b is the block range b1-b2 (e.g. MBC_D0=2.0-63)
_re_MBC_am_blkrange = re.compile(r"MBC_(\w)(\d+)=(\d+)\.(\d+)-(\d+)")
# MBC_am=s.b - TRDC a, MBCm_MEMs, m is the MBC instance, s is the memory, and b is the block (e.g. MBC_D0=0.12)
_re_MBC_am_blk = re.compile(r"MBC_(\w)(\d+)=(\d+)\.(\d+)")
# MBC_am=s.b - TRDC a, MBCm_MEMs, m is the MBC instance, s is the memory, and b is the block (e.g. MBC_N2=0)
_re_MBC_am_mem = re.compile(r"MBC_(\w)(\d+)=(\d+)")
_re_MRC_am = re.compile(r"MRC_(\w)(\d+)=(\d+)")  # MRC_am=0 - TRDC a, MRCm, m is the MRC instance (e.g. MRC_W2=0)


class CfgResourceProvider:
    """Provider for the resources parsed from CFG file"""

    @classmethod
    def atomic_resource_from_cfg_name(cls, name: str, outer_name: str, outer_all_atoms: List[str]) -> AtomicResource | None:
        """Auto-infer atomic resource from name used in .cfg file"""
        factories = {
            (re.compile("^MBC_"), _mbc_resource_from_cfg_name),
            (re.compile("^MRC_"), _rrc_resource_from_cfg_name),
            (re.compile("^MDAC_"), _mdac_resource_from_cfg_name),
            (re.compile("^BCTRL"), _bctrl_resource_from_cfg_name),
        }
        for factory in factories:
            if factory[0].match(name):
                return factory[1](name, outer_name, outer_all_atoms)
        return None


def _mdac_get_raw_range(match_object: re.Match) -> Dict[str, Any]:
    """Creates dictionary with information about MDAC range.

    Args:
        match_object: Regular expression match object containing MDAC range information

    Returns:
        Dictionary containing MDAC range configuration data
    """
    mdac = {}
    mdac["trdc"] = match_object.group(1)
    mdac["master"] = int(match_object.group(2))
    mdac["core"] = 1 if match_object.group(3).lower() == "c" else 0  # todo: this information shall rather go to MdacModel ??
    r1 = int(match_object.group(4))
    r2 = int(match_object.group(5))
    mdac["reg"] = r1
    mdac["rcnt"] = r2 - r1 + 1
    return mdac


def _mdac_get_raw_one(match_object: re.Match) -> Dict[str, Any]:
    """Creates dictionary with information about one MDAC.

    Args:
        match_object: Regular expression match object containing single MDAC information

    Returns:
        Dictionary containing single MDAC configuration data
    """
    mdac = {}
    mdac["trdc"] = match_object.group(1)
    mdac["master"] = int(match_object.group(2))
    mdac["core"] = 1 if match_object.group(3).lower() == "c" else 0  # todo: this information shall rather go to MdacModel ??
    mdac["reg"] = int(match_object.group(4))
    return mdac


def _mdac_guess_nice_name(_: str, outer_name: str) -> str:
    """Returns correct name of the MDAC resource.

    Args:
        _: Original name (unused)
        outer_name: Outer name to use for generating the nice name

    Returns:
        Formatted MDAC resource name
    """
    return f"MDAC_{outer_name}"


def _mdac_resource_from_cfg_name(name: str, outer_name: str, _: List[str]) -> MdacResource | None:
    """Creates MDAC resource from the raw information in cfg file. Supports both one MDAC and MDAC range.

    Args:
        name: Raw name from cfg file
        outer_name: Outer name for resource naming
        _: List of atoms (unused)

    Returns:
        MdacResource instance if successfully created, None otherwise
    """
    formats = [
        (_re_MDAC_am_range, _mdac_get_raw_range),
        (_re_MDAC_am_one, _mdac_get_raw_one),
    ]

    res = None
    for f in formats:
        m = f[0].match(name)
        if m:
            raw = {
                "name": _mdac_guess_nice_name(name, outer_name),
                "desc": name,
                "type": "MDAC",
            } | f[
                1
            ](m)
            res = MdacResource(raw)
            break
    return res


def _mrc_get_raw(match_object: re.Match) -> Dict[str, Any]:
    """Returns dictionary with raw information about MRC.

    Args:
        match_object: Regular expression match object containing MRC information

    Returns:
        Dictionary containing MRC configuration data
    """
    return {"trdc": match_object.group(1), "mrc": int(match_object.group(2))}


def _mrc_guess_nice_name(_: str, outer_name: str) -> str:
    """Returns correct name of the MRC resource.

    Args:
        _: Original name (unused)
        outer_name: Outer name to use for generating the nice name

    Returns:
        Formatted MRC resource name
    """
    return f"MRC_{outer_name}"


def _rrc_resource_from_cfg_name(name: str, outer_name: str, outer_atoms: List[str]) -> MrcResource | None:
    """Creates MRC resource from the raw information in cfg file.

    Args:
        name: Raw name from cfg file
        outer_name: Outer name for resource naming
        outer_atoms: List of atoms containing additional parameters

    Returns:
        MrcResource instance if successfully created, None otherwise
    """
    res = None
    m = _re_MRC_am.match(name)
    if m:
        raw = {
            "name": _mrc_guess_nice_name(name, outer_name),
            "desc": name,
            "type": "MRC",
        } | _mrc_get_raw(m)
        res = MrcResource(raw)

        # the MRC resource definition also comes with nrgns option describing the MRC model / mixing data
        # and model definition :(
        trdc = ChipModelProvider.get_model().get_trdc(res.get_trdc_id())
        if trdc is not None:
            mrc = trdc.get_mrc(res.get_index())
            if mrc:
                number_of_regions = utils.get_attribute_value_from_list(outer_atoms, "nrgns", remove=True)
                if number_of_regions:
                    mrc.set_model_number_of_regions(int(number_of_regions))
                big = utils.get_attribute_value_from_list(outer_atoms, "big")
                if big:
                    mrc.set_model_region_offset(10 if int(big) == 1 else 14)
    return res


def _mbc_get_raw_block_range(match_object: re.Match) -> Dict[str, Any]:
    """Creates dictionary with information about MBC block range.

    Args:
        match_object: Regular expression match object containing MBC block range information

    Returns:
        Dictionary containing MBC block range configuration data
    """
    mbc = {"trdc": match_object.group(1), "mbc": int(match_object.group(2)), "mem": int(match_object.group(3))}
    b0 = int(match_object.group(4))
    b1 = int(match_object.group(5))
    mbc["blk"] = b0
    mbc["bcnt"] = b1 - b0 + 1
    mbc["write_type"] = "range"
    return mbc


def _mbc_get_raw_block(match_object: re.Match) -> Dict[str, Any]:
    """Creates dictionary with information about one MBC block.

    Args:
        match_object: Regular expression match object containing single MBC block information

    Returns:
        Dictionary containing single MBC block configuration data
    """
    return {
        "trdc": match_object.group(1),
        "mbc": int(match_object.group(2)),
        "mem": int(match_object.group(3)),
        "blk": int(match_object.group(4)),
        "write_type": "block",
    }


def _mbc_get_raw_mem(match_object: re.Match) -> Dict[str, Any]:
    """Creates dictionary with information about entire MEM block in MBC.

    Args:
        match_object: Regular expression match object containing MBC memory information

    Returns:
        Dictionary containing MBC memory configuration data
    """
    return {"trdc": match_object.group(1), "mbc": int(match_object.group(2)), "mem": int(match_object.group(3)), "write_type": "mem"}


def _mbc_guess_nice_name(_: str, outer_name: str) -> str:
    """Returns correct name of the MBC resource.

    Args:
        _: Original name (unused)
        outer_name: Outer name to use for generating the nice name

    Returns:
        Formatted MBC resource name
    """
    name = f"MBC_{outer_name}"
    if len(ResourceDatabaseProvider.get_database().find_atomic_resource_by("name", name)) > 0:
        pass
    return name


def _mbc_resource_from_cfg_name(name: str, outer_name: str, outer_atoms: List[str]) -> MbcResource | None:
    """Creates the MBC resource from the raw information in cfg file.

    Args:
        name: Raw name from cfg file
        outer_name: Outer name for resource naming
        outer_atoms: List of atoms containing additional parameters

    Returns:
        MbcResource instance if successfully created, None otherwise
    """
    supported_formats = [
        (_re_MBC_am_blkrange, _mbc_get_raw_block_range),
        (_re_MBC_am_blk, _mbc_get_raw_block),
        (_re_MBC_am_mem, _mbc_get_raw_mem),
    ]

    res = None
    for supported_format in supported_formats:
        match_object = supported_format[0].match(name)
        if match_object:
            raw = {
                "name": _mbc_guess_nice_name(name, outer_name),
                "desc": name,
                "type": "MBC",
            } | supported_format[
                1
            ](match_object)
            res = MbcResource(raw)

            # the MBC resource definition also comes with option describing the MBC model / mixing data
            # and model definition :(
            trdc = ChipModelProvider.get_model().get_trdc(res.get_trdc_id())
            if trdc is not None:
                mbc = trdc.get_mbc(res.get_index())
                if mbc:
                    # Do not remove attributes from the list as there might be second resource of the same type
                    origin_parameter = utils.get_attribute_value_from_list(outer_atoms, "origin")
                    number_of_blocks_parameter = utils.get_attribute_value_from_list(outer_atoms, "nblks")
                    block_size_parameter = utils.get_attribute_value_from_list(outer_atoms, "blksize")
                    if origin_parameter and number_of_blocks_parameter and block_size_parameter:
                        origin = FormatedInt(origin_parameter)
                        if origin.get_value() > UInt64Constraints.MAX_VALUE:
                            source = "/".join(["cfg", trdc.get_name(), raw["name"], "MEM", str(raw["mem"]), "ORIGIN"])
                            logger.error("Origin address %s exceeds maximum 64-bit value.", origin, extra={"source": source})
                            origin = FormatedInt(UInt64Constraints.DEFAULT_VALUE)
                        number_of_blocks = utils.parse_int(number_of_blocks_parameter)
                        block_size = FormatedInt(block_size_parameter)
                        mbc.set_model_mem(res.get_mem(), origin, number_of_blocks, block_size)
            # skip other formats
            break
    return res


def _bctrl_guess_nice_name_ipg_debug(_: str, outer_name: str, m: re.Match) -> str:
    """Returns correct name of the block control IPG debug resource.

    Args:
        _: Original name (unused)
        outer_name: Outer name to use for generating the nice name
        m: Regular expression match object containing IPG debug information

    Returns:
        Formatted block control IPG debug resource name
    """
    regn = m.group(2) if m.group(2) else ""
    return f"BCTRL_{m.group(1)}_IPG_DEBUG{regn}_{outer_name}"


def _bctrl_get_raw_ipg_debug(m: re.Match) -> Dict[str, Any]:
    """Creates dictionary with raw information about IPG debug resource.

    Args:
        m: Regular expression match object containing IPG debug information

    Returns:
        Dictionary containing IPG debug configuration data
    """
    return {
        "bctrl": m.group(1),
        "regn": (int(m.group(3)) - 1) if m.group(3) else 0,
        "mask": (m.group(5)) if m.group(5) else (m.group(6) if m.group(6) else m.group(7)),
    }


def _bctrl_resource_from_cfg_name_ipg_debug(name: str, outer_name: str, _: List[str]) -> BctrlResourceIpgDebug | None:
    """Creates IPG debug resource from raw information in cfg file.

    Args:
        name: Raw name from cfg file
        outer_name: Outer name for resource naming
        _: List of atoms (unused)

    Returns:
        BctrlResourceIpgDebug instance if successfully created, None otherwise
    """
    supported_formats = [
        (_re__bctrl_a_ipg_debug, _bctrl_get_raw_ipg_debug),
    ]

    res = None
    for supported_format in supported_formats:
        match_object = supported_format[0].match(name)
        if match_object:
            raw = {
                "name": _bctrl_guess_nice_name_ipg_debug(name, outer_name, match_object),
                "desc": name,
                "type": "BCTRL_IPG_DEBUG",
            } | supported_format[
                1
            ](match_object)
            res = BctrlResourceIpgDebug(raw)
            break

    return res


def _bctrl_resource_from_cfg_name(name: str, outer_name: str, outer_atoms: List[str]) -> BctrlResource | None:
    """Creates IPG debug resource from raw information in cfg file.

    Args:
        name: Raw name from cfg file
        outer_name: Outer name for resource naming
        outer_atoms: List of atoms containing additional parameters

    Returns:
        BctrlResource instance if successfully created, None otherwise
    """
    res = _bctrl_resource_from_cfg_name_ipg_debug(name, outer_name, outer_atoms)
    # can add more BCTRL register types in future
    return res
