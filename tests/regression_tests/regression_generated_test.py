#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause

"""Regression tests for generated configurations."""

import math
import os.path
import typing
from random import random
from tempfile import TemporaryDirectory
from typing import Any, Dict, List, Tuple

import pytest

from smct import utils
from smct.configuration.configuration_provider import ConfigurationProvider
from smct.model.chip_model_provider import ChipModelProvider
from smct.parsers.cfg_parser import CfgFileParser
from smct.parsers.hdr_parser import ApiResourceParser
from smct.parsers.resource_parser import ResourceParser
from smct.resources.res_api import ApiResource
from smct.resources.res_mbc import MbcResource, MbcResourceWriteType
from smct.resources.res_mdac import MdacResource
from smct.resources.res_mrc import MrcResource
from smct.resources.resource_base import MacroResource
from smct.resources.resource_database_provider import ResourceDatabaseProvider
from tests.test_utils import execute_binary, execute_cli, get_smct_root
from tests.utils.cfg_file_generator import (
    AccessRight,
    Agent,
    AssignedResource,
    CfgFileGenerator,
    Channel,
    Configuration,
    LogicalMachine,
    Mailbox,
    Mode,
    StartStop,
)
from tests.utils.file_diff import FileDiffer

TEST_BOARDS: Dict[str, List[str]] = {"MIMX95": ["mcimx95evk"]}


def _generate_default_access_templates() -> List[AccessRight]:
    """Generate default access right templates.
    
    Returns:
        List of default AccessRight objects
    """
    return [
        AccessRight("NOTIFY", {"api": "notify"}),
        AccessRight("GET", {"api": "get"}),
        AccessRight("SET", {"api": "set"}),
        AccessRight("PRIV", {"api": "priv"}),
        AccessRight("ALL", {"api": "all"}),
        AccessRight("READONLY", {"perm": "ro"}),
    ]


def _flatten_board_dict(input_dict: Dict[str, List[str]]) -> List[Tuple[str, str]]:
    """Flattens the dictionary to list of tuples where dictionary key may be present multiple times"""
    return [(k, v) for k, v_list in input_dict.items() for v in v_list]


def _get_lms_limit(device: str) -> int:
    """Get the maximum number of logical machines for a device.
    
    Args:
        device: Device name
        
    Returns:
        Maximum number of logical machines
    """
    if device == "MIMX95":
        return 3
    return 1


def _get_trdc_domains_limit(device: str) -> int:
    """Get the maximum number of TRDC domains for a device.
    
    Args:
        device: Device name
        
    Returns:
        Maximum number of TRDC domains
    """
    return 16


# def _get_sm_lm_config(access_templates: List[AccessRight], assigned_resources: List[AssignedResource]) -> Dict[str, Any]:
def _get_sm_lm_config(access_templates: List[AccessRight], assigned_resources: List[AssignedResource]) -> LogicalMachine:
    """Create SM logical machine configuration.
    
    Args:
        access_templates: List of access right templates
        assigned_resources: List of assigned resources
        
    Returns:
        LogicalMachine configuration for SM
    """
    templates: Dict[str, AccessRight] = {}
    for template in access_templates:
        templates[template.name] = template
    resources: Dict[str, AssignedResource] = {}
    for resource in assigned_resources:
        resources[resource.name] = resource
    modes = [Mode(1, 2)]
    start_stops: Dict[bool, List[StartStop]] = {}
    agents: Dict[str, Agent] = {}
    lm = LogicalMachine("LM0", "SM", 2, 1, 0, "feenv", "none", templates, resources, modes, start_stops, agents)
    return lm


@pytest.mark.skip("Work in progress")
def test_1(capsys: Any) -> None:
    """Test basic configuration generation and validation.
    
    Args:
        capsys: Pytest capsys fixture
    """
    test_dict = {
        "make": {"soc": "MIMX95", "board": "mcimx95evk", "build_tool": "gcc_cross"},
        "dox": {"name": "MX95EVK", "description": "i.MX95 EVK Configuration Data"},
        "board": {"DEBUG_UART_INSTANCE": "2", "DEBUG_UART_BAUDRATE": "115200", "I2C_INSTANCE": "1", "I2C_BAUDRATE": "400000"},
        "device_include_path": "",
        "common_access_rights": [{"name": "ALL", "parameters": {"api": "all"}}, {"name": "OWNER", "parameters": {"api": "all", "perm": "rw"}}],
        "domains": [
            {
                "id": "DOM0",
                "did": 0,
                "access_rights": [{"name": "DATA", "parameters": {"perm": "rw", "api": "none"}}],
                "assigned_resources": [{"name": "M33_TCM_SYS", "template": "DATA", "parameters": {"begin": "0x020200000", "size": "256K"}}],
            }
        ],
        "logical_machines": [
            {
                "id": "LM0",
                "name": "SM",
                "did": 2,
                "boot": 1,
                "skip": 0,
                "safe": "feenv",
                "rpc": "none",
                "access_rights": [
                    {"name": "DATA", "parameters": {"perm": "rw", "api": "none"}},
                ],
                "modes": [{"msel": 1, "boot": 2}],
                "assigned_resources": [
                    {"name": "CLK_A55MTRBUS", "template": "ALL"},
                    {"name": "M33_TCM_SYS", "template": "DATA", "parameters": {"begin": "0x020200000", "size": "256K"}},
                ],
            },
            {
                "id": "LM1",
                "name": "M7",
                "did": 4,
                "boot": 2,
                "skip": 0,
                "safe": "seenv",
                "rpc": "scmi",
                "agents": [
                    {
                        "id": "SCMI_AGENT0",
                        "name": "M7",
                        "access_rights": [
                            {"name": "DATA", "parameters": {"perm": "rw"}},
                            {"name": "EXEC", "parameters": {"perm": "sec_rwx"}},
                            {"name": "TEST_MU", "parameters": {"perm": "sec_rw"}},
                        ],
                        "mailboxes": [
                            {
                                "type": "mu",
                                "mu": 2,
                                "test": 8,
                                "priority": "high",
                                "channels": [
                                    {"db": 0, "xport": "smt", "check": "crc32", "rpc": "scmi", "type": "a2p"},
                                    {"db": 1, "xport": "smt", "check": "crc32", "rpc": "scmi", "type": "p2a_notify", "notify": 24},
                                    {"db": 2, "xport": "smt", "check": "crc32", "rpc": "scmi", "type": "p2a_priority", "test": "default"},
                                ],
                            }
                        ],
                        "assigned_resources": [
                            {"name": "CLK_A55MTRBUS", "template": "ALL"},
                            {"name": "M33P", "template": "OWNER"},
                            {"name": "MU1_A", "template": "TEST_MU"},
                            {"name": "M33_ROM", "template": "EXEC", "parameters": {"begin": "0x000000000", "end": "0x00003FFFF"}},
                            {"name": "M33_TCM_CODE", "template": "EXEC", "parameters": {"begin": "0x0201C0000", "size": "256K"}},
                            {"name": "FAULT_SW3", "template": "OWNER", "parameters": {"reaction": "grp_reset"}},
                        ],
                    }
                ],
            },
        ],
    }

    with TemporaryDirectory() as temp:
        # Prepare path
        device_name = "MIMX95"
        sm_fw_root_temp = utils.find_firmware_root_dir(os.path.join(get_smct_root(), ".."))
        if sm_fw_root_temp is None:
            pytest.fail("Could not find firmware root directory")
            return
        sm_fw_root = sm_fw_root_temp
        device_cfg_include_file_path = _get_device_include_path(device_name, sm_fw_root, temp)
        test_dict["device_include_path"] = device_cfg_include_file_path
        # Generate test CFG file content
        generator = CfgFileGenerator.from_dict(test_dict)
        generator.generate()
        result = generator.get_result()
        _test_cfg(capsys, temp, sm_fw_root, result)


@pytest.mark.skip("Work in progress")
@pytest.mark.parametrize("device_board_pair", _flatten_board_dict(TEST_BOARDS))
def test_generated(capsys: Any, device_board_pair: Tuple[str, str]) -> None:
    """Test randomly generated configuration files.
    
    Args:
        capsys: Pytest capsys fixture
        device_board_pair: Tuple of (device, board) to test
    """
    device, board = device_board_pair
    sm_fw_root = utils.find_firmware_root_dir(os.path.join(get_smct_root(), ".."))
    if sm_fw_root is None:
        pytest.fail("Could not find SM firmware root directory")
        return
    if not _load_resources(sm_fw_root, device, board):
        pytest.fail(f'Resource database was not properly loaded for device "{device}" and board "{board}"')

    already_used_assignments: List[AssignedResource] = []

    number_of_lms = _get_lms_limit(device)
    lm_counter = 0
    global_access_templates = _generate_default_access_templates()

    dids = list(range(16))
    dids.remove(0)  # DID 0 should not be automatically assigned - ELE
    dids.remove(9)  # DID 9 should not be automatically assigned - Debug

    test_dictionary = _create_base_of_dictionary(device, board, "Description", common_access_templates=global_access_templates)
    lms: Dict[str, LogicalMachine] = {}

    owner_access_template = AccessRight("OWNER", {"perm": "sec_rw", "api": "all"})
    lm_access_templates = [
        AccessRight("DATA", {"perm": "rw", "api": "none"}),
        owner_access_template,
        AccessRight("DFMT0", {"sa": "secure"}),
        AccessRight("DFMT1", {"sa": "secure", "pa": "privileged"}),
    ]

    lm_final_access_templates = global_access_templates.copy()
    lm_final_access_templates.extend(lm_access_templates)

    assigned_resources: List[AssignedResource] = []

    _create_assignment_for_macro("M33P", [owner_access_template], already_used_assignments, assigned_resources)
    _create_assignment_for_macro("M33_TCM_CODE", lm_final_access_templates, already_used_assignments, assigned_resources)

    assign_amount = int(random() * 30) + 5
    _generate_assignments(assign_amount, lm_final_access_templates, assigned_resources, already_used_assignments)

    lm_sm = _get_sm_lm_config(lm_access_templates, assigned_resources)
    lms[lm_sm.name] = lm_sm
    dids.remove(lm_sm.did)
    lm_counter += 1

    boot_order = lm_sm.boot
    boot_order += 1

    agent_order = 0

    number_of_lms_to_be_created = number_of_lms - lm_counter
    for index in range(lm_counter, number_of_lms_to_be_created + 1):
        did = dids.pop()
        boot = boot_order
        boot_order += 1
        skip = 1
        lm_access_rights: Dict[str, AccessRight] = {}
        lm_assigned_resources: Dict[str, AssignedResource] = {}
        modes: List[Mode] = []
        start_stops: Dict[bool, List[StartStop]] = {}
        agents: Dict[str, Agent] = {}
        lm_id = f"LM{index}"

        db = 0
        notify = None
        channels = [Channel(db, "smt", "crc32", "scmi", "a2p", "default", notify), Channel(1, "smt", "crc32", "scmi", "p2a_notify", None, 24)]

        mu = 9
        mailbox_test = 8
        mailboxes = [Mailbox("mu", mu, mailbox_test, "high", channels)]

        agent_access_rights: Dict[str, AccessRight] = {}
        owner_access_template = AccessRight("OWNER", {"perm": "sec_rw", "api": "all"})
        agent_access_rights_list = [owner_access_template]

        agent_joined_access_rights = global_access_templates.copy()
        agent_joined_access_rights.extend(agent_access_rights_list)

        for right in agent_access_rights_list:
            agent_access_rights[right.name] = right

        agent_assigned_resources: Dict[str, AssignedResource] = {}
        agent_assigned_resources_list: List[AssignedResource] = []

        cpus = get_unused_cpus(already_used_assignments)

        lm_cpu = cpus[0]
        if lm_cpu is None:
            continue

        _create_assignment_for_macro(lm_cpu.get_name(), [owner_access_template], already_used_assignments, agent_assigned_resources_list)

        assign_amount = int(random() * 15) + 5
        _generate_assignments(assign_amount, agent_joined_access_rights, agent_assigned_resources_list, already_used_assignments)

        for assignment in agent_assigned_resources_list:
            agent_assigned_resources[assignment.name] = assignment

        agent = Agent(f"SCMI_AGENT{agent_order}", "name", agent_access_rights, mailboxes, agent_assigned_resources)
        agents[agent.id] = agent
        agent_order += 1
        lm = LogicalMachine(lm_id, lm_id, did, boot, skip, "seenv", "scmi", lm_access_rights, lm_assigned_resources, modes, start_stops, agents)
        lms[lm.id] = lm

    lm_counter += number_of_lms_to_be_created

    test_dictionary.logical_machines = lms

    with TemporaryDirectory() as temp:
        device_cfg_include_file_path = _get_device_include_path(device, sm_fw_root, temp)
        test_dictionary.device_cfg_path = device_cfg_include_file_path
        try:
            # Generate test CFG file content
            generator = CfgFileGenerator(test_dictionary)
            generator.generate()
            result = generator.get_result()
        except Exception as ex:  # pylint: disable=broad-exception-caught
            pytest.fail(f"Failed to generate content due to exception: {str(ex)}")
        _save_generated_configuration(board, device, result)
        _test_cfg(capsys, temp, sm_fw_root, result)


def _generate_assignments(
    assign_amount: int, access_templates: List[AccessRight], assigned_resources: List[AssignedResource], already_used_assignments: List[AssignedResource]
) -> None:
    """Generate random resource assignments.
    
    Args:
        assign_amount: Number of assignments to generate
        access_templates: Available access right templates
        assigned_resources: List to append generated assignments to
        already_used_assignments: List of already used assignments to avoid duplicates
    """
    for _ in range(assign_amount):
        random_assignment = _generate_random_assignment(access_templates, already_used_assignments)
        if random_assignment is not None:
            already_used_assignments.append(random_assignment)
            assigned_resources.append(random_assignment)


def get_unused_cpus(already_used_assignments: List[AssignedResource]) -> List[MacroResource]:
    """Get list of CPU resources that haven't been assigned yet.
    
    Args:
        already_used_assignments: List of already used assignments
        
    Returns:
        List of unused CPU macro resources
    """
    cpus = _get_cpu_resources()
    already_used_cpus = []
    for cpu in cpus:
        for assignment in already_used_assignments:
            if assignment.name == cpu.get_name():
                already_used_cpus.append(cpu)
    for cpu in already_used_cpus:
        cpus.remove(cpu)
    return cpus


def _create_assignment_for_macro(
    macro_name: str, access_templates: List[AccessRight], already_used_assignments: List[AssignedResource], assigned_resources: List[AssignedResource]
) -> AssignedResource:
    """Create assignment for a specific macro resource.
    
    Args:
        macro_name: Name of the macro resource
        access_templates: Available access right templates
        already_used_assignments: List of already used assignments
        assigned_resources: List to append the assignment to
        
    Returns:
        Created AssignedResource
    """
    macro_resource = ResourceDatabaseProvider.get_database().find_macro_resource(macro_name)
    assert macro_resource is not None
    resource_assignment = _generate_assignment(macro_resource, access_templates)
    assert resource_assignment is not None
    assigned_resources.append(resource_assignment)
    already_used_assignments.append(resource_assignment)
    return resource_assignment


def _get_cpu_resources() -> List[MacroResource]:
    """Get all CPU macro resources from the database.
    
    Returns:
        List of CPU macro resources
    """
    cpu_resources = []
    for macro_resource in ResourceDatabaseProvider.get_database().macro_resources_list():
        for atom in macro_resource.get_atomic_resources():
            if isinstance(atom, ApiResource):
                api = typing.cast(ApiResource, atom)
                if api.is_cpu():
                    cpu_resources.append(macro_resource)
    return cpu_resources


def _save_generated_configuration(board: str, device: str, configuration_content: str) -> None:
    """Save generated configuration to file.
    
    Args:
        board: Board name
        device: Device name
        configuration_content: Configuration file content
    """
    folder = os.path.join(get_smct_root(), "test_results", f"test_generated_{device}_{board}")
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, "configuration.cfg")
    with open(path, "w", encoding="utf-8") as f:
        f.write(configuration_content)


def _get_device_include_path(device_name: str, sm_fw_root: str, temp_directory: str) -> str:
    """Get relative path to device configuration file.
    
    Args:
        device_name: Device name
        sm_fw_root: SM firmware root directory
        temp_directory: Temporary directory path
        
    Returns:
        Relative path to device.cfg file
    """
    common_root_of_path = os.path.commonpath([sm_fw_root, temp_directory])
    temp_rest = temp_directory.removeprefix(common_root_of_path)
    go_up_by = temp_rest.count(os.path.sep)
    config_rest = sm_fw_root.removeprefix(common_root_of_path).removeprefix("\\")
    go_up_path = (".." + os.path.sep) * go_up_by
    device_cfg_include_file_path = (
        os.path.join(temp_directory, go_up_path, config_rest, "devices", device_name, "configtool", "device.cfg")
        .removeprefix(temp_directory)
        .removeprefix("\\")
    )
    return str(device_cfg_include_file_path)


def _test_cfg(capsys: Any, test_directory: str, sm_fw_root: str, configuration_content: str) -> None:
    """Test generated configuration file against legacy tool.
    
    Args:
        capsys: Pytest capsys fixture
        test_directory: Directory for test files
        sm_fw_root: SM firmware root directory
        configuration_content: Configuration file content to test
    """
    # Prepare generated file to be tested
    file_path = os.path.join(test_directory, "generated.cfg")
    output_path_smct = os.path.join(test_directory, "output_smct")
    output_path_legacy = os.path.join(test_directory, "output_legacy")
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(configuration_content)
    # SMCT CLI
    code, _, stderr = execute_cli(capsys, ["-c", file_path, "-o", output_path_smct, "--sm_dir", sm_fw_root])
    assert code == 0
    assert stderr == ""
    # Legacy application
    config_tool = os.path.join(sm_fw_root, "configs", "configtool.pl")
    code, _, stderr = execute_binary("perl", [config_tool, "-i", file_path, "-o", output_path_legacy])
    assert stderr == ""
    assert code == 0
    # Check differences
    output_path_diff = os.path.join(test_directory, "output_diff")
    differ = FileDiffer(FileDiffer.default_c_files_pattern, output_path_legacy, output_path_smct, output_path_diff)
    if not differ.check_differences():
        differ.store_differences_to_disk(output_path_diff)
        pytest.fail(differ.get_string_result())


def _load_resources(root_directory: str, device_name: str, board_name: str) -> bool:
    """Load device and board resources into the database.
    
    Args:
        root_directory: SM firmware root directory
        device_name: Device name
        board_name: Board name
        
    Returns:
        True if resources loaded successfully, False otherwise
    """
    ResourceDatabaseProvider.clear_database()
    ChipModelProvider.clear_model()
    ConfigurationProvider.clear_configuration()
    header_parser = ApiResourceParser()
    cfg_parser = CfgFileParser()
    resource_parser = ResourceParser(device_name)

    resource_parser.parse_soc_resources()
    header_parser.parse_device(root_directory, device_name)
    header_parser.parse_board(root_directory, board_name)
    cfg_parser.add_static_resources()
    cfg_parser.parse_device(root_directory, device_name)

    if ResourceDatabaseProvider.get_database().is_empty():
        return False
    return True


def _create_base_of_dictionary(
    device: str, board: str, description: str, build_tool: str = "gcc_cross", common_access_templates: List[AccessRight] | None = None
) -> Configuration:
    """Create base configuration dictionary.
    
    Args:
        device: Device name
        board: Board name
        description: Configuration description
        build_tool: Build tool to use (default: gcc_cross)
        common_access_templates: Common access right templates
        
    Returns:
        Base Configuration object
    """
    if common_access_templates is None:
        common_access_templates = _generate_default_access_templates()

    common_access_templates_dict: Dict[str, AccessRight] = {}
    for template in common_access_templates:
        common_access_templates_dict[template.name] = template
    board_command = {"DEBUG_UART_INSTANCE": "2", "DEBUG_UART_BAUDRATE": "115200", "I2C_INSTANCE": "1", "I2C_BAUDRATE": "400000"}
    dox_command = {"name": device, "description": description}
    make_command = {"soc": device, "board": board, "build_tool": build_tool}
    return Configuration(common_access_templates_dict, {}, {}, make_command, dox_command, board_command, "")


def _get_parameters(macro: MacroResource) -> Dict[str, str]:
    """Get parameters for a macro resource assignment.
    
    Args:
        macro: Macro resource to get parameters for
        
    Returns:
        Dictionary of parameter name to value
    """
    parameters: Dict[str, str] = {}
    for atom in macro.get_atomic_resources():
        if isinstance(atom, MbcResource):
            mbc = typing.cast(MbcResource, atom)
            if mbc.get_write_type() == MbcResourceWriteType.MEM:
                trdc = ChipModelProvider.get_model().get_trdc(mbc.get_trdc_id())
                if trdc is None:
                    continue
                mbc_model = trdc.get_mbc(mbc.get_index())
                if mbc_model is None:
                    continue
                mem_model = mbc_model.get_model_mem(mbc.get_mem())
                if mem_model is None:
                    continue
                origin = mem_model.get_origin()
                block_count = mem_model.get_block_count()
                block_size = mem_model.get_block_size()
                max_size = block_count * block_size

                offset = int(random() * max_size)
                offset = int(math.floor(offset / block_size)) * block_size
                begin = origin + offset
                size = int(random() * (max_size - offset))
                size = int(math.ceil(size / block_size)) * block_size

                parameters["begin"] = str(begin)
                parameters["size"] = str(size)
        if isinstance(atom, MrcResource):
            # begin is in first half of memory range and end may overlap to the second half of the memory range
            begin = int(random() * (2 << 30))
            end = begin + int(random() * (2 << 30))
            parameters["begin"] = str(begin)
            parameters["end"] = str(end)
    return parameters


def _requires_trdc_permission(macro: MacroResource) -> bool:
    """Check if macro resource requires TRDC permission.
    
    Args:
        macro: Macro resource to check
        
    Returns:
        True if TRDC permission required, False otherwise
    """
    requires_trdc_permission = False
    for atom in macro.get_atomic_resources():
        if isinstance(atom, (MbcResource, MrcResource)):
            requires_trdc_permission = True
    return requires_trdc_permission


def _requires_api_permission(macro: MacroResource) -> bool:
    requires_api_permission = False
    for atom in macro.get_atomic_resources():
        if isinstance(atom, ApiResource):
            requires_api_permission = True
    return requires_api_permission


def _get_suitable_access_templates(requires_trdc_permission: bool, requires_api_permission: bool, permission_templates: List[AccessRight]) -> List[AccessRight]:
    possible_templates = []
    for template in permission_templates:
        valid = True
        if len(template.parameters.keys()) == 0:
            continue
        template_parameters = template.parameters
        is_trdc = "perm" in template_parameters
        is_api = "api" in template_parameters

        if requires_trdc_permission and not is_trdc:
            valid = False
        if requires_api_permission and not is_api:
            valid = False
        if valid:
            possible_templates.append(template)
    return possible_templates


def _get_possible_templates(macro_resource: MacroResource, permission_templates: List[AccessRight]) -> List[AccessRight]:
    requires_api_permission = _requires_api_permission(macro_resource)
    requires_trdc_permission = _requires_trdc_permission(macro_resource)
    possible_templates = _get_suitable_access_templates(requires_trdc_permission, requires_api_permission, permission_templates)
    return possible_templates


def _get_random_macro_resource() -> MacroResource:
    macro_resources_list = ResourceDatabaseProvider.get_database().macro_resources_list()
    macro_index = int(random() * (len(macro_resources_list) - 1))
    macro_resource = macro_resources_list[macro_index]
    return macro_resource


def _generate_assignment(macro_resource: MacroResource, permission_templates: List[AccessRight]) -> AssignedResource | None:
    possible_templates = _get_possible_templates(macro_resource, permission_templates)

    if len(possible_templates) == 0:
        return None

    template_index = int(random() * (len(possible_templates) - 1))
    template = possible_templates[template_index]
    template_name = template.name

    parameters = _get_parameters(macro_resource)

    return AssignedResource(macro_resource.get_name(), template_name, parameters)


def _can_macro_be_used(macro_resource: MacroResource) -> bool:
    for atom in macro_resource.get_atomic_resources():
        if isinstance(atom, MdacResource):
            return False
        if isinstance(atom, ApiResource):
            api = typing.cast(ApiResource, atom)
            if api.is_cpu():
                return False  # LM already has CPU set manually
    return True


def _can_assigned_resource_be_used(assigned_resource: AssignedResource, already_assigned_resources: List[AssignedResource]) -> bool:
    for resource in already_assigned_resources:
        if assigned_resource.name == resource.name:
            return False
    return True


def _generate_random_assignment(permission_templates: List[AccessRight], already_used_assignments: List[AssignedResource]) -> AssignedResource | None:
    macro_counter = 0
    assignment_counter = 0
    macro_resource: MacroResource | None = None
    assigned_resource: AssignedResource | None = None
    while assignment_counter < 50:
        while macro_counter < 50:
            macro_resource = _get_random_macro_resource()
            macro_counter += 1
            if _can_macro_be_used(macro_resource):
                break

        if macro_resource is None:
            break

        possible_templates = _get_possible_templates(macro_resource, permission_templates)
        assigned_resource = _generate_assignment(macro_resource, possible_templates)
        assignment_counter += 1

        if assigned_resource is not None and _can_assigned_resource_be_used(assigned_resource, already_used_assignments):
            break
    return assigned_resource
