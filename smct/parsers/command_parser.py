#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Module related to parser of the CFG files."""

from __future__ import annotations

import logging
import re
from typing import Any, List, TYPE_CHECKING

from smct import utils
from smct.exceptions.cfg_tool_exception import CfgToolException
from smct.model.model_trdc import TrdcModel
from smct.owners.owner_agent import MailboxLoopback, MailboxMu, ScmiAgent, ScmiChannel, SmtChannel
from smct.owners.owner_dom import DOM
from smct.owners.owner_lm import LM
from smct.resources.res_api import ApiResource

from ..configuration.configuration_provider import ConfigurationProvider
from ..model.chip_model_provider import ChipModelProvider
from ..owners.owner_base import ResourceOwner
from ..resources.resource_database_provider import ResourceDatabaseProvider
from ..utils import FormatedInt, UInt32Constraints
from .resource_parser import ResourceParser

if TYPE_CHECKING:
    from smct.parsers.cfg_parser import CfgFileParser
_re_board_value_assign = re.compile(r"(\w+)=(\w+)")
_re_fusa_value_assign = re.compile(r"(\w+)=(?:\"(.*?)\"|(\w+))")

logger = logging.getLogger()


def _assign_dfmt_defines(owner: ResourceOwner) -> None:
    """Assigns DFMT0 and DFMT1 defines to Resource Owner.

    Args:
        owner: The resource owner to assign defines to.
    """
    for define_name in ["DFMT0", "DFMT1"]:
        define = ResourceDatabaseProvider.get_database().get_define(define_name)
        if define:
            owner.assign_define(define)


class CommandParser:
    """Preprocessor for CFG files that passes on all commands except LM, DOM, and AGENT."""

    # Implement these three - call parent implementation
    @classmethod
    def parse_command_dom_n(cls, first: re.Match, atoms: List[str], file_parser: CfgFileParser) -> None:
        """Process DOMn command from CFG file; implement in subclasses."""

    @classmethod
    def parse_command_lm_n(cls, first: re.Match, atoms: List[str], file_parser: CfgFileParser) -> None:
        """Process LMn command from CFG file; implement in subclasses."""

    @classmethod
    def parse_command_scmi_agent_n(cls, first: re.Match, atoms: List[str], file_parser: CfgFileParser) -> None:
        """Process SCMI_AGENTn command from CFG file; implement in subclasses."""

    @classmethod
    def parse_command_trdc_config_a(cls, first: re.Match, atoms: List[str], file_parser: CfgFileParser) -> None:
        """Pass through TRDC_CONFIG_a command."""

    @classmethod
    def parse_command_bctrl_config_a(cls, first: re.Match, atoms: List[str], file_parser: CfgFileParser) -> None:
        """Pass through BCTRL_CONFIG_a command."""

    @classmethod
    def parse_command_debug(cls, first: re.Match, atoms: List[str], file_parser: CfgFileParser) -> None:
        """Pass through DEBUG command."""

    @classmethod
    def parse_command_mix(cls, first: re.Match, atoms: List[str], file_parser: CfgFileParser) -> None:
        """Pass through MIX command."""

    @classmethod
    def parse_command_make(cls, first: re.Match, atoms: List[str], file_parser: CfgFileParser) -> None:
        """Pass through MAKE command."""

    @classmethod
    def parse_command_dox(cls, first: re.Match, atoms: List[str], file_parser: CfgFileParser) -> None:
        """Pass through DOX command."""

    @classmethod
    def parse_command_mailbox(cls, first: re.Match, atoms: List[str], file_parser: CfgFileParser) -> None:
        """Pass through MAILBOX command."""

    @classmethod
    def parse_command_channel(cls, first: re.Match, atoms: List[str], file_parser: CfgFileParser) -> None:
        """Pass through CHANNEL command."""

    @classmethod
    def parse_command_mode(cls, first: re.Match, atoms: List[str], file_parser: CfgFileParser) -> None:
        """Pass through MODE command."""

    @classmethod
    def parse_command_auto_create_res(cls, first: re.Match, atoms: List[str], file_parser: CfgFileParser) -> bool:
        """Pass through auto create resource command."""
        return True

    @classmethod
    def parse_command_board(cls, first: re.Match, atoms: List[str], file_parser: CfgFileParser) -> None:
        """Pass through BOARD command."""

    @classmethod
    def parse_command_fusa_def(cls, first: re.Match, atoms: List[str], file_parser: CfgFileParser) -> None:
        """Pass through FUSA_DEF command."""

    @classmethod
    def parse_command_fusa_task(cls, first: re.Match, atoms: List[str], file_parser: CfgFileParser) -> None:
        """Pass through FUSA_TASK command."""


class CfgCommandParser(CommandParser):
    """Parser for the commands from CFG file."""

    @classmethod
    def parse_command_trdc_config_a(cls, first: re.Match, atoms: List[str], _: CfgFileParser) -> None:
        """Parses command TRDC_CONFIG_a and stores the information about the TRDC to the chip model.

        Args:
            first: The regex match object for the command.
            atoms: List of atoms from the command line.
        """
        atoms.pop(0)
        id_letter = first.group(1)
        trdc = ChipModelProvider.get_model().get_trdc(id_letter)
        if trdc is None:
            raise CfgToolException(f"There is no TRDC instance {id_letter}")
        ndid = utils.get_attribute_value_from_list(atoms, "ndid", remove=True)
        nmstr = utils.get_attribute_value_from_list(atoms, "nmstr", remove=True)
        nmbc = utils.get_attribute_value_from_list(atoms, "nmbc", remove=True)
        nmrc = utils.get_attribute_value_from_list(atoms, "nmrc", remove=True)
        kpaen = utils.get_attribute_value_from_list(atoms, "kpaen", remove=True)
        sidsz = utils.get_attribute_value_from_list(atoms, "sidsz", remove=True)
        if not ndid or not nmstr or not nmbc or not nmrc:
            raise CfgToolException("Command TRDC_CONFIG_a does not contain either ndid, nmstr, nmbc or nmrc attribute")
        if not kpaen:
            kpaen = "1"
        if not sidsz:
            default = TrdcModel.DFMT1_register["SID"]["width"]
            sidsz = default if default else "6"

        trdc.set_model_params(int(ndid), int(nmstr), int(nmbc), int(nmrc), int(kpaen), int(sidsz))
        if atoms:
            logger.warning("Unexpected parameters on command TRDC_CONFIG_%s", id_letter)

    @classmethod
    def parse_command_bctrl_config_a(cls, first: re.Match, atoms: List[str], __: CfgFileParser) -> None:
        """Parses command BCTR_CONFIG_a and stores the information about the block control to the chip model.

        Args:
            first: The regex match object for the command.
            atoms: List of atoms from the command line.
        """
        atoms.pop(0)
        id_letter = first.group(1)
        ChipModelProvider.get_model().get_bctrl(id_letter)  # Creates the block control
        if atoms:
            logger.warning("Unexpected parameters on command BCTR_CONFIG_%s", id_letter)

    @classmethod
    def parse_command_dom_n(cls, first: re.Match, atoms: List[str], file_parser: CfgFileParser) -> None:
        """Parses the command DOMn and stores the information about the domain in configuration object.

        Sets the domain as owner for the following resources.

        Args:
            first: The regex match object for the command.
            atoms: List of atoms from the command line.
            file_parser: The CFG file parser instance.
        """
        atoms.pop(0)
        did_string = utils.get_attribute_value_from_list(atoms, "did", remove=True)
        if did_string is None:
            logger.error("Command '%s' does not contain attribute did", first.group(0), extra={"source": file_parser.get_current_file()})
            return
        did = int(did_string)
        name = utils.get_attribute_value_from_list(atoms, "name", remove=True)
        dom = ConfigurationProvider.get_configuration().get_by_did(did)
        if not dom:
            dom = DOM(first.group(0), did, name)
            ConfigurationProvider.get_configuration().add_dom(dom)
        # Dirty flag is set (and kept) True if DOM is defined in an first-level cfg file
        # It is set False if it occurs in the included file
        dom.set_dirty_flag(len(file_parser.get_include_list()) == 0)
        _assign_dfmt_defines(dom)
        file_parser.set_current_resource_owner(dom)
        if atoms:
            logger.warning("Unexpected parameters on command DOM%i", did)

    @classmethod
    def parse_command_lm_n(cls, first: re.Match, atoms: List[str], file_parser: CfgFileParser) -> None:
        """Parses the LMn command and stores the information about the logical machine in configuration object.

        Sets the logical machine as owner of the following resources.

        Args:
            first: The regex match object for the command.
            atoms: List of atoms from the command line.
            file_parser: The CFG file parser instance.
        """
        atoms.pop(0)
        name = utils.get_attribute_value_from_list(atoms, "name", remove=True)
        did_str = utils.get_attribute_value_from_list(atoms, "did", remove=True)
        did = utils.parse_int(did_str) if did_str is not None else int(first.group(1))
        boot_str = utils.get_attribute_value_from_list(atoms, "boot", remove=True)
        boot = utils.parse_int(boot_str) if boot_str is not None else None
        skip_str = utils.get_attribute_value_from_list(atoms, "skip", remove=True)
        skip = bool(utils.parse_int(skip_str)) if skip_str is not None else None
        rpc = utils.get_attribute_value_from_list(atoms, "rpc", remove=True)
        rtime_str = utils.get_attribute_value_from_list(atoms, "rtime", remove=True)
        rtime = utils.parse_int(rtime_str) if rtime_str is not None else None
        safe = utils.get_attribute_value_from_list(atoms, "safe", remove=True)
        group_str = utils.get_attribute_value_from_list(atoms, "group", remove=True)
        group = utils.parse_int(group_str) if group_str is not None else None
        auto = utils.get_attribute_value_from_list(atoms, "auto", remove=True)
        default = utils.contains_attribute_in_list(atoms, "default", no_value=True, remove=True)
        if name is None:
            logger.error("Command LM requires parameter 'name', but it is not specified.", extra={"source": file_parser.get_current_file()})
            return
        lm = LM(first.group(0), did, name, rpc, rtime, safe, group, auto, default)
        lm.get_msel(0, boot, skip)
        _assign_dfmt_defines(lm)
        file_parser.set_current_resource_owner(lm)
        ConfigurationProvider.get_configuration().add_lm(lm)
        if atoms:
            logger.warning("Unexpected parameters on command LM%i", did)

    @classmethod
    def parse_command_scmi_agent_n(cls, first: re.Match, atoms: List[str], file_parser: CfgFileParser) -> None:
        """Parses the SCMI_AGENTn command and stores the information about the SCMI agent in the configuration object.

        Sets the SCMI agent as owner of the following resources.

        Args:
            first: The regex match object for the command.
            atoms: List of atoms from the command line.
            file_parser: The CFG file parser instance.
        """
        atoms.pop(0)
        agent_id = first.group(0)
        current_lm = file_parser.get_current_logical_machine()
        if not current_lm:
            raise CfgToolException(f"Cannot define agent {agent_id} outside LM")
        name = utils.get_attribute_value_from_list(atoms, "name", remove=True)
        if name is None:
            name = f"AGENT{agent_id}"
            source = "/".join(["user_config", current_lm.get_id(), name])
            logger.warning("Command SCMI_AGENT requires parameter name, but it is not specified. Defaulting to name '%s'", name, extra={"source": source})
        secure = utils.contains_attribute_in_list(atoms, "secure", no_value=True, remove=True)
        agent = ScmiAgent(agent_id, current_lm, name, secure, current_lm.get_safe(), current_lm.get_did())
        _assign_dfmt_defines(agent)
        file_parser.set_current_resource_owner(agent)
        current_lm.add_agent(agent)
        dup = utils.get_attribute_value_from_list(atoms, "dup", remove=True)
        if dup is not None:
            dup_int = utils.parse_int(dup)
            dup_agents = [x for x in ConfigurationProvider.get_configuration().get_all_agents() if x.get_id() == ("SCMI_AGENT" + str(dup_int))]
            if len(dup_agents) != 1:
                source = "/".join(["user_config", current_lm.get_id(), name])
                validation_id = ".".join([agent_id, "DUP"])
                logger.error(
                    "Agent %s cannot 'use' dup for self or an agent with higher number", name, extra={"source": source, "validation_id": validation_id}
                )
            else:
                agent.duplicate(dup_agents[0], dup_int)
        if atoms:
            logger.warning("Unexpected parameters on command SCMI_AGENT%s", agent_id)

    @classmethod
    def parse_command_debug(cls, _: re.Match, atoms: List[str], __: CfgFileParser) -> None:
        """Parses the DEBUG command and stores the defined domain IDs as debug domains or logical machines.

        Args:
            _: The regex match object for the command (unused).
            atoms: List of atoms from the command line.
            file_parser: The CFG file parser instance.
        """
        atoms.pop(0)
        did_str = utils.get_attribute_value_from_list(atoms, "did", remove=True)
        did = utils.parse_int(did_str) if did_str is not None else -1
        dom = ConfigurationProvider.get_configuration().get_by_did(did)
        if dom is not None:
            dom.set_debug()
        else:
            raise CfgToolException(f"Invalid did={did} specified in DEBUG command")
        if atoms:
            logger.warning("Unexpected parameters on command DEBUG")

    @classmethod
    def parse_command_mix(cls, _: re.Match, atoms: List[str], file_parser: CfgFileParser) -> None:
        """Parses the MIX command and stores the mix name in the configuration.

        Args:
            _: The regex match object for the command (unused).
            atoms: List of atoms from the command line.
            file_parser: The CFG file parser instance.
        """
        atoms.pop(0)
        name = utils.get_attribute_value_from_list(atoms, "name", remove=True)
        if name is None:
            logger.error("MIX command requires parameter name, but none was specified.", extra={"source": file_parser.get_current_file()})
            return
        ChipModelProvider.get_model().add_mix(name)
        if atoms:
            logger.warning("Unexpected parameters on command MIX")

    @classmethod
    def parse_command_make(cls, _: re.Match, atoms: List[str], file_parser: CfgFileParser) -> None:
        """Parses the MAKE command and stores the make information in the configuration.

        Args:
            _: The regex match object for the command (unused).
            atoms: List of atoms from the command line.
            file_parser: The CFG file parser instance.
        """
        # MAKE is useful to parse other headers
        atoms.pop(0)
        header_parser = file_parser.get_header_parser()
        root_directory = file_parser.get_root_directory()
        if header_parser is not None and root_directory is not None:
            device = utils.get_attribute_value_from_list(atoms, "soc", remove=True)
            board = utils.get_attribute_value_from_list(atoms, "board", remove=True)
            build = utils.get_attribute_value_from_list(atoms, "build", remove=True)
            while utils.contains_attribute_in_list(atoms, "var"):
                mak_var = utils.get_variable_from_list(atoms, remove=True)
                if mak_var:
                    variable_string, *value_string = mak_var.split("|")
                    if not value_string:
                        ConfigurationProvider.get_configuration().set_mak_variable(variable_string, 1)
                    elif len(value_string) == 1:
                        ConfigurationProvider.get_configuration().set_mak_variable(variable_string, value_string[0])
                    else:
                        logger.error("MAKE command contains 'var' definition with multiple values.", extra={"source": file_parser.get_current_file()})
                        continue
            if device and board and build:
                rp = ResourceParser(device)
                rp.parse_soc_resources()

                ConfigurationProvider.get_configuration().set_device(device, board)
                ConfigurationProvider.get_configuration().set_build_tool(build)
                if not header_parser.parse_device(root_directory, device):
                    raise CfgToolException(f"Failed to load device '{device}")
                if not header_parser.parse_board(root_directory, board):
                    raise CfgToolException(f"Failed to load board {board}")
        if atoms:
            logger.warning("Unexpected parameters on command MAKE")

    @classmethod
    def parse_command_dox(cls, _: re.Match, atoms: List[str], file_parser: CfgFileParser) -> None:
        """Parses the DOX command and stores the doxygen information in configuration.

        Args:
            _: The regex match object for the command (unused).
            atoms: List of atoms from the command line.
            file_parser: The CFG file parser instance.
        """
        # DOX gives documentation info
        atoms.pop(0)
        name = utils.get_attribute_value_from_list(atoms, "name", remove=True)
        desc = utils.get_attribute_value_from_list(atoms, "desc", remove=True)
        if name is None:
            logger.warning(
                "Command DOX requires parameter name, but it was not specified. Using empty string instead.", extra={"source": file_parser.get_current_file()}
            )
            name = ""
        if desc is None:
            logger.warning(
                "Command DOX requires parameter desc, but it was not specified. Using empty string instead.", extra={"source": file_parser.get_current_file()}
            )
            desc = ""
        if name:
            ConfigurationProvider.get_configuration().set_doxygen_name_descr(name, desc)
        if atoms:
            logger.warning("Unexpected parameters on command DOX")

    @classmethod
    def parse_command_mailbox(cls, _: re.Match, atoms: List[str], file_parser: CfgFileParser) -> None:
        """Parses the MAILBOX command and stores the information about the mailbox in current SCMI agent.

        Args:
            _: The regex match object for the command (unused).
            atoms: List of atoms from the command line.
            file_parser: The CFG file parser instance.
        """
        atoms.pop(0)
        current_agent = file_parser.get_current_agent()
        if not current_agent:
            raise CfgToolException("The MAILBOX needs to be assigned to SCMI_AGENT")
        type_parameter = utils.get_attribute_value_from_list(atoms, "type", remove=True)
        test_str = utils.get_attribute_value_from_list(atoms, "test", remove=True)
        test = utils.parse_int(test_str) if test_str is not None else None
        priority = utils.get_attribute_value_from_list(atoms, "priority", remove=True)
        if type_parameter == "mu":
            mu_str = utils.get_attribute_value_from_list(atoms, "mu", remove=True)
            sma_str = utils.get_attribute_value_from_list(atoms, "sma", remove=True)
            sma = FormatedInt(sma_str) if sma_str is not None else None
            if sma is not None:
                if sma.get_value() > UInt32Constraints.MAX_VALUE:
                    source = "/".join(["user_config", current_agent.get_owner().get_id(), current_agent.get_id(), "SMA"])
                    validation_id = ".".join([current_agent.get_id(), "SMA"])
                    logger.error(
                        "SMA address %s exceeds maximum 32-bit value",
                        sma,
                        extra={"source": source, "validation_id": validation_id},
                    )
                    sma = FormatedInt(UInt32Constraints.DEFAULT_VALUE)
            mu = utils.parse_int(mu_str) if mu_str is not None else -1
            mail_box = MailboxMu(mu, test, sma, priority)
            current_agent.add_mailbox(mail_box)
        elif type_parameter == "loopback":
            current_agent.add_mailbox(MailboxLoopback(test, priority))
        elif not type_parameter:
            raise CfgToolException("Missing MAILBOX type")
        else:
            raise CfgToolException(f"Unsupported MAILBOX type '{type_parameter}'")
        if atoms:
            logger.warning("Unexpected parameters on command MAILBOX")

    @classmethod
    def parse_command_channel(cls, _: re.Match, atoms: List[str], file_parser: CfgFileParser) -> None:
        """Parses the CHANNEL command and stores the information in the current agent's mailbox.

        Args:
            _: The regex match object for the command (unused).
            atoms: List of atoms from the command line.
            file_parser: The CFG file parser instance.
        """
        atoms.pop(0)
        current_agent = file_parser.get_current_agent()
        if current_agent is None:
            raise CfgToolException("The CHANNEL needs to be assigned to SCMI_AGENT's MAILBOX")
        mailbox = current_agent.get_mailbox()
        if mailbox is None:
            raise CfgToolException("The CHANNEL needs to be assigned to SCMI_AGENT's MAILBOX")

        # the CHANNEL command describes two interconnected channels
        xport = utils.get_attribute_value_from_list(atoms, "xport", remove=True)
        if xport == "smt":
            db_str = utils.get_attribute_value_from_list(atoms, "db", remove=True)
            if db_str is None:
                source = "/".join(["user_config", current_agent.get_id(), "CHANNEL"])
                logger.error("Parameter 'db' was not set in '%s'", ", ".join(atoms), extra={"source": source})
            db = utils.parse_int(db_str) if db_str is not None else 0
            check = utils.get_attribute_value_from_list(atoms, "check", remove=True)
            xport_ch = SmtChannel(db, check)
            xport_ch.set_mailbox(mailbox)
        elif not xport:
            raise CfgToolException("Missing CHANNEL XPORT type")
        else:
            raise CfgToolException(f"Unsupported CHANNEL XPORT type '{xport}'")

        rpc = utils.get_attribute_value_from_list(atoms, "rpc", remove=True)
        if rpc == "scmi":
            sequence = utils.get_attribute_value_from_list(atoms, "sequence", remove=True)
            channel_type = utils.get_attribute_value_from_list(atoms, "type", remove=True)
            test = utils.get_attribute_value_from_list(atoms, "test", remove=True)
            notify = utils.get_attribute_value_from_list(atoms, "notify", remove=True)
            if channel_type is None:
                source = "/".join(["user_config", current_agent.get_id(), "CHANNEL"])
                logger.error("Command CHANNEL(%s) in agent '%s' must contain parameter 'type'", atoms, current_agent.get_name(), extra={"source": source})
                return
            rpc_ch = ScmiChannel(current_agent, channel_type, sequence, test, notify)
            if xport_ch:
                xport_ch.set_rpc_channel(rpc_ch)
                rpc_ch.set_xport_channel(xport_ch)
            current_agent.add_channel(rpc_ch)
        elif not rpc:
            raise CfgToolException("Missing CHANNEL RPC type")
        else:
            raise CfgToolException(f"Unsupported CHANNEL RPC type '{rpc}'")
        if atoms:
            logger.warning("Unexpected parameters on command CHANNEL")

    @classmethod
    def parse_command_mode(cls, _: re.Match, atoms: List[str], file_parser: CfgFileParser) -> None:
        """Parses the MODE command and stores the information in current logical machine.

        Args:
            _: The regex match object for the command (unused).
            atoms: List of atoms from the command line.
            file_parser: The CFG file parser instance.
        """
        atoms.pop(0)
        current_lm = file_parser.get_current_logical_machine()
        if not current_lm:
            raise CfgToolException("The MODE needs to be assigned to LM")
        msel_str = utils.get_attribute_value_from_list(atoms, "msel", remove=True)
        msel = utils.parse_int(msel_str) if msel_str is not None else None
        if isinstance(msel, int):
            boot_str = utils.get_attribute_value_from_list(atoms, "boot", remove=True)
            boot = utils.parse_int(boot_str) if boot_str is not None else None
            skip_parameter = utils.get_attribute_value_from_list(atoms, "skip", remove=True)
            skip = None
            if skip_parameter is not None:
                skip = bool(utils.parse_int(skip_parameter))
            current_lm.get_msel(msel, boot, skip)  # Creates the MSEL if does not exist yet
        else:
            raise CfgToolException("MODE requires an 'msel' parameter")
        if atoms:
            logger.warning("Unexpected parameters on command MODE")

    @classmethod
    def parse_command_auto_create_res(cls, first: re.Match, atoms: List[str], _: CfgFileParser) -> bool:
        """Parses the resource command and creates the atomic resource from the information in the command.

        Args:
            first: The regex match object for the command.
            atoms: List of atoms from the command line.
            file_parser: The CFG file parser instance.

        Returns:
            True to continue processing the line.
        """
        name = first.group(1)
        if len(ResourceDatabaseProvider.get_database().find_atomic_resource_by("name", name)) == 0:
            cat = first.group(2)
            attributes = {"name": name, "type": "API", "cat": cat, "api": cat}
            test = utils.get_attribute_value_from_list(atoms, "test", remove=True)
            if test:
                attributes["test"] = test
            res = ApiResource(attributes)
            ResourceDatabaseProvider.get_database().add_atomic_resource(res)
        return True  # continue processing line

    @classmethod
    def parse_command_board(cls, _: re.Match, atoms: List[str], file_parser: CfgFileParser) -> None:
        """Parses BOARD command.

        Args:
            _: The regex match object for the command (unused).
            atoms: List of atoms from the command line.
            file_parser: The CFG file parser instance.
        """
        atoms.pop(0)
        file_parser.set_current_resource_owner(ResourceOwner("BOARD"))
        pattern_match = _re_board_value_assign.match(atoms[0])
        if pattern_match:
            config = pattern_match.group(1)
            value = pattern_match.group(2)
            match config:
                case "DEBUG_UART_INSTANCE":
                    ConfigurationProvider.get_configuration().set_debug_uart_instance(FormatedInt(value))
                case "DEBUG_UART_BAUDRATE":
                    ConfigurationProvider.get_configuration().set_debug_uart_baudrate(FormatedInt(value))
                case "I2C_INSTANCE":
                    ConfigurationProvider.get_configuration().set_pmic_i2c_instance(FormatedInt(value))
                case "I2C_BAUDRATE":
                    ConfigurationProvider.get_configuration().set_pmic_i2c_baudrate(FormatedInt(value))
                case _:
                    ConfigurationProvider.get_configuration().add_board_config(config, value)
            atoms.pop(0)
        if atoms:
            logger.warning("Unexpected parameters on command BOARD")

    @classmethod
    def parse_command_fusa_def(cls, _: re.Match, atoms: List[str], file_parser: CfgFileParser) -> None:
        """Parses FUSA_DEF command.

        Args:
            _: The regex match object for the command (unused).
            atoms: List of atoms from the command line.
            file_parser: The CFG file parser instance.
        """
        pattern_match = _re_fusa_value_assign.match(atoms[1])
        if pattern_match:
            config = pattern_match.group(1)
            value = pattern_match.group(2) if pattern_match.group(2) is not None else pattern_match.group(3)
            parsed_val = utils.parse_int_or_return_str(value)
            comment = utils.get_attribute_value_from_list(atoms, "comment")
            ConfigurationProvider.get_configuration().add_fusa_config(config, parsed_val, comment)

    @classmethod
    def parse_command_fusa_task(cls, _: re.Match, atoms: List[str], file_parser: CfgFileParser) -> None:
        """Parses FUSA_DEF command.

        Args:
            _: The regex match object for the command (unused).
            atoms: List of atoms from the command line.
            file_parser: The CFG file parser instance.
        """
        name = utils.get_attribute_value_from_list(atoms, "task")
        period: Any | None = utils.get_attribute_value_from_list(atoms, "period")
        task_type = utils.get_attribute_value_from_list(atoms, "type")
        comment = utils.get_attribute_value_from_list(atoms, "comment")
        parsed_period = utils.parse_int_or_return_str(period)

        if name is not None:
            ConfigurationProvider.get_configuration().add_fusa_task(name, parsed_period, task_type, comment)


class CfgPreprocessor(CommandParser):
    """Preprocessor for configuration files."""

    @classmethod
    def parse_command_lm_n(cls, first: re.Match, atoms: List[str], file_parser: CfgFileParser) -> None:
        """Parses the LMn command and stores the information about the logical machine in configuration object.

        Sets the logical machine as owner of the following resources.

        Args:
            first: The regex match object for the command.
            atoms: List of atoms from the command line.
            file_parser: The CFG file parser instance.
        """
        lm_index = first.group(1)
        lm_auto = ApiResource({"name": f"LMM_{lm_index}", "type": "API", "cat": "LMM", "api": "LMM"})
        ResourceDatabaseProvider.get_database().add_automatic_resource(lm_auto)

    @classmethod
    def parse_command_scmi_agent_n(cls, first: re.Match, atoms: List[str], file_parser: CfgFileParser) -> None:
        """Parses the SCMI_AGENTn command and stores the information about the SCMI agent in the configuration object.

        Sets the SCMI agent as owner of the following resources.

        Args:
            first: The regex match object for the command.
            atoms: List of atoms from the command line.
            file_parser: The CFG file parser instance.
        """
        agent_index = first.group(1)
        agent_auto = ApiResource({"name": f"BASE_AGENT_{agent_index}", "type": "API", "cat": "BASE", "api": "BASE"})
        ResourceDatabaseProvider.get_database().add_automatic_resource(agent_auto)
