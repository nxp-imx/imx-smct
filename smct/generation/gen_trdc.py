#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Module for generating file config_trdc.h"""
import logging
import math
import typing
from typing import Any, Dict, List, Tuple

from smct import utils
from smct.model.model_trdc import MbcModel, MrcModel, TrdcModel
from smct.owners.owner_base import AssignedResource, ResourceOwner
from smct.resources.res_mbc import MbcResource, MbcResourceWriteType
from smct.resources.res_mdac import MdacResource
from smct.resources.res_mrc import MrcResource
from smct.resources.res_trdc import TrdcResource

from ..configuration.configuration_provider import ConfigurationProvider
from ..model.chip_model_provider import ChipModelProvider
from .generator import GenDcdInit, GeneratorBase, GenHeading
from .trdc.mbc_block import MbcBlock
from .trdc.mbc_generation_model import MbcGenerationModel
from .trdc.mrc_generation_model import MrcGenerationModel
from .trdc.mrc_region import MrcRegion

logger = logging.getLogger()


def _get_permission(trdc: TrdcModel, assigned_resource: AssignedResource) -> int:
    """Returns permission value from TRDC based on the perm attribute in the assigned resource.

    Args:
        trdc: The TRDC model to get permission value from
        assigned_resource: The assigned resource containing permission parameter

    Returns:
        The permission value as an integer
    """
    permission_string = assigned_resource.get_param_value("perm", "0")
    permission = trdc.get_perm_value(permission_string)
    return permission


def _generate_mbc_dcd_write_internal(dcd: GenDcdInit, trdc: TrdcModel, block: MbcBlock, block_id: int, permissions: List[int]) -> None:
    """Generates write for block in the MBC resource into the DCD initialization object.

    Args:
        dcd: The DCD initialization object to write to
        trdc: The TRDC model
        block: The MBC block to generate write for
        block_id: The ID of the block
        permissions: List of permissions
    """
    permission = block.get_permission()
    glbac_index = permissions.index(permission)
    blocks_in_register = int(MbcModel.register_width // MbcModel.block_size)
    word = int(block_id // blocks_in_register)
    block_index = int(block_id % blocks_in_register)
    offset = MbcModel.block_size * block_index
    register_name = block.get_register_name(word)
    # Register was not yet configured
    if register_name not in dcd:
        dcd.set_key_name(register_name, trdc.get_register_offset(register_name))
        dcd.add_key_comment(register_name, block.get_name())
        dcd[register_name] = 0
    # nse 1bit, permIndex 3bit - 4 times in register
    nse_bit = 1 if permission & 0xFF != 0 else 0
    clear_mask = ~(0xF << offset)
    data = glbac_index | nse_bit << MbcModel.nse_bit_offset
    dcd[register_name] = (dcd[register_name] & clear_mask) | (data << offset)


def _create_mrc_region(trdc: TrdcModel, mrc: MrcResource, assigned_resource: AssignedResource, did: int, permission: int) -> MrcRegion | None:
    """Creates MRC generation region from assigned resource.

    Args:
        trdc: The TRDC model
        mrc: The MRC resource
        assigned_resource: The assigned resource to create region from
        did: The domain ID
        permission: The permission value

    Returns:
        MrcRegion object if successful, None if domain ID is invalid
    """
    source = "/".join(["cfg", "mixes", trdc.get_name(), mrc.get_name()])
    extra = {"source": source}
    if assigned_resource is not None:
        validation_id = ".".join([assigned_resource.get_owner().get_id(), "RESOURCES", assigned_resource.get_resource().get_name()])
        extra["validation_id"] = validation_id
        begin = assigned_resource.get_param_value("begin")
        if begin is None:
            extra["validation_id"] = ".".join([validation_id, "BEGIN"])
            logger.error("'begin' parameter missing for '%s'", mrc.get_name(), extra=extra)
            return None
        memory_begin = begin.get_value()
        size = assigned_resource.get_param_value("size")
        if size is None:
            extra["validation_id"] = ".".join([validation_id, "SIZE"])
            logger.error("'size' parameter missing for '%s'", mrc.get_name(), extra=extra)
            return None
        memory_size = size.get_value()
        memory_end = memory_begin + memory_size
        if memory_end > 0:
            memory_end -= 1
    else:
        logger.error("Assigned resource is undefined.", extra=extra)
        return None

    if 0 < did >= trdc.get_domains_count():
        source = "/".join(["cfg", "mixes", trdc.get_name(), mrc.get_name()])
        validation_id = ".".join([assigned_resource.get_owner().get_id(), "RESOURCES", assigned_resource.get_resource().get_name()])
        logger.error("Invalid domain id %i requested for '%s'", did, mrc, extra={"source": source, "validation_id": validation_id})
        return None
    return MrcRegion(did, memory_begin, memory_end, permission)


def _create_mbc_block(trdc: TrdcModel, mbc: MbcResource, did: int, permission: int, assigned_resource: AssignedResource | None = None) -> MbcBlock | None:
    """Creates MBC block from the given parameters.

    Args:
        trdc: The TRDC model
        mbc: The MBC resource
        did: The domain ID
        permission: The permission value
        assigned_resource: The assigned resource, optional

    Returns:
        MbcBlock object if successful, None if domain ID is invalid or block range cannot be generated
    """
    block_range: tuple[int, int] | None
    source = "/".join(["cfg", "mixes", trdc.get_name(), mbc.get_name()])
    extra = {"source": source}
    if assigned_resource is not None:
        validation_id = ".".join([assigned_resource.get_owner().get_id(), "RESOURCES", assigned_resource.get_resource().get_name()])
        extra["validation_id"] = validation_id

    if 0 < did >= trdc.get_domains_count():
        logger.error("Invalid domain id %i requested for '%s'", did, mbc, extra=extra)
        return None
    if mbc.get_write_type() != MbcResourceWriteType.MEM or assigned_resource is None:
        mbc_range = mbc.get_block_range()
        block_range = mbc_range.start, mbc_range.stop
    else:
        begin = assigned_resource.get_param_value("begin")
        if begin is None:
            extra["validation_id"] = ".".join([validation_id, "BEGIN"])
            logger.error("'begin' parameter missing for '%s'", mbc.get_name(), extra=extra)
            return None
        size = assigned_resource.get_param_value("size")
        if size is None:
            extra["validation_id"] = ".".join([validation_id, "SIZE"])
            logger.error("'size' parameter missing for '%s'", mbc.get_name(), extra=extra)
            return None
        block_range = _generate_mbc_mem_range_registers(trdc, mbc, begin.get_value(), size.get_value())
        if block_range is None:
            return None

    return MbcBlock(did, mbc, block_range, permission)


def _create_default_mrc_regions(trdc: TrdcModel, mrc: MrcResource) -> List[MrcRegion]:
    """Creates MRC generation regions from default configuration of the given MRC resource.

    Args:
        trdc: The TRDC model
        mrc: The MRC resource to create default regions for

    Returns:
        List of MrcRegion objects created from default configuration
    """
    result = []
    for default_permission in mrc.get_default_permissions():
        did_begin, did_end = default_permission.get_dids()
        permission = trdc.get_perm_value(default_permission.get_permission())
        begin = default_permission.get_begin().get_value()
        end = begin + default_permission.get_size().get_value()
        if end > 0:
            end -= 1
        for did in range(did_begin, did_end + 1):
            if 0 < did >= trdc.get_domains_count():
                source = "/".join(["cfg", "mixes", trdc.get_name(), mrc.get_name()])
                logger.error("Invalid domain id %i requested for '%s'", did, mrc, extra={"source": source})
                return []
            region = MrcRegion(did, begin, end, permission)
            result.append(region)

        # Do not generate debug region if there is no access in the default assignment
        # or the debug access should not be generated
        if permission != 0 and default_permission.should_generate_debug_access():
            for debug_domain in ConfigurationProvider.get_configuration().get_all_debug_domains():
                debug_region = MrcRegion(debug_domain.get_did(), begin, end, trdc.DEBUG_DOMAIN_PERMISSION)
                result.append(debug_region)
    return result


def _create_default_mbc_blocks(trdc: TrdcModel, mbc: MbcResource) -> List[MbcBlock]:
    """Creates MBC generation blocks from default configuration of the given MBC resource.

    Args:
        trdc: The TRDC model
        mbc: The MBC resource to create default blocks for

    Returns:
        List of MbcBlock objects created from default configuration
    """
    result = []
    for default_permission in mbc.get_default_permissions():
        dids = default_permission.get_dids()
        permission = trdc.get_perm_value(default_permission.get_permission())
        did_begin, did_end = dids

        for did in range(did_begin, did_end + 1):
            if 0 < did >= trdc.get_domains_count():
                source = "/".join(["cfg", "mixes", trdc.get_name(), mbc.get_name()])
                logger.error("Invalid domain id %i requested for '%s'", did, mbc, extra={"source": source})
                return []
            block = _create_mbc_block(trdc, mbc, did, permission)
            if block is not None:
                result.append(block)

    return result


def _generate_mrc_global_access_control_registers_from_model(
    dcd: GenDcdInit, trdc: TrdcModel, mrc: MrcResource, model: MrcGenerationModel, range_start: int = 0, range_end: int = 8
) -> None:
    """Generates writes into DCD initialization object for all permissions used in given MRC generation model.

    Args:
        dcd: The DCD initialization object to write to
        trdc: The TRDC model
        mrc: The MRC resource
        model: The MRC generation model containing permissions
        range_start: Start index of permission range to generate
        range_end: End index of permission range to generate
    """
    counter = 0
    mrc_index = mrc.get_index()
    permissions = model.get_permissions()
    for permission in permissions:
        previous_counter = counter
        counter += 1
        if previous_counter < range_start or previous_counter > range_end:
            continue
        reg = f"TRDC_{trdc.get_id()}_MRC{mrc_index}_GLBAC{previous_counter}"
        register_offset = trdc.get_register_offset(reg)
        dcd.set_key_name(reg, register_offset)
        dcd.add_key_comment(reg, mrc.get_name())
        dcd.set_value_alignment_for_address(register_offset, 4)
        dcd[reg] = permission


def _generate_mbc_global_access_control_registers_from_model(
    dcd: GenDcdInit, trdc: TrdcModel, mbc_index: int, model: MbcGenerationModel, range_start: int = 0, range_end: int = 8
) -> None:
    """Generates writes into DCD initialization object for all required permissions for all MBCs in the TRDC.

    Args:
        dcd: The DCD initialization object to write to
        trdc: The TRDC model
        mbc_index: Index of the MBC
        model: The MBC generation model containing permissions
        range_start: Start index of permission range to generate
        range_end: End index of permission range to generate
    """
    counter = 0
    permissions = model.get_permissions()
    for permission in permissions:
        previous_counter = counter
        counter += 1
        if previous_counter < range_start or previous_counter > range_end:
            continue
        reg = f"TRDC_{trdc.get_id()}_MBC{mbc_index}_MEMN_GLBAC{previous_counter}"
        register_offset = trdc.get_register_offset(reg)
        dcd.set_key_name(reg, register_offset)
        dcd.set_value_alignment_for_address(register_offset, 4)
        dcd[reg] = permission


def _generate_mbc_model(dcd: GenDcdInit, trdc: TrdcModel, mbc_index: int, model: MbcGenerationModel) -> None:
    """Generates all MBC resources writes into the DCD initialization object.

    Args:
        dcd: The DCD initialization object to write to
        trdc: The TRDC model
        mbc_index: Index of the MBC
        model: The MBC generation model containing blocks to generate
    """
    mbc_model = trdc.get_mbc(mbc_index)
    if mbc_model is None:
        logger.error("MBC model for MBC%i is not known", mbc_index)
        return
    permissions = model.get_permissions()
    blocks_dictionary = model.get_blocks()
    for domain in blocks_dictionary:
        for block in blocks_dictionary[domain]:
            start_block, end_block = block.get_block_range()
            for block_index in range(start_block, end_block):
                _generate_mbc_dcd_write_internal(dcd, trdc, block, block_index, permissions)


def _generate_mrc_model(dcd: GenDcdInit, trdc: TrdcModel, mrc: MrcResource, model: MrcGenerationModel) -> None:
    """Generates writes into DCD initialization object from given MRC generation model.

    Args:
        dcd: The DCD initialization object to write to
        trdc: The TRDC model
        mrc: The MRC resource
        model: The MRC generation model containing regions to generate
    """
    mrc_index = mrc.get_index()
    mrc_model = trdc.get_mrc(mrc_index)
    if mrc_model is None:
        logger.error("MRC model for MRC%i is not known", mrc_index)
        return
    address_bit_offset = mrc_model.get_model_region_offset()
    # 31-14/10 address
    # W0: 2-0 permission index
    # W1: 4 nse, 0 vld

    permissions = model.get_permissions()

    regions_dictionary = model.get_regions()
    for domain in regions_dictionary:
        region_counter = 0
        for region in regions_dictionary[domain]:
            permission = region.get_permission()
            start_register = mrc.get_start_register_name(region.get_domain(), region_counter)
            end_register = mrc.get_end_register_name(region.get_domain(), region_counter)
            block_begin = region.get_start_address() >> MrcModel.strt_addr_offset
            block_end = region.get_end_address() >> MrcModel.end_addr_offset
            vld = 1

            data_start = 0
            data_end = 0

            if region.is_clearing():
                block_end = 0
            else:
                permission_index = permissions.index(permission)
                nse_bit = 1 if permission & 0xFF != 0 else 0
                if block_end != 0:  # Generate the start only if end is not zero (taken from legacy CLI app)
                    data_start = block_begin << address_bit_offset | permission_index
                data_end = block_end << address_bit_offset | nse_bit << 4 | vld

            if block_end != 0:  # Generate the start only if end is not zero (taken from legacy CLI app)
                dcd.set_key_name(start_register, trdc.get_register_offset(start_register))
                dcd.add_key_comment(start_register, mrc.get_name())
                dcd[start_register] = data_start

            dcd.set_key_name(end_register, trdc.get_register_offset(end_register))
            dcd.add_key_comment(end_register, mrc.get_name())
            dcd[end_register] = data_end

            region_counter += 1


def _process_mbc_assignments(
    dcd: GenDcdInit, trdc: TrdcModel, resources: Dict[str, Dict[TrdcResource, List[AssignedResource]]]
) -> Dict[int, MbcGenerationModel]:
    """Processes MBC assignments and generates MBC configuration.

    Args:
        dcd: The DCD initialization object to write to
        trdc: The TRDC model
        resources: Dictionary of resources organized by type

    Returns:
        Dictionary mapping MBC indices to their generation models
    """
    mbc_generation_models: Dict[int, MbcGenerationModel] = {}
    # Default configuration assignments
    default_assignments = ConfigurationProvider.get_configuration().get_all_default_mbc_assignments(trdc)
    for default_assignment in default_assignments:
        mbc, _ = default_assignment
        mbc_index = mbc.get_index()
        trdc_mbc_model = trdc.get_mbc(mbc_index)
        if trdc_mbc_model is None:
            logger.error("MBC model for MBC%i is not known", mbc_index)
            continue
        mbc_generation_model = mbc_generation_models.setdefault(mbc_index, MbcGenerationModel())
        for default_block in _create_default_mbc_blocks(trdc, mbc):
            if default_block is not None:
                mbc_generation_model.add_block(default_block)

    if len(resources["MBC"]) > 0:
        # User configuration assignments
        for trdc_resource in resources["MBC"]:
            mbc = typing.cast(MbcResource, trdc_resource)
            mbc_index = mbc.get_index()
            trdc_mbc_model = trdc.get_mbc(mbc_index)
            if trdc_mbc_model is None:
                logger.error("MBC model for MBC%i is not known", mbc_index)
                continue
            mbc_generation_model = mbc_generation_models.setdefault(mbc_index, MbcGenerationModel())
            for assigned_resource in resources["MBC"][trdc_resource]:
                block = _create_mbc_block(trdc, mbc, assigned_resource.get_owner().get_did(), _get_permission(trdc, assigned_resource), assigned_resource)
                if block is not None:
                    mbc_generation_model.add_block(block)
                for debug_domain in ConfigurationProvider.get_configuration().get_all_debug_domains():
                    debug_block = _create_mbc_block(trdc, mbc, debug_domain.get_did(), trdc.DEBUG_DOMAIN_PERMISSION)
                    if debug_block is not None:
                        mbc_generation_model.add_block(debug_block)

    mbcs_to_be_generated = []
    # Add default configuration
    for assignment in ConfigurationProvider.get_configuration().get_all_default_mbc_assignments(trdc):
        mbc, _ = assignment
        if mbc.get_index() not in mbcs_to_be_generated:
            mbcs_to_be_generated.append(mbc.get_index())

    # Add user configuration
    for trdc_resource in resources["MBC"]:
        mbc = typing.cast(MbcResource, trdc_resource)
        if mbc.get_index() not in mbcs_to_be_generated:
            mbcs_to_be_generated.append(mbc.get_index())

    for mbc_index in mbcs_to_be_generated:
        mbc_model = mbc_generation_models[mbc_index]
        _generate_mbc_model(dcd, trdc, mbc_index, mbc_model)
        _generate_mbc_global_access_control_registers_from_model(dcd, trdc, mbc_index, mbc_model, 1, 7)

    return mbc_generation_models


def _process_mrc_assignments(
    dcd: GenDcdInit, trdc: TrdcModel, resources: Dict[str, Dict[TrdcResource, List[AssignedResource]]]
) -> Dict[int, MrcGenerationModel]:
    """Processes MRC assignments and generates MRC configuration.

    Args:
        dcd: The DCD initialization object to write to
        trdc: The TRDC model
        resources: Dictionary of resources organized by type

    Returns:
        Dictionary mapping MRC indices to their generation models
    """
    mrc_generation_models: Dict[int, MrcGenerationModel] = {}
    # Create MRC regions from default configuration
    for assignment in ConfigurationProvider.get_configuration().get_all_default_mrc_assignments(trdc):
        mrc, _ = assignment
        mrc_index = mrc.get_index()
        trdc_mrc_model = trdc.get_mrc(mrc_index)
        if trdc_mrc_model is None:
            source = "/".join(["cfg", "mixes", trdc.get_name(), mrc.get_name()])
            logger.error("MRC model for MRC%i in TRDC %s is not known", mrc_index, trdc.get_id(), extra={"source": source})
            continue
        mrc_generation_model = mrc_generation_models.setdefault(mrc_index, MrcGenerationModel(trdc_mrc_model.get_model_number_of_regions()))
        for default_region in _create_default_mrc_regions(trdc, mrc):
            if default_region is not None:
                mrc_generation_model.add_region(default_region)

    # Create MRC regions from user configuration
    for trdc_resource in resources["MRC"]:
        mrc = typing.cast(MrcResource, trdc_resource)
        mrc_index = mrc.get_index()
        trdc_mrc_model = trdc.get_mrc(mrc_index)
        if trdc_mrc_model is None:
            source = "/".join(["cfg", "mixes", trdc.get_name(), mrc.get_name()])
            logger.error("MRC model for MRC%i in TRDC %s is not known", mrc_index, trdc.get_id(), extra={"source": source})
            continue
        mrc_generation_model = mrc_generation_models.setdefault(mrc_index, MrcGenerationModel(trdc_mrc_model.get_model_number_of_regions()))
        for assigned_resource in resources["MRC"][trdc_resource]:

            region = _create_mrc_region(trdc, mrc, assigned_resource, assigned_resource.get_owner().get_did(), _get_permission(trdc, assigned_resource))
            if region is not None:
                mrc_generation_model.add_region(region)

            if assigned_resource.should_generate_debug():
                for debug_domain in ConfigurationProvider.get_configuration().get_all_debug_domains():
                    region = _create_mrc_region(trdc, mrc, assigned_resource, debug_domain.get_did(), trdc.DEBUG_DOMAIN_PERMISSION)
                    if region is not None:
                        mrc_generation_model.add_region(region)

    mrcs_to_be_generated = []
    # Add default configuration
    for assignment in ConfigurationProvider.get_configuration().get_all_default_mrc_assignments(trdc):
        mrc, _ = assignment
        if mrc not in mrcs_to_be_generated:
            mrcs_to_be_generated.append(mrc)

    # Add user configuration
    for trdc_resource in resources["MRC"]:
        mrc = typing.cast(MrcResource, trdc_resource)
        if mrc not in mrcs_to_be_generated:
            mrcs_to_be_generated.append(mrc)

    # Generate configuration of all MRCs
    for mrc in mrcs_to_be_generated:
        mrc_model = mrc_generation_models[mrc.get_index()]
        mrc_model.remove_unnecessary_regions()
        mrc_model.sort_regions()

        mrc_model.generate_clearing()
        if mrc.get_clr() > MrcGenerationModel.DEFAULT_CLEARING:
            for assigned_resource in resources["MRC"][trdc_resource]:
                if "clr" in assigned_resource.get_params():
                    did = assigned_resource.get_owner().get_did()
                    clr = assigned_resource.get_param_value_int("clr", MrcGenerationModel.DEFAULT_CLEARING)
                    mrc_model.generate_clearing_in_domain(did, clr)
                    if assigned_resource.should_generate_debug():
                        for debug_domain in ConfigurationProvider.get_configuration().get_all_debug_domains():
                            mrc_model.generate_clearing_in_domain(debug_domain.get_did(), clr)
        _generate_mrc_model(dcd, trdc, mrc, mrc_model)
        _generate_mrc_global_access_control_registers_from_model(dcd, trdc, mrc, mrc_model, 1, 7)

    return mrc_generation_models


def _generate_mbc_mem_range_registers(trdc: TrdcModel, mbc: MbcResource, begin: int, size: int) -> Tuple[int, int] | None:
    """Generates permission assignment in part of MEM in MBC for memory space protection.

    Args:
        trdc: The TRDC model
        mbc: The MBC resource
        begin: Start address of the memory range
        size: Size of the memory range

    Returns:
        Tuple of (start_block, end_block) indices if successful, None if MBC model not found or size exceeds available blocks
    """
    mbc_model = trdc.get_mbc(mbc.get_index())
    if mbc_model is None:
        logger.error("MBC%s model in TRDC %s was not found and resource assignment cannot be generated", mbc.get_index(), trdc.get_id())
        return None
    mem_model = mbc_model.get_model_mem(mbc.get_mem())
    if mem_model is None:
        logger.error("MBC%s MEM%s model in TRDC %s was not found and resource assignment cannot be generated", mbc.get_index(), mbc.get_mem(), trdc.get_id())
        return None
    origin = mem_model.get_origin().get_value()
    block_size = mem_model.get_block_size().get_value()
    start = begin - origin
    start_block = int(math.ceil(start / block_size))
    block_count = int(math.ceil(size / block_size))
    total_block_count = mem_model.get_block_count()
    end_block_index = start_block + block_count
    if end_block_index > total_block_count:
        logger.error(
            "Size of %s blocks (%s B) is bigger than %s (%s B) blocks available in the MEM%s of MBC%s in TRDC %s",
            end_block_index,
            size,
            total_block_count,
            total_block_count * block_size,
            mbc.get_index(),
            mbc.get_mem(),
            trdc.get_id(),
        )
    return start_block, start_block + block_count


def _generate_mdac_registers(dcd: GenDcdInit, trdc: TrdcModel, mdac: MdacResource, assigned_resource: AssignedResource) -> None:
    """Generates all MDAC register writes into the DCD initialization object.

    Args:
        dcd: The DCD initialization object to write to
        trdc: The TRDC model
        mdac: The MDAC resource
        assigned_resource: The assigned resource containing MDAC configuration
    """
    owner: ResourceOwner = assigned_resource.get_owner()

    did = owner.get_did()
    mdid = assigned_resource.get_param_value("mdid")
    if mdid is not None:
        if mdid == "none":
            return
        if isinstance(mdid, int):
            mdid_int = typing.cast(int, mdid)
            did = mdid_int
        if isinstance(mdid, str):
            mdid_int = utils.parse_int(mdid)
            did = mdid_int

    source = "/".join(["user_config", owner.get_name(), "assigned_resources", mdac.get_name()])
    validation_id = ".".join([owner.get_id(), "RESOURCES", mdac.get_name()])
    if did < 0 or did >= trdc.get_domains_count():
        logger.error("Invalid domain ID of '%s'", owner.get_id(), extra={"source": source, "validation_id": validation_id})
        return

    pa = assigned_resource.get_param_value("pa", "bypass")
    if pa not in TrdcModel.pa_types:
        logger.error("'%s' uses %s with unknown 'pa' value %s", owner.get_id(), mdac.get_name(), pa, extra={"source": source, "validation_id": validation_id})
        return
    pa = TrdcModel.pa_types[pa]

    sa = assigned_resource.get_param_value("sa", "bypass")
    if sa not in TrdcModel.sa_types:
        logger.error("'%s' uses %s with unknown 'sa' value %s", owner.get_id(), mdac.get_name(), pa, extra={"source": source})
        return
    sa = TrdcModel.sa_types[sa]

    vld = 1
    sid = assigned_resource.get_param_value_int("sid", 0)
    if sid >= 2 ** trdc.get_sidsz():
        logger.error(
            "'%s' uses %s with with 'sid' value %s greater that 'sidsz=%i' ", owner.get_id(), mdac.get_name(), sid, trdc.get_sidsz(), extra={"source": source}
        )
        return
    kpa_default = 0 if sid != 0 else 1
    kpa = assigned_resource.get_param_value_int("kpa", kpa_default)
    if trdc.get_kpaen() == 0 and assigned_resource.get_param_value("kpa", default=None) is not None:
        logger.error("'%s' uses %s with with 'kpa' value %s while 'kpa' is disabled", owner.get_id(), mdac.get_name(), kpa, extra={"source": source})
        return

    if mdac.is_core():
        dfmt = 0
        data = (
            sa << TrdcModel.DFMT0_register["SA"]["offset"]
            | vld << TrdcModel.DFMT0_register["VLD"]["offset"]
            | dfmt << TrdcModel.DFMT0_register["DFMT"]["offset"]
            | did << TrdcModel.DFMT0_register["DID"]["offset"]
        )
        if trdc.get_kpaen():
            data |= kpa << TrdcModel.DFMT0_register["KPA"]["offset"]
        if trdc.get_sidsz() > 0:
            data |= sid << TrdcModel.DFMT0_register["SID"]["offset"]
    else:
        dfmt = 1
        data = (
            sa << TrdcModel.DFMT1_register["SA"]["offset"]
            | pa << TrdcModel.DFMT1_register["PA"]["offset"]
            | vld << TrdcModel.DFMT1_register["VLD"]["offset"]
            | dfmt << TrdcModel.DFMT1_register["DFMT"]["offset"]
            | did << TrdcModel.DFMT1_register["DID"]["offset"]
        )
        if trdc.get_kpaen():
            data |= kpa << TrdcModel.DFMT1_register["KPA"]["offset"]
        if trdc.get_sidsz() > 0:
            data |= sid << TrdcModel.DFMT1_register["SID"]["offset"]

    for r in range(mdac.get_register(), mdac.get_register() + mdac.get_registers_count()):
        reg = f"TRDC_{trdc.get_id()}_MDA_W{r}_{mdac.get_master()}_DFMT{dfmt}"
        if reg in dcd:
            if dcd[reg] != data:
                logger.error(
                    "The %s generates %s=%s for %s, but it is already defined as %s by someone else.",
                    trdc.get_name(),
                    reg,
                    utils.convert_to_hex(data),
                    mdac.get_name(),
                    utils.convert_to_hex(dcd[reg]),
                )
        else:
            # first time we set the register, calculate its offset, the DCD will use it internally
            dcd.set_key_name(reg, trdc.get_register_offset(reg))

        dcd[reg] = data
        dcd.add_key_comment(reg, f"{mdac.get_name()}/{assigned_resource.get_owner().get_name()}")


class GeneratorTRDC(GeneratorBase):
    """Generator of config_trdc.h"""

    def _get_generator_info(self) -> Dict[str, Any]:
        """Returns information about this generator.

        Returns:
            Dict[str, Any]: Dictionary containing the generator name and required includes.
        """
        return {"name": "TRDC", "incl": ["config_user.h"]}

    def _generate_trdc_configuration(self, trdc: TrdcModel, assigned_resources: List[AssignedResource]) -> None:
        """Generates the configuration for given TRDC.

        Args:
            trdc (TrdcModel): The TRDC model to generate configuration for.
            assigned_resources (List[AssignedResource]): List of assigned resources for the TRDC.
        """
        self.print_generator(GenHeading(f"TRDC {trdc.get_id()} Config"))
        dcd = GenDcdInit(f"SM_{trdc.get_name()}_CONFIG", f"Config for TRDC {trdc.get_id()}")
        dcd.set_sort(False)

        resources: Dict[str, Dict[TrdcResource, List[AssignedResource]]] = {
            "MDAC": {},
            "MBC": {},
            "MRC": {},
        }
        for assigned_resource in assigned_resources:
            for trdc_resource in assigned_resource.get_trdc_resources():
                trdc_of_resource = ChipModelProvider.get_model().get_trdc(trdc_resource.get_trdc_id())
                if trdc_of_resource is not trdc:  # Ignore resources that configure different TRDC instance
                    continue
                if isinstance(trdc_resource, MdacResource):
                    if trdc_resource not in resources["MDAC"]:
                        resources["MDAC"][trdc_resource] = []
                    resources["MDAC"][trdc_resource].append(assigned_resource)
                elif isinstance(trdc_resource, MbcResource):
                    if trdc_resource not in resources["MBC"]:
                        resources["MBC"][trdc_resource] = []
                    resources["MBC"][trdc_resource].append(assigned_resource)
                elif isinstance(trdc_resource, MrcResource):
                    if trdc_resource not in resources["MRC"]:
                        resources["MRC"][trdc_resource] = []
                    resources["MRC"][trdc_resource].append(assigned_resource)

        # walk over all MDACs
        for trdc_resource in resources["MDAC"]:
            mdac = typing.cast(MdacResource, trdc_resource)
            for assigned_resource in resources["MDAC"][trdc_resource]:
                _generate_mdac_registers(dcd, trdc, mdac, assigned_resource)

        mbc_generation_models = _process_mbc_assignments(dcd, trdc, resources)
        mrc_generation_models = _process_mrc_assignments(dcd, trdc, resources)

        dcd.sort_keys()

        # Generate the GLBAC0 writes at the end to mimic legacy CLI application
        if len(resources["MBC"]) > 0:
            mbc_resources = typing.cast(List[MbcResource], resources["MBC"])
            ordered_mbcs = sorted(mbc_resources, key=lambda mbc_resource: mbc_resource.get_index())
            for trdc_resource in ordered_mbcs:
                mbc = typing.cast(MbcResource, trdc_resource)
                _generate_mbc_global_access_control_registers_from_model(dcd, trdc, mbc.get_index(), mbc_generation_models[mbc.get_index()], 0, 0)
        if len(resources["MRC"]) > 0:
            mrc_resources = typing.cast(List[MrcResource], resources["MRC"])
            ordered_mrcs = sorted(mrc_resources, key=lambda mrc_resource: mrc_resource.get_index())
            for trdc_resource in ordered_mrcs:
                mrc = typing.cast(MrcResource, trdc_resource)
                _generate_mrc_global_access_control_registers_from_model(dcd, trdc, mrc, mrc_generation_models[mrc.get_index()], 0, 0)

        dcd[0x00000000] = 0x0000C001  # This turns on the TRDC and must be generated last
        self.print_generator(dcd)

    def _get_doxygen_file_name(self) -> str:
        """Returns the doxygen file name.

        Returns:
            str: Empty string for doxygen file name.
        """
        return ""

    def _get_doxygen_brief_lines(self) -> List[str]:
        """Returns the doxygen brief description lines.

        Returns:
            List[str]: List of brief description lines for doxygen documentation.
        """
        return ["", "", " Header file containing configuration info for the TRDC SM abstraction."]

    def print_content(self) -> None:
        """Prints the TRDC configuration content for all TRDCs."""
        all_trdc_assignments = self._get_configuration().get_all_trdc_assignments()
        for trdc in sorted(ChipModelProvider.get_model().get_all_trdcs()):
            try:
                trdc_assignments = all_trdc_assignments[trdc]
            except KeyError:
                source = "/".join(["cfg", "mixes", trdc.get_name()])
                logger.info("TRDC '%s' has no assignments", trdc.get_id(), extra={"source": source})
                continue
            self._generate_trdc_configuration(trdc, trdc_assignments)

    def __str__(self) -> str:
        """Returns string representation of the generator.

        Returns:
            str: String representation of the TRDC generator.
        """
        return "TRDC generator"
