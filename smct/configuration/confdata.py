#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause

"""Module related to user configuration"""

import json
import logging
import os
import typing
from typing import Any, Dict, List, Tuple

from smct.configuration.confdata_fusa import FusaConfigurationData, FusaDefine, FusaTask
from smct.configuration.confdata_loader import ConfigLoader
from smct.exceptions.cfg_tool_exception import CfgToolException
from smct.model.chip_model_provider import ChipModelProvider
from smct.model.model_bctrl import BctrlModel
from smct.model.model_trdc import TrdcModel
from smct.owners.owner_agent import Channel, Mailbox, MailboxLoopback, MailboxMu, ScmiAgent, ScmiChannel, SmtChannel
from smct.owners.owner_base import AssignedDefine, AssignedResource
from smct.owners.owner_dom import DOM
from smct.owners.owner_lm import LM, MSEL, StartStop
from smct.parsers.resource_parser import ResourceParser
from smct.product_info import ProductInfo
from smct.resources.default_permission import DefaultPermission
from smct.resources.res_mbc import MbcResource
from smct.resources.res_mrc import MrcResource
from smct.resources.resource_database_provider import ResourceDatabaseProvider
from smct.utils import FormatedInt, validate_json

logger = logging.getLogger()


class ConfigurationData:
    """Main object representing user configuration. Exists as singleton CONF"""

    def __init__(self) -> None:
        self._sm_fw_directory: str = ""
        self._config_name: str = ""  # config name
        self._dox_name: str = ""  # doxygen config name
        self._dox_descr: str = ""  # doxygen config description
        self._device: str | None = None  # target device
        self._board: str | None = None  # target board
        self._domains: List[DOM | LM | None] = [None] * 16  # index to this list is a did
        self._lmm: List[LM] = []  # selection of LMs (note that LM is also mapped by _domains)
        self._board_configs: List[Tuple[str, str]] = []
        self._fusa: FusaConfigurationData = FusaConfigurationData()
        self._build_tool: str = ""
        self._debug_uart: Tuple[FormatedInt, FormatedInt] = (FormatedInt("-1"), FormatedInt("-1"))
        self._pmic_i2c: Tuple[FormatedInt, FormatedInt] = (FormatedInt("-1"), FormatedInt("-1"))
        self._mak_variables: List[Tuple[str, Any]] = []
        self._common_defines: Dict[str, AssignedDefine] = {}

    def get_doxygen_description(self) -> str:
        """Returns doxygen description of the configuration.

        Returns:
            Doxygen description string.
        """
        return self._dox_descr

    def get_doxygen_name(self) -> str:
        """Returns doxygen name of the configuration.

        Returns:
            Doxygen name string.
        """
        return self._dox_name

    def get_config_name(self) -> str:
        """Returns name of the configuration.

        Returns:
            Configuration name string.
        """
        return self._config_name

    def get_device_name(self) -> str | None:
        """Returns name of the device.

        Returns:
            Device name string or None if not set.
        """
        return self._device

    def get_board_name(self) -> str | None:
        """Returns name of the board.

        Returns:
            Board name string or None if not set.
        """
        return self._board

    def set_doxygen_name_descr(self, name: str, descr: str) -> None:
        """Sets doxygen name and description of the configuration.

        Args:
            name: Doxygen name to set.
            descr: Doxygen description to set.
        """
        self._dox_name = name
        self._dox_descr = descr

    def set_config_name(self, name: str) -> None:
        """Sets name of the configuration.

        Args:
            name: Configuration name to set.
        """
        self._config_name = name

    def set_device(self, device: str, board: str | None = None) -> None:
        """Sets device in the configuration.

        Args:
            device: Device name to set.
            board: Optional board name to set.
        """
        self._device = device
        if board:
            self._board = board

    def get_by_did(self, did: int) -> DOM | LM | None:
        """Returns domain or logical machine by domain ID.

        Args:
            did: Domain ID to look up.

        Returns:
            Domain or logical machine object, or None when invalid domain ID is provided or the domain is not configured.
        """
        if 0 <= did < len(self._domains):
            return self._domains[did]
        return None

    def get_all_non_lm_domains(self) -> List[DOM]:
        """Returns all pure DOM domains which are not LMs"""
        return [dom for dom in self._domains if dom is not None and not isinstance(dom, LM)]

    def get_all_debug_domains(self) -> List[DOM | LM]:
        """Returns all domains that have debug property enabled.

        Returns:
            List of domains with debug property enabled.
        """
        return [dom for dom in self._domains if dom is not None and dom.is_debug()]

    def add_dom(self, dom: DOM) -> None:
        """Adds domain to this configuration.

        Args:
            dom: Domain to add.

        Raises:
            CfgToolException: If domain ID is already used by another domain.
        """
        existing = self.get_by_did(dom.get_did())
        if existing:
            raise CfgToolException(f"{dom.get_id()} uses did={dom.get_did()} which is already used by {existing.get_id()}")
        self._domains[dom.get_did()] = dom

    def add_lm(self, lm: LM) -> None:
        """Adds logical machine to this configuration.

        Args:
            lm: Logical machine to add.
        """
        self.add_dom(lm)
        self._lmm.append(lm)

    def get_all_lms(self) -> List[LM]:
        """Returns all logical machines.

        Returns:
            List of all logical machines.
        """
        return self._lmm

    def get_all_scmi_lms(self) -> List[LM]:
        """Returns all SCMI logical machines.

        Returns:
            List of logical machines with SCMI RPC type.
        """
        return [lm for lm in self._lmm if lm.get_rpc() == "scmi"]

    def get_all_agents(self) -> List[ScmiAgent]:
        """Returns all agents of all logical machines.

        Returns:
            List of all agents from all logical machines.
        """
        result = []
        for logical_machine in self._lmm:
            for agent in logical_machine.get_all_agents():
                result.append(agent)
        return result

    def get_all_scmi_agents(self) -> List[ScmiAgent]:
        """Returns all SCMI agents of all logical machines.

        Returns:
            List of all SCMI agents from all logical machines.
        """
        result = []
        for logical_machine in self._lmm:
            for agent in logical_machine.get_all_agents():
                if isinstance(agent, ScmiAgent):
                    result.append(agent)
        return result

    def get_all_channels(self) -> List[Channel]:
        """Returns all channels from all agents.

        Returns:
            List of all channels from all agents.
        """
        result = []
        for agent in self.get_all_agents():
            result += agent.get_all_channels()
        return result

    def get_all_smt_channels(self) -> List[SmtChannel]:
        """Returns all SMT channels from all agents.

        Returns:
            List of all SMT channels from all agents.
        """
        result = [typing.cast(SmtChannel, ch) for ch in self.get_all_channels() if ch.get_type() == "smt"]
        return result

    def get_all_scmi_channels(self) -> List[ScmiChannel]:
        """Returns all SCMI channels from all SCMI agents.

        Returns:
            List of all SCMI channels from all SCMI agents.
        """
        result = []
        for agent in self.get_all_scmi_agents():
            result += agent.get_all_scmi_channels()
        return result

    def get_max_scmi_channel_notify(self) -> int:
        """Returns maximal SCMI channel notify property.

        Returns:
            Maximum depth of notification buffer across all SCMI channels.
        """
        all_scmi_channels = self.get_all_scmi_channels()
        maximum = 1
        for channel in all_scmi_channels:
            maximum = max(maximum, channel.get_notify())
        return maximum

    def get_lm_id(self, logical_machine: LM) -> int:
        """Returns ID of the logical machine in the configuration.

        Args:
            logical_machine: Logical machine to find ID for.

        Returns:
            ID of the logical machine in the configuration.

        Raises:
            CfgToolException: When the logical machine could not be found.
        """
        all_logical_machines = self._lmm
        if logical_machine in all_logical_machines:
            return all_logical_machines.index(logical_machine)
        raise CfgToolException(f"Cannot determine LM instance index for {logical_machine.get_id()}")

    def get_default_lm(self) -> LM | None:
        """Returns the default logical machine.

        Returns:
            Default logical machine or None if no default is set.
        """
        for logical_machine in self._lmm[::-1]:
            if logical_machine.get_default():
                return logical_machine
        return None

    def get_lm_of_agent(self, agent: ScmiAgent) -> LM | None:
        """Returns the LM that contains the given agent.

        Args:
            agent: Agent to find the containing LM for.

        Returns:
            Logical machine that contains the agent, or None if not found.
        """
        for lm in self._lmm:
            if agent in lm.get_all_agents():
                return lm
        return None

    def get_lm_rpc_inst(self, lm: LM) -> int:
        """Returns RPC instance number of the RPC type used by given logical machine.

        Args:
            lm: Logical machine to get RPC instance for.

        Returns:
            RPC instance number.

        Raises:
            CfgToolException: If RPC instance index cannot be determined.
        """
        if lm.get_rpc():
            counter = 0
            for lm2 in self._lmm:
                if lm == lm2:
                    return counter
                if lm.get_rpc() == lm2.get_rpc():
                    counter += 1
        raise CfgToolException(f"Cannot determine RPC instance index for {lm.get_id()}")

    def get_all_lm_msels(self) -> List[MSEL]:
        """Returns MSELs from all logical machines.

        Returns:
            List of all MSELs from all logical machines.
        """
        result = []
        for logical_machine in self._lmm:
            result += logical_machine.get_all_msels()
        return result

    def get_max_msel_num(self) -> int:
        """Returns maximal amount of MSELs in all logical machines.

        Returns:
            Maximum number of MSELs across all logical machines.
        """
        result = 0
        for logical_machine in self._lmm:
            maximal_msels = logical_machine.get_max_msel_num()
            result = max(result, maximal_msels)
        return result

    def get_all_lm_start_stops(self, start: bool) -> List[StartStop]:
        """Returns all logical machine MSEL start-stops.

        Args:
            start: If True, returns start sequences; if False, returns stop sequences.

        Returns:
            List of start-stop sequences.
        """
        result = []
        for msel in self.get_all_lm_msels():
            if msel:
                result += msel.get_start() if start else msel.get_stop()
        return [start_stop for start_stop in result if start_stop is not None]

    def get_lm_start_stop_index(self, start_stop: StartStop, start: bool) -> int:
        """Returns index of given start-stop.

        Args:
            start_stop: Start-stop sequence to find index for.
            start: If True, searches in start sequences; if False, searches in stop sequences.

        Returns:
            Index of the start-stop sequence.

        Raises:
            CfgToolException: If start-stop index cannot be determined.
        """
        all_lm_start_stops = self.get_all_lm_start_stops(start)
        if start_stop in all_lm_start_stops:
            return all_lm_start_stops.index(start_stop)
        msel = start_stop.get_msel()
        raise CfgToolException(f"Cannot determine MSEL{msel.get_msel()} Start/Stop instance index for {msel.get_lm().get_id()}")

    def get_scmi_agent_id(self, agent: ScmiAgent) -> int:
        """Returns index of given SCMI agent.

        Args:
            agent: SCMI agent to find index for.

        Returns:
            Index of the SCMI agent.

        Raises:
            CfgToolException: If SCMI agent index cannot be determined.
        """
        all_scmi_agents = self.get_all_scmi_agents()
        if agent in all_scmi_agents:
            return all_scmi_agents.index(agent)
        raise CfgToolException(f"Cannot determine SCMI Agent instance index for {agent.get_id()}")

    def get_all_seenv_lms(self) -> List[LM]:
        """Returns all logical machines that have property 'seenv'.

        Returns:
            List of logical machines with 'seenv' property.
        """
        result = [lm for lm in self._lmm if lm.get_safe() == "seenv"]
        return result

    def get_all_seenv_agents(self) -> List[ScmiAgent]:
        """Returns all agents that are in logical machines with property 'seenv'.

        Returns:
            List of agents from logical machines with 'seenv' property.
        """
        result = []
        for slm in self.get_all_seenv_lms():
            result += slm.get_all_agents()
        return result

    def get_agent_seenv_id(self, agent: ScmiAgent) -> int:
        """Returns index of the SEENV agent.

        Args:
            agent: SCMI agent to get SEENV index for.

        Returns:
            SEENV index of the agent (1-based).

        Raises:
            CfgToolException: If SEENV index cannot be determined.
        """
        all_seenv_agents = self.get_all_seenv_agents()
        if agent in all_seenv_agents:
            return all_seenv_agents.index(agent) + 1
        raise CfgToolException(f"Cannot determine SCMI Agent's SEENV instance index for {agent.get_id()}")

    def get_channel_inst(self, searched_channel: Channel) -> int:
        """Return instance number of Channel within other channels of the same type.

        Args:
            searched_channel: Channel to find instance number for.

        Returns:
            Instance number of the channel within channels of the same type.

        Raises:
            CfgToolException: If channel instance index cannot be determined.
        """
        if searched_channel.get_type() != "none":
            all_channels = self.get_all_channels()
            i = 0
            for channel in all_channels:
                if channel == searched_channel:
                    return i
                if channel.get_type() == searched_channel.get_type():
                    i += 1
        raise CfgToolException("Cannot determine CHANNEL instance index")

    def get_all_message_unit_mailboxes(self) -> List[MailboxMu]:
        """Returns all mailbox messaging units.

        Returns:
            List of all message unit mailboxes.
        """
        result = [typing.cast(MailboxMu, agent.get_mailbox()) for agent in self.get_all_agents() if isinstance(agent.get_mailbox(), MailboxMu)]
        return result

    def get_all_message_unit_numbers(self) -> List[int]:
        """Returns all mailbox messaging units numbers.

        Returns:
            List of message unit numbers.
        """
        result = [typing.cast(MailboxMu, agent.get_mailbox()).get_mu() for agent in self.get_all_agents() if isinstance(agent.get_mailbox(), MailboxMu)]
        return result

    def get_all_loopback_mailboxes(self) -> List[MailboxLoopback]:
        """Returns all loopback mailboxes in the configuration.

        Returns:
            List of all loopback mailboxes.
        """
        result = [typing.cast(MailboxLoopback, agent.get_mailbox()) for agent in self.get_all_agents() if isinstance(agent.get_mailbox(), MailboxLoopback)]
        return result

    def get_mailbox_instance_index(self, searched_mailbox: Mailbox) -> int:
        """Returns instance number of Mailbox within other mailboxes of the same MB type.

        Args:
            searched_mailbox: Mailbox to find instance number for.

        Returns:
            Instance number of the mailbox within mailboxes of the same type.

        Raises:
            CfgToolException: If mailbox instance number cannot be determined.
        """
        if searched_mailbox.get_type():
            all_mailboxes = [a.get_mailbox() for a in self.get_all_agents()]
            i = 0
            for mailbox in all_mailboxes:
                if mailbox is None:
                    continue
                if mailbox == searched_mailbox:
                    return i
                if mailbox.get_type() == searched_mailbox.get_type():
                    i += 1
        raise CfgToolException(f"Cannot determine MAILBOX instance number for MB type='{searched_mailbox.get_type()}'")

    def get_all_lm_assignments(self) -> List[AssignedResource]:
        """Returns all logical machine resource assignments.

        Returns:
            List of all resource assignments from logical machines and their agents.
        """
        result = []
        for logical_machine in self._lmm:
            result += logical_machine.get_assigned_resources()
            for agent in logical_machine.get_all_agents():
                result += agent.get_assigned_resources()
        return result

    def get_all_dom_assignments(self) -> List[AssignedResource]:
        """Returns all domain resource assignments.

        Returns:
            List of all resource assignments from domains and their agents.
        """
        result = []
        for domain in self._domains:
            if domain:
                result += domain.get_assigned_resources()
                if isinstance(domain, LM):
                    for agent in domain.get_all_agents():
                        result += agent.get_assigned_resources()
        return result

    def get_all_bctrl_assignments(self) -> Dict[BctrlModel, List[AssignedResource]]:
        """Returns all block control resource assignments.

        Returns:
            Dictionary mapping block control models to their assigned resources.
        """
        result: Dict[BctrlModel, List[AssignedResource]] = {}
        for assigned_resource in self.get_all_lm_assignments():
            block_control_resources = assigned_resource.get_bctrl_resources()
            for resource in block_control_resources:
                block_control = ChipModelProvider.get_model().get_bctrl(resource.get_bctrl_id())
                if block_control is None:
                    source = "/".join(["user_config", assigned_resource.get_owner().get_name(), "BCTRL", resource.get_name()])
                    logger.warning("BCTRL %s does not exist", resource.get_bctrl_id(), extra={"source": source})
                    continue
                if block_control not in result:
                    result[block_control] = []
                if assigned_resource not in result[block_control]:
                    result[block_control].append(assigned_resource)
        return result

    def get_all_trdc_assignments(self) -> Dict[TrdcModel, List[AssignedResource]]:
        """Returns all TRDC resource assignments.

        Returns:
            Dictionary mapping TRDC models to their assigned resources.
        """
        result: Dict[TrdcModel, List[AssignedResource]] = {}
        for assigned_resource in self.get_all_dom_assignments():
            trdc_resources = assigned_resource.get_trdc_resources()
            for resource in trdc_resources:
                trdc = ChipModelProvider.get_model().get_trdc(resource.get_trdc_id())
                if trdc is None:
                    source = "/".join(["user_config", assigned_resource.get_owner().get_name(), resource.get_name()])
                    logger.warning("TRDC %s does not exist", resource.get_trdc_id(), extra={"source": source})
                    continue
                if trdc not in result:
                    result[trdc] = []
                if assigned_resource not in result[trdc]:
                    result[trdc].append(assigned_resource)
        return result

    @classmethod
    def get_all_default_mbc_assignments(cls, trdc: TrdcModel) -> List[Tuple[MbcResource, DefaultPermission]]:
        """Returns all MBC default resource assignments in given TRDC.

        Args:
            trdc: TRDC model to get MBC assignments for.

        Returns:
            List of tuples containing MBC resources and their default permissions.
        """
        result: List[Tuple[MbcResource, DefaultPermission]] = []
        atomic_resources = ResourceDatabaseProvider.get_database().atomic_resources()
        for resource in atomic_resources:
            if isinstance(resource, MbcResource):
                if resource.get_trdc_id() == trdc.get_id():
                    for default_permission in resource.get_default_permissions():
                        result.append((resource, default_permission))
        return result

    @classmethod
    def get_all_default_mrc_assignments(cls, trdc: TrdcModel) -> List[Tuple[MrcResource, DefaultPermission]]:
        """Returns all MRC default resource assignments in given TRDC.

        Args:
            trdc: TRDC model to get MRC assignments for.

        Returns:
            List of tuples containing MRC resources and their default permissions.
        """
        result: List[Tuple[MrcResource, DefaultPermission]] = []
        atomic_resources = ResourceDatabaseProvider.get_database().atomic_resources()
        for resource in atomic_resources:
            if isinstance(resource, MrcResource):
                if resource.get_trdc_id() == trdc.get_id():
                    for default_permission in resource.get_default_permissions():
                        result.append((resource, default_permission))
        return result

    def get_default_test_channel(self) -> int:
        """Returns default test channel or -1 if none is specified.

        Returns:
            Index of default test channel, or -1 if none is specified.
        """
        result = -1
        channels = self.get_all_scmi_channels()
        for channel in channels:
            if channel.get_test() == "default":
                result = channels.index(channel)
        return result

    @classmethod
    def get_owner_lm(cls, assigned_resource: AssignedResource) -> LM | None:
        """Returns logical machine that owns this assigned resource or the logical machine of the agent that owns it.

        Args:
            assigned_resource: Assigned resource to find owner for.

        Returns:
            Logical machine that owns the resource, or None if owner is not set properly.
        """
        owner = assigned_resource.get_owner()
        if isinstance(owner, LM):
            return owner
        if isinstance(owner, ScmiAgent):
            return owner.get_owner()
        source = "/".join(["user_config", assigned_resource.get_resource().get_name()])
        logger.error("Owner of the assigned resource '%s' is not set", assigned_resource, extra={"source": source})
        return None

    def get_assignment_json(self) -> object:
        """Returns dictionary with all assigned resources.

        Returns:
            Dictionary containing all assigned resources and configuration data.
        """
        lms: List[object] = []
        doms: List[object] = []
        board_configs: List[Dict[str, str | FormatedInt]] = []
        board_configs_custom: List[Dict[str, Any]] = []
        mak_variables: List[Dict[str, Any]] = []
        defines_list: List[object] = []
        cfg = {
            "name": self._config_name,
            "doxygen_name": self._dox_name,
            "description": self._dox_descr,
            "device": self._device,
            "board": self._board,
            "build_tool": self._build_tool,
            "board_configs": board_configs,
            "board_configs_custom": board_configs_custom,
            "mak_variables": mak_variables,
            "fusa": self._fusa.get_assignment_json(),
            "common_defines": defines_list,
        }

        ret = {
            "SMCT_version": ProductInfo.get_smct_version(),
            "SM_FW_compatibility_version": ProductInfo.get_sm_fw_compatible_version(),
            "Config": cfg,
            "LMs": lms,
            "DOMs": doms,
        }

        # Required board configs
        board_configs.append({"name": "DEBUG_UART_INSTANCE", "value": self.get_debug_uart_instance()})
        board_configs.append({"name": "DEBUG_UART_BAUDRATE", "value": self.get_debug_uart_baudrate()})
        board_configs.append({"name": "I2C_INSTANCE", "value": self.get_pmic_i2c_instance()})
        board_configs.append({"name": "I2C_BAUDRATE", "value": self.get_pmic_i2c_baudrate()})

        for define in self._common_defines.values():
            defines_list.append(define.get_assignment_json())

        # Custom board configs
        for config in self._board_configs:
            name, value = config
            board_configs_custom.append({"name": name, "value": value})

        # MAK file variables
        for mak_variable in self._mak_variables:
            variable, value = mak_variable
            mak_variables.append({"name": variable.upper(), "value": str(value).upper()})

        for lm in self._lmm:
            lms.append(lm.get_assignment_json())
        for dom in self._domains:
            if dom is not None and dom not in self._lmm:
                doms.append(dom.get_assignment_json())
        ret.update(ResourceDatabaseProvider.get_database().get_automatic_resources_json())
        ret.update(ResourceDatabaseProvider.get_database().get_user_resources_json())

        return ret

    def set_debug_uart_instance(self, instance: FormatedInt) -> None:
        """Sets instance of UART used for debugging.

        Args:
            instance: UART instance to use for debugging.
        """
        self._debug_uart = (instance, self._debug_uart[1])

    def get_debug_uart_instance(self) -> FormatedInt:
        """Returns instance of UART used for debugging.

        Returns:
            UART instance used for debugging.
        """
        return self._debug_uart[0]

    def set_debug_uart_baudrate(self, baudrate: FormatedInt) -> None:
        """Sets baudrate of UART used for debugging.

        Args:
            baudrate: Baudrate to set for debug UART.
        """
        self._debug_uart = (self._debug_uart[0], baudrate)

    def get_debug_uart_baudrate(self) -> FormatedInt:
        """Returns baudrate of UART used for debugging.

        Returns:
            Baudrate of UART used for debugging.
        """
        return self._debug_uart[1]

    def set_pmic_i2c_instance(self, instance: FormatedInt) -> None:
        """Sets instance of I2C used to control PMIC.

        Args:
            instance: I2C instance to use for PMIC control.
        """
        self._pmic_i2c = (instance, self._pmic_i2c[1])

    def get_pmic_i2c_instance(self) -> FormatedInt:
        """Returns instance of I2C used to control PMIC.

        Returns:
            I2C instance used to control PMIC.
        """
        return self._pmic_i2c[0]

    def set_pmic_i2c_baudrate(self, baudrate: FormatedInt) -> None:
        """Sets baudrate of I2C used to control PMIC.

        Args:
            baudrate: Baudrate to set for PMIC I2C.
        """
        self._pmic_i2c = (self._pmic_i2c[0], baudrate)

    def get_pmic_i2c_baudrate(self) -> FormatedInt:
        """Returns baudrate of I2C used to control PMIC.

        Returns:
            Baudrate of I2C used to control PMIC.
        """
        return self._pmic_i2c[1]

    def add_board_config(self, config: str, value: str) -> None:
        """Adds unknown board configuration.

        Args:
            config: Configuration name to add.
            value: Configuration value to set.
        """
        self._board_configs.append((config, value))

    def get_board_configs(self) -> List[Tuple[str, str]]:
        """Returns board configurations other than the known ones.

        Returns:
            List of tuples containing board configuration names and values.
        """
        return self._board_configs

    def add_fusa_config(self, config: str, value: str | int, comment: str | None) -> None:
        """Adds FUSA configuration define.

        Args:
            config: Configuration value name.
            value: Value to set.
            comment: Optional comment for the configuration.
        """
        define = FusaDefine(config, value, comment)
        self._fusa.add_config(define)

    def get_fusa_configs(self) -> List[FusaDefine]:
        """Returns all FUSA configuration defines.

        Returns:
            List of FusaDefine objects.
        """
        return self._fusa.get_all_configs()

    def add_fusa_task(self, name: str, period: Any | None, task_type: str | None = None, comment: str | None = None) -> None:
        """Adds FUSA task.

        Args:
            name: Task name.
            period: Task period
            task_type: one of FusaTask.Types
            comment: Task comment
        """
        task = FusaTask(name, period, task_type, comment)
        self._fusa.add_task(task)

    def get_fusa_tasks(self) -> List[FusaTask]:
        """Returns all FUSA tasks.

        Returns:
            List of FusaTask objects.
        """
        return self._fusa.get_all_tasks()

    def load_configuration(self, folder: str) -> None:
        """Loads configuration from JSON file.

        Args:
            folder: Path to folder containing user_configuration.json file.
        """
        file_name = os.path.join(folder, "user_configuration.json")
        json_object = None
        if not os.path.exists(file_name):
            logger.error("File not found: %s", file_name, extra={"source": file_name})
            return
        with open(file_name, "r", encoding="utf-8") as file:
            json_object = json.load(file)

        validate_json(json_object, file_name, "user_schema.json", "critical")
        # Configuration initialization
        config = json_object["Config"]
        if config is None:
            raise CfgToolException("Configuration JSON does not contain base configuration section")
        lm_name = config["name"]
        dox_name = config["doxygen_name"]
        description = config["description"]
        device = config["device"]
        board = config["board"]
        build_tool = config["build_tool"]
        if None in [lm_name, dox_name, description, device, board, build_tool]:
            raise CfgToolException("Configuration section in Configuration is missing some elements")

        resource_parser = ResourceParser(device)
        resource_parser.parse_soc_resources()

        self.set_config_name(lm_name)
        self.set_doxygen_name_descr(dox_name, description)
        self.set_device(device, board)
        self.set_build_tool(build_tool)

        for board_config in config["board_configs"]:
            name = board_config["name"]
            value = board_config["value"]
            match name:
                case "DEBUG_UART_INSTANCE":
                    self.set_debug_uart_instance(FormatedInt(value))
                case "DEBUG_UART_BAUDRATE":
                    self.set_debug_uart_baudrate(FormatedInt(value))
                case "I2C_INSTANCE":
                    self.set_pmic_i2c_instance(FormatedInt(value))
                case "I2C_BAUDRATE":
                    self.set_pmic_i2c_baudrate(FormatedInt(value))
                case _:
                    source = "/".join(["board_config", name])
                    validation_id = ".".join(["BOARD", name])
                    logger.warning("Unknown board config '%s' in %s", name, "board_configs", extra={"source": source, "validation_id": validation_id})
        for board_config in config["board_configs_custom"]:
            name = board_config["name"]
            value = board_config["value"]
            self.add_board_config(name, value)

        fusa = config.get("fusa")
        if fusa:
            for fusa_def in fusa.get("defines", []):
                name = fusa_def.get("name")
                value = fusa_def.get("value")
                comment = fusa_def.get("comment")
                self.add_fusa_config(name, value, comment)
            for fusa_task in fusa.get("tasks", []):
                name = fusa_task.get("name")
                period = fusa_task.get("period")
                task_type = fusa_task.get("type")
                comment = fusa_task.get("comment")
                self.add_fusa_task(name, period, task_type, comment)

        for mak_variable in config["mak_variables"]:
            name = mak_variable["name"]
            value = mak_variable["value"]
            self.set_mak_variable(name, value)

        for common_define in config["common_defines"]:
            name = common_define["name"]
            params = common_define["params"]
            params_str = " ".join(f"{key}={val}" for key, val in params.items())
            define = AssignedDefine(name, params_str)
            self.set_common_define(define)

        # Logical machines initialization
        lms = ConfigLoader.load_configuration_handle_logical_machines(json_object["LMs"], self._common_defines)
        for lm in lms:
            self.add_lm(lm)

        # Domains initialization
        doms = ConfigLoader.load_config_handle_domains(json_object["DOMs"], self._common_defines)
        for dom in doms:
            self.add_dom(dom)

        if self.get_doxygen_name() is None:
            raise CfgToolException("Configuration was not loaded properly")

    def set_build_tool(self, build: str) -> None:
        """Sets the build tool.

        Args:
            build: Build tool name to set.
        """
        self._build_tool = build

    def get_build_tool(self) -> str:
        """Returns the build tool.

        Returns:
            Name of the build tool.
        """
        return self._build_tool

    def set_sm_fw_root_directory(self, directory: str) -> None:
        """Sets the SM FW root directory to the configuration.

        Args:
            directory: Path to SM FW root directory.
        """
        self._sm_fw_directory = directory

    def get_sm_fw_root_directory(self) -> str:
        """Returns the SM FW root directory.

        Returns:
            Path to the SM FW root directory.
        """
        return self._sm_fw_directory

    def get_mak_variables(self) -> List[Tuple[str, Any]]:
        """Returns MAK file variables.

        Returns:
            List of tuples containing MAK variable names and values.
        """
        return self._mak_variables

    def set_mak_variable(self, variable: str, value: Any) -> None:
        """Sets new MAK file variable to the configuration.

        Args:
            variable: Variable name to set.
            value: Variable value to set.
        """
        self._mak_variables.append((variable, value))

    def set_common_define(self, define: AssignedDefine) -> None:
        """Sets common define to the configuration.

        Args:
            define: AssignedDefine object to add to common defines.
        """
        self._common_defines[define.get_name()] = define

    def get_common_define(self, name: str) -> AssignedDefine | None:
        """Returns common define or None if not specified.

        Args:
            name: Name of the common define to retrieve.

        Returns:
            AssignedDefine object if found, None otherwise.
        """
        if name in self._common_defines:
            return self._common_defines[name]
        return None

    def get_common_defines(self) -> Dict[str, AssignedDefine]:
        """Returns all common define names as a list"""
        return self._common_defines
