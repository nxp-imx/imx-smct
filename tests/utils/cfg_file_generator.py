#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause

"""Module related to generation of test CFG files"""

import json
from dataclasses import dataclass
from io import StringIO
from typing import Any, Dict, List


class Base:
    """Base class for configuration data structures."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert object to dictionary representation.

        Returns:
            Dictionary representation of the object
        """
        return vars(self)


@dataclass
class AccessRight(Base):
    """Access right representation"""

    name: str
    parameters: Dict[str, str]


@dataclass
class AssignedResource(Base):
    """Resource assignment representation"""

    name: str
    template: str
    parameters: Dict[str, str]


@dataclass
class Domain(Base):
    """Domain section representation"""

    id: str
    name: str
    did: int
    access_rights: Dict[str, AccessRight]
    assigned_resources: Dict[str, AssignedResource]


@dataclass
class Mode(Base):
    """Mode command representation"""

    msel: int
    boot: int


@dataclass
class StartStop(Base):
    """Start/stop assignment representation"""

    resource: str
    start: int | None
    stop: int | None


@dataclass
class Channel(Base):
    """Channel command representation"""

    db: int
    xport: str
    check: str
    rpc: str
    type: str
    test: str | None
    notify: int | None


@dataclass
class Mailbox(Base):
    """Mailbox section representation"""

    type: str
    mu: int | None
    test: int | None
    priority: str | None
    channels: List[Channel]


@dataclass
class Agent(Base):
    """Agent section representation"""

    id: str
    name: str
    access_rights: Dict[str, AccessRight]
    mailboxes: List[Mailbox]
    assigned_resources: Dict[str, AssignedResource]


@dataclass
class LogicalMachine(Base):
    """Logical machine section representation"""

    id: str
    name: str
    did: int
    boot: int
    skip: int
    safe: str
    rpc: str
    access_rights: Dict[str, AccessRight]
    assigned_resources: Dict[str, AssignedResource]
    modes: List[Mode]
    start_stops: Dict[bool, List[StartStop]]
    agents: Dict[str, Agent]


@dataclass
class Configuration:
    """Complete configuration data structure."""

    access_rights: Dict[str, AccessRight]
    domains: Dict[str, Domain]
    logical_machines: Dict[str, LogicalMachine]
    make_command: Dict[str, str]
    dox_command: Dict[str, str]
    board_command: Dict[str, str]
    device_cfg_path: str


def format_parameters(parameters: Dict[str, Any]) -> str:
    """Formats given parameters to CFG file parameters format"""
    return ", ".join(f"{a}={b}" if b is not None else a for a, b in parameters.items())


def _parse_resource_assignment(json_list: List[Dict[str, Any]]) -> Dict[str, AssignedResource]:
    """Parses resource assignments from given list"""
    result = {}
    for assignment in json_list:
        name = assignment["name"]
        template = assignment["template"]
        parameters = {}
        if "parameters" in assignment:
            parameters = assignment["parameters"]
        result[name] = AssignedResource(name, template, parameters)
    return result


def _parse_common_access_rights(json_list: List[Dict[str, Any]]) -> Dict[str, AccessRight]:
    """Parses common access rights from given list"""
    result = {}
    for json_access_right in json_list:
        name = json_access_right["name"]
        parameters = {}
        if "parameters" in json_access_right:
            parameters = json_access_right["parameters"]
        result[name] = AccessRight(name, parameters)
    return result


def _parse_modes(json_list: List[Dict[str, Any]]) -> List[Mode]:
    """Parses mode related information from given list"""
    result = []
    for json_mode in json_list:
        msel = json_mode["msel"]
        boot = json_mode["boot"]
        result.append(Mode(msel, boot))
    return result


def _parse_start_stops(json_list: List[Dict[str, Any]]) -> Dict[bool, List[StartStop]]:
    """Parses start/stop information from given list"""
    starts = []
    stops = []
    for json_start_stop in json_list:
        resource = json_start_stop["resource"]
        start = None
        stop = None
        if "start" in json_start_stop:
            start = json_start_stop["start"]
        if "stop" in json_start_stop:
            stop = json_start_stop["stop"]
        start_stop = StartStop(resource, start, stop)
        if start is not None:
            starts.append(start_stop)
        if stop is not None:
            stops.append(start_stop)
    return {True: starts, False: stops}


def _parse_mailboxes(json_list: List[Dict[str, Any]]) -> List[Mailbox]:
    """Parses mailbox related information from given list"""
    result = []
    for json_mailbox in json_list:
        mailbox_type = json_mailbox["type"]
        test = json_mailbox["test"]
        mu = None
        if "mu" in json_mailbox:
            mu = json_mailbox["mu"]
        priority = json_mailbox["priority"]
        channels = _parse_channels(json_mailbox["channels"])
        result.append(Mailbox(mailbox_type, mu, test, priority, channels))
    return result


def _parse_channels(json_list: List[Dict[str, Any]]) -> List[Channel]:
    """Parses channel related information from given list"""
    result = []
    for json_channel in json_list:
        db = json_channel["db"]
        xport = json_channel["xport"]
        check = json_channel["check"]
        rpc = json_channel["rpc"]
        channel_type = json_channel["type"]
        test = None
        notify = None
        if "test" in json_channel:
            test = json_channel["test"]
        if "notify" in json_channel:
            notify = json_channel["notify"]
        result.append(Channel(db, xport, check, rpc, channel_type, test, notify))
    return result


def _parse_domains(json_list: List[Dict[str, Any]]) -> Dict[str, Domain]:
    """Parses domain related information from the given list"""
    result = {}
    for json_access_right in json_list:
        domain_id = json_access_right["id"]
        name = json_access_right["name"]
        did = json_access_right["did"]
        json_access_rights: List[Dict[str, Any]] = json_access_right["access_rights"]
        access_rights = _parse_common_access_rights(json_access_rights)
        assigned_resources = _parse_resource_assignment(json_access_right["assigned_resources"])
        result[domain_id] = Domain(domain_id, name, did, access_rights, assigned_resources)
    return result


def _parse_logical_machines(json_object: List[Dict[str, Any]]) -> Dict[str, LogicalMachine]:
    """Parses logical machine related information from the given list"""
    result = {}
    for json_logical_machine in json_object:
        lm_id = json_logical_machine["id"]
        name = json_logical_machine["name"]
        did = json_logical_machine["did"]
        boot = json_logical_machine["boot"]
        skip = json_logical_machine["skip"]
        safe = json_logical_machine["safe"]
        rpc = json_logical_machine["rpc"]
        access_rights = {}
        if "access_rights" in json_logical_machine:
            access_rights = _parse_common_access_rights(json_logical_machine["access_rights"])
        assigned_resources = {}
        if "assigned_resources" in json_logical_machine:
            assigned_resources = _parse_resource_assignment(json_logical_machine["assigned_resources"])
        modes = []
        if "modes" in json_logical_machine:
            modes = _parse_modes(json_logical_machine["modes"])
        start_stops = {}
        if "start_stops" in json_logical_machine:
            start_stops = _parse_start_stops(json_logical_machine["start_stops"])
        agents = {}
        if "agents" in json_logical_machine:
            agents = _parse_agents(json_logical_machine["agents"])

        result[lm_id] = LogicalMachine(lm_id, name, did, boot, skip, safe, rpc, access_rights, assigned_resources, modes, start_stops, agents)
    return result


def _parse_agents(json_object: List[Dict[str, Any]]) -> Dict[str, Agent]:
    """Parses agent related information from given list"""
    result = {}
    for json_access_right in json_object:
        agent_id = json_access_right["id"]
        name = json_access_right["name"]
        json_access_rights: List[Dict[str, Any]] = json_access_right["access_rights"]
        access_rights = _parse_common_access_rights(json_access_rights)
        assigned_resources = _parse_resource_assignment(json_access_right["assigned_resources"])
        mailboxes = _parse_mailboxes(json_access_right["mailboxes"])

        result[agent_id] = Agent(agent_id, name, access_rights, mailboxes, assigned_resources)
    return result


class CfgFileGenerator:
    """Generator of test CFG files"""

    def __init__(self, config: Configuration) -> None:
        self._buffer = StringIO()
        self._configuration: Configuration = config

    @classmethod
    def from_dict(cls, dictionary: Dict[str, Any]) -> "CfgFileGenerator":
        """Create generator from dictionary"""
        required_keys_in_dict = ["common_access_rights", "domains", "logical_machines", "make", "dox", "board", "device_include_path"]
        for key in required_keys_in_dict:
            if key not in dictionary:
                raise KeyError(f"Key {key} is required in the input dictionary")

        common_access_rights: List[Dict[str, Any]] = dictionary["common_access_rights"]
        domains: List[Dict[str, Any]] = dictionary["domains"]
        logical_machines: List[Dict[str, Any]] = dictionary["logical_machines"]
        make: Dict[str, str] = dictionary["make"]
        dox_dict: Dict[str, str] = dictionary["dox"]
        board_dict: Dict[str, str] = dictionary["board"]
        device_include_path: str = dictionary["device_include_path"]

        configuration = Configuration(
            _parse_common_access_rights(common_access_rights),
            _parse_domains(domains),
            _parse_logical_machines(logical_machines),
            make,
            dox_dict,
            board_dict,
            device_include_path,
        )
        return cls(configuration)

    @classmethod
    def from_json(cls, json_file: str) -> "CfgFileGenerator":
        """Create generator from JSON file"""
        with open(json_file, "r", encoding="utf-8") as file:
            return cls.from_dict(json.load(file))

    def generate(self) -> None:
        """Generates content of the CFG file based on the loaded dictionary of information"""
        self._generate_make_command()
        self._generate_dox_command()
        self._print("")

        self._generate_include_device()
        self._print("")

        self._generate_board_commands()
        self._print("")

        self._print("# Common access rights")
        self._generate_access_rights(list(self._configuration.access_rights.values()))
        self._print("")
        self._generate_domains()
        self._print("# Logical machines")
        self._print("")
        self._generate_logical_machines()

    def get_result(self) -> str:
        """Returns content of the content buffer"""
        position = self._buffer.tell()
        self._buffer.seek(0)
        content = self._buffer.read()
        self._buffer.seek(position)
        return content

    def _generate_include_device(self) -> None:
        """Generates include path for the device CFG file"""
        if self._configuration:
            device_cfg_path = self._configuration.device_cfg_path.replace("\\", "/")  # Path must be in Linux format even on Windows
            self._print(f"include {device_cfg_path}")

    def _generate_dox_command(self) -> None:
        """Generates DOX command"""
        self._print(f'DOX     name={self._configuration.dox_command["name"]}, desc="{self._configuration.dox_command["description"]}"')

    def _generate_make_command(self) -> None:
        """Generates MAKE command"""
        self._print(
            f'MAKE    soc={self._configuration.make_command["soc"]}, board={self._configuration.make_command["board"]}, build={self._configuration.make_command["build_tool"]}'
        )

    def _generate_board_commands(self) -> None:
        """Generates BOARD commands"""
        for key, value in self._configuration.board_command.items():
            self._print(f"BOARD               {key}={value}")

    def _generate_domains(self) -> None:
        """Generates DOMn commands and all domain related content"""
        for domain in self._configuration.domains.values():
            self._print(f'{domain.id}                name="{domain.name}", did={domain.did}')
            self._print("")
            self._generate_access_rights(list(domain.access_rights.values()))
            self._print("")
            self._generate_assignments(list(domain.assigned_resources.values()))

    def _generate_logical_machines(self) -> None:
        """Generates LMn commands and all logical machine related content"""
        for logical_machine in self._configuration.logical_machines.values():
            parameters = {
                "did": logical_machine.did,
                "name": logical_machine.name,
                "rpc": logical_machine.rpc,
                "boot": logical_machine.boot,
                "skip": logical_machine.skip,
                "safe": logical_machine.safe,
            }
            parameters_str = format_parameters(parameters)
            self._print(f"{logical_machine.id}                {parameters_str}")
            self._print("")
            self._generate_access_rights(list(logical_machine.access_rights.values()))
            self._print("")
            self._generate_modes(logical_machine.modes)
            self._print("")
            self._generate_assignments(list(logical_machine.assigned_resources.values()))
            self._print("")
            self._generate_agents(list(logical_machine.agents.values()))
            self._print("")
            self._print("")

    def _generate_modes(self, modes: List[Mode]) -> None:
        """Generates MODE commands from given list"""
        for mode in modes:
            self._print(f"MODE             msel={mode.msel}, boot={mode.boot}")

    def _generate_agents(self, agents: List[Agent]) -> None:
        """Generates AGENT commands and all agent related content"""
        for agent in agents:
            self._print(f"{agent.id}             name={agent.name}")
            self._generate_mailboxes(agent.mailboxes)
            self._print("")
            self._generate_access_rights(list(agent.access_rights.values()))
            self._print("")
            self._generate_assignments(list(agent.assigned_resources.values()))

    def _generate_assignments(self, assignments: List[AssignedResource]) -> None:
        """Generates section of resource assignments"""
        for assignment in assignments:
            separator = ", " if len(assignment.parameters) > 0 else ""
            parameters = separator + format_parameters(assignment.parameters)
            self._print(f"{assignment.name}         {assignment.template}{parameters}")

    def _generate_access_rights(self, access_rights: List[AccessRight]) -> None:
        """Generates section with access rights definitions"""
        for access_right in access_rights:
            self._print(f"{access_right.name}:               {format_parameters(access_right.parameters)}")

    def _generate_mailboxes(self, mailboxes: List[Mailbox]) -> None:
        """Generates MAILBOX command and all channels in this mailbox"""
        for mailbox in mailboxes:
            parameters = [f"type={mailbox.type}"]
            if mailbox.mu is not None:
                parameters.append(f"mu={mailbox.mu}")
            if mailbox.test is not None:
                parameters.append(f"test={mailbox.test}")
            if mailbox.priority is not None:
                parameters.append(f"priority={mailbox.priority}")
            parameters_str = ", ".join(parameters)
            self._print(f"MAILBOX              {parameters_str}")
            self._generate_channels(mailbox.channels)

    def _generate_channels(self, channels: List[Channel]) -> None:
        """Generates CHANNEL commands from given list"""
        for channel in channels:
            parameters = {"db": channel.db, "xport": channel.xport, "check": channel.check, "rpc": channel.rpc, "type": channel.type}
            if channel.test is not None:
                parameters["test"] = channel.test
            if channel.notify is not None:
                parameters["notify"] = channel.notify
            parameters_str = format_parameters(parameters)
            self._print(f"CHANNEL             {parameters_str}")

    def _print(self, text: str) -> None:
        """Prints given string into the content buffer"""
        print(text, file=self._buffer)
