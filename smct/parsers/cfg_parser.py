#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Module related to parser of the CFG files."""

import logging
import os.path
import re
import typing
from typing import Any, Dict, List, Sequence

from smct import utils
from smct.exceptions.cfg_tool_exception import CfgToolException
from smct.owners.owner_agent import ScmiAgent
from smct.owners.owner_dom import DOM
from smct.owners.owner_lm import LM
from smct.parsers.command_parser import CfgCommandParser, CommandParser
from smct.resources.res_api import ApiResource
from smct.resources.res_mdac import MdacResource
from smct.resources.resource_base import AtomicResource, MacroResource

from ..configuration.configuration_provider import ConfigurationProvider
from ..model.chip_model_provider import ChipModelProvider
from ..owners.owner_base import AssignedDefine, ResourceOwner
from ..resources.resource_database_provider import ResourceDatabaseProvider
from .cfg_resource_provider import CfgResourceProvider
from .hdr_parser import ApiResourceParser

_re_comment = re.compile(r"^\s*#")
_re_blank = re.compile(r"^\s*$")
_re_macro = re.compile(r"^\s*([A-Za-z0-9._]+)\s*:\s*([^#]*)")  # definition e.g: MACRO: VALUE
_re_include = re.compile(r"^\s*include\s+([A-Za-z0-9._/\\:\-]+)")
_re_bctrl_a_ipg_debug = re.compile(r"\bBCTRL_(\w)_IPG_DEBUG(_(\d+))?=((0x[0-9A-Fa-f]+)|(0b[0-1]+)|(\d+))")
_re_mdac_dfmt_x = re.compile(r"\b(DFMT(\d))\b")

logger = logging.getLogger()


class CfgFileMacro:
    """Config file macro object."""

    def __init__(self) -> None:
        self.name: str = ""
        self.value: str = ""
        self.file_name: str = ""
        self.file_line: int = 0


def _is_macro_parameter_name(name: str) -> bool:
    """Returns True if given name could be a macro resource parameter (used during cfg file parsing).

    Args:
        name: The name to check.

    Returns:
        True if the name could be a macro resource parameter, False otherwise.
    """
    if str.islower(name[0]):
        return True
    return False


class CfgFileParser:
    """Parser for the configuration CFG file."""

    def __init__(self) -> None:
        self._macros: Dict[str, CfgFileMacro] = {}
        self._current_owner: ResourceOwner | None = None
        self._current_domain: DOM | None = None
        self._current_logical_machine: LM | None = None
        self._current_agent: ScmiAgent | None = None
        self._header_parser: ApiResourceParser | None = None
        self._mixes: List[str] = []
        self._root_directory: str | None = None
        self._current_file: str | None = None
        self._current_line: int | None = None
        self._expanded_defines: List[AssignedDefine] = []
        self._include_list: List[str] = []
        self._command_parser: CommandParser | None = None

    def set_command_parser(self, command_parser: CommandParser) -> None:
        """Sets the command parser.

        Args:
            command_parser: The command parser to set.
        """
        self._command_parser = command_parser

    def enable_board_parser(self, header_parser: ApiResourceParser, root_directory: str) -> None:
        """Enables parsing of board files.

        Args:
            header_parser: The header parser to use for board files.
            root_directory: The root directory for parsing.
        """
        self._header_parser = header_parser
        self._root_directory = root_directory  # needed when _header_parser is set

    def get_macro(self, name: str) -> CfgFileMacro | None:
        """Returns macro by its name or None if such macro was not parsed.

        Args:
            name: The name of the macro to retrieve.

        Returns:
            CfgFileMacro instance if found, None otherwise.
        """
        if name in self._macros:
            return self._macros[name]
        return None

    def get_current_file(self) -> str | None:
        """Gets the current file being parsed.

        Returns:
            The path to the current file being parsed, or None if no file is being parsed.
        """
        return self._current_file

    def get_current_line(self) -> int | None:
        """Gets the current line of file being parsed.

        Returns:
            The line number of the  current file being parsed, or None if no file is being parsed.
        """
        return self._current_line

    def get_current_logical_machine(self) -> LM | None:
        """Gets the current logical machine.

        Returns:
            The current logical machine instance, or None if no logical machine is set.
        """
        return self._current_logical_machine

    def get_current_agent(self) -> ScmiAgent | None:
        """Gets the current SCMI agent.

        Returns:
            The current SCMI agent instance, or None if no agent is set.
        """
        return self._current_agent

    def set_current_resource_owner(self, owner: ResourceOwner) -> None:
        """Sets the current resource owner.

        Args:
            owner: The resource owner to set as current.
        """
        self._set_current_resource_owner(owner)

    def get_header_parser(self) -> ApiResourceParser | None:
        """Gets the header parser instance.

        Returns:
            The header parser instance, or None if no header parser is set.
        """
        return self._header_parser

    def get_root_directory(self) -> str | None:
        """Gets the root directory for parsing.

        Returns:
            The root directory path, or None if no root directory is set.
        """
        return self._root_directory

    def _expand_line(self, line: str) -> str:
        """Expand one line by replacing all known macros.

        Args:
            line: The line to expand.

        Returns:
            The expanded line with macros replaced.
        """
        line = line.replace("\n", " ")
        line = line.replace("\r", " ")
        previous_line = ""

        # expand all repeatedly (multi-level expansion)
        used_macro_resources = []
        while line != previous_line:
            previous_line = line
            atoms = utils.parse_line_to_atoms(line)
            if atoms and len(atoms) > 0:
                for atom in atoms:
                    macro_resource = ResourceDatabaseProvider.get_database().find_macro_resource(atom)
                    if macro_resource:
                        if atom not in used_macro_resources:
                            # Macro resources do not expand to atomic resources, but they may contain more
                            # so, expand everything which is NOT a valid atomic resource
                            used_macro_resources.append(atom)  # do not do it again for this one
                            for param in macro_resource.get_parameters():
                                line = line + " " + param
                        continue
                    if atom in self._macros:
                        define = AssignedDefine(atom, self._macros[atom].value)
                        if ConfigurationProvider.get_configuration().get_common_define(atom) is None:
                            self._get_current_resource_owner().assign_define(define)
                        ResourceDatabaseProvider.get_database().add_define(define)
                        self._expanded_defines.append(define)
                    if atom in self._macros:
                        line = line.replace(atom, self._macros[atom].value)

        # remove commas and multi-spaces. Turn them to single space delimiters
        line = re.sub(r",", " ", line)
        line = re.sub(r"\s+", " ", line)
        line = line.strip()
        return line

    def _set_current_resource_owner(self, owner: ResourceOwner) -> None:
        """Sets current domain, logical machine or SCMI agent as owner of following resources.

        Args:
            owner: The resource owner to set as current.
        """
        if isinstance(owner, LM):
            owner = typing.cast(LM, owner)
            self._current_owner = owner
            self._current_domain = None
            self._current_logical_machine = owner
            self._current_agent = None
        elif isinstance(owner, ScmiAgent):
            owner = typing.cast(ScmiAgent, owner)
            self._current_owner = owner
            self._current_domain = None
            self._current_agent = owner
        elif isinstance(owner, DOM):
            owner = typing.cast(DOM, owner)
            self._current_owner = owner
            self._current_domain = owner
            self._current_logical_machine = None
            self._current_agent = None
        elif owner.get_id() == "BOARD":
            # parsing BOARD command, no owner but need to define something for common_defines
            self._current_owner = owner
            self._current_domain = None
            self._current_logical_machine = None
            self._current_agent = None

    def _get_current_resource_owner(self) -> ResourceOwner:
        """Returns current resource owner.

        Returns:
            The current resource owner.
        """
        return typing.cast(ResourceOwner, self._current_owner)

    def _parse_line(self, line: str, file_path: str, line_num: int) -> None:
        """Parse processed lines to catch TRDC_CONFIG_a, BCTRL_CONFIG_x etc.

        Args:
            line: The line of text to parse.
            file_path: The path to the file being parsed.
            line_num: The line number in the file.
        """
        if self._command_parser is None:
            logger.error("Command parser not initialized", extra={"source": file_path})
            return

        commands: list[tuple[re.Pattern[str], typing.Callable]] = [
            (re.compile(r"\bTRDC_CONFIG_(\w+)\b"), self._command_parser.parse_command_trdc_config_a),
            (re.compile(r"\bBCTRL_CONFIG_(\w)\b"), self._command_parser.parse_command_bctrl_config_a),
            (re.compile(r"\bDOM(\d+)\b"), self._command_parser.parse_command_dom_n),
            (re.compile(r"\bLM(\d+)\b"), self._command_parser.parse_command_lm_n),
            (re.compile(r"\bSCMI_AGENT(\d*)\b"), self._command_parser.parse_command_scmi_agent_n),
            (re.compile(r"\bDEBUG\b"), self._command_parser.parse_command_debug),
            (re.compile(r"\bMIX\b"), self._command_parser.parse_command_mix),
            (re.compile(r"\bMAKE\b"), self._command_parser.parse_command_make),
            (re.compile(r"\bDOX\b"), self._command_parser.parse_command_dox),
            (re.compile(r"\bMAILBOX\b"), self._command_parser.parse_command_mailbox),
            (re.compile(r"\bCHANNEL\b"), self._command_parser.parse_command_channel),
            (re.compile(r"\bMODE\b"), self._command_parser.parse_command_mode),
            (re.compile(r"\b((LMM)_\d+)\b"), self._command_parser.parse_command_auto_create_res),
            (re.compile(r"\b((BASE)_\d+)\b"), self._command_parser.parse_command_auto_create_res),
            (re.compile(r"\bBOARD\b"), self._command_parser.parse_command_board),
            (re.compile(r"\bFUSA_DEF\b"), self._command_parser.parse_command_fusa_def),
            (re.compile(r"\bFUSA_TASK\b"), self._command_parser.parse_command_fusa_task),
        ]

        self._current_line = line_num

        atoms_list = utils.parse_line_to_atoms(line)
        # first, try to process the command
        is_hit = False
        if atoms_list and len(atoms_list) > 0:
            first = atoms_list[0]  # the command is the first atom of the line
            for cmd in commands:
                match = cmd[0].match(first)
                if match:
                    command_return_value: bool | None = cmd[1](match, atoms_list, self)
                    if not command_return_value:
                        is_hit = True  # if handler returns True, the processing continues

        # next, process the resource assignment
        if not is_hit and isinstance(self._command_parser, CfgCommandParser):
            for atom in atoms_list:
                macro = ResourceDatabaseProvider.get_database().find_macro_resource(atom)
                resources: Sequence[AtomicResource | MacroResource] = []
                if macro:
                    resources = [macro]
                else:
                    resources = ResourceDatabaseProvider.get_database().find_atomic_resource_by("name", atom)

                if len(resources) == 0:
                    resources = ResourceDatabaseProvider.get_database().find_atomic_resource_by("desc", atom)
                if len(resources) == 1:
                    resource = resources[0]
                    is_startstop = False
                    # is any extra parameter required by a macro resource (e.g. DFMT1)?
                    if isinstance(resource, MacroResource):
                        parameters = resource.get_parameters()
                        for res_param in parameters:
                            # the macro resource requires a parameter,
                            # it needs to exist as a text macro in current parsing context
                            if res_param in self._macros:
                                # text macro really exists, get the text macro value and add it to the list of atoms
                                # so it can be consumed by the resource assignment
                                res_param_macro = self._macros[res_param]
                                atoms_list.extend(utils.parse_line_to_atoms(res_param_macro.value))

                    if self._current_logical_machine is not None:
                        is_startstop = self._current_logical_machine.handle_start_stops(resource, atoms_list)
                    if self._current_owner:
                        if not is_startstop:
                            # assign resource to current owner if it exists, remember if it comes from external include file
                            ignore_api_check = (
                                self._current_owner.get_id() == "LM0"
                                or (isinstance(self._current_owner, ScmiAgent) and self._current_owner.get_owner().get_id() == "LM0")
                                or isinstance(self._current_owner, DOM)
                            )
                            assignment = self._current_owner.assign_resource(resource, atoms_list, self._expanded_defines, ignore_api_check=ignore_api_check)
                            if assignment:
                                assignment.set_dirty_flag(len(self._include_list) == 0)
                    else:
                        # this may happen e.g. when setting did=0-15,perm=0 defaults
                        bad_owner = DOM("DOM_BAD", 0)
                        bad_assigned_resource = bad_owner.assign_resource(resource, atoms_list)
                        if bad_assigned_resource:
                            source = "/".join(["user_config", resource.get_name()])
                            logger.error("Invalid resource assignment of '%s'", resource.get_name(), extra={"source": source})
                else:
                    if str.upper(atom[0]) == atom[0]:
                        source = "/".join([file_path, atom])
                        logger.warning("%s::%i: Unknown command/assignment '%s'", file_path, line_num, atom, extra={"source": source})

        self._current_line = None

    def _process_macro(self, configuration_macro: CfgFileMacro) -> None:
        """Processes the configuration macro and creates the macro resource in resource database.

        Args:
            configuration_macro: The configuration macro to process
        """
        skip = False
        if self._current_owner is not None and self._current_owner.get_id() == "BOARD":
            hit = False
            param_atoms = utils.parse_line_to_atoms(configuration_macro.value)
            for param_atom in param_atoms:
                if ResourceDatabaseProvider.get_database().find_atomic_resource_by("name", param_atom):
                    hit = True
            if not hit:
                define = AssignedDefine(configuration_macro.name, configuration_macro.value)
                ConfigurationProvider.get_configuration().set_common_define(define)
        self._macros[configuration_macro.name] = configuration_macro
        if _re_blank.match(configuration_macro.value):
            # blank macro may mean "removal" of automatic atomic resource
            resources = ResourceDatabaseProvider.get_database().find_atomic_resource_by("name", configuration_macro.name)
            if len(resources) == 0:
                return
            if len(resources) > 1:
                source = "/".join([configuration_macro.file_name, configuration_macro.name])
                logger.error("There are multiple atomic resources with name '%s'", configuration_macro.name, extra={"source": source})
                return
            atomic = resources[0]
            if isinstance(atomic, ApiResource):
                skip = True
                atomic.set_auto(True)
        # process the macro if not skipped
        if not skip:
            self._macros[configuration_macro.name] = configuration_macro
            macro = MacroResource(configuration_macro.name)

            # all atomic words in the macro value
            atoms = utils.parse_line_to_atoms(configuration_macro.value)
            if atoms:
                while len(atoms) > 0:
                    atom_name = atoms.pop(0)
                    atomic_resources = ResourceDatabaseProvider.get_database().find_atomic_resource_by("name", atom_name)
                    atom: AtomicResource | None = None

                    if len(atomic_resources) == 1:
                        # existing atomic resource
                        atom = atomic_resources[0]
                        macro.add_atomic_resource(atom)
                    elif len(atomic_resources) == 0:
                        # unknown atomic resource, use factory to create (try to create)
                        atom = CfgResourceProvider.atomic_resource_from_cfg_name(atom_name, configuration_macro.name, atoms)
                        if atom:
                            # name already exists?
                            old_name = atom.get_name()
                            for i in range(1, 100):
                                existing_resources = ResourceDatabaseProvider.get_database().find_atomic_resource_by("name", atom.get_name())
                                if len(existing_resources) > 0:
                                    atom.rename(f"{old_name}_{i}")
                                else:
                                    break
                            ResourceDatabaseProvider.get_database().add_atomic_resource(atom)
                            macro.add_atomic_resource(atom)
                        elif _is_macro_parameter_name(atom_name):
                            pass  # skip everything which looks like parameter
                        elif _re_mdac_dfmt_x.match(atom_name):
                            # HACK: make sure the DFMT is put to end
                            # (to be consumed by MDAC, but often it is sooner on line)
                            if len(atoms):
                                atoms.append(atom_name)
                            else:
                                macro.add_parameter(atom_name)
                        else:
                            found_macro = ResourceDatabaseProvider.get_database().find_macro_resource(atom_name)
                            if found_macro is not None:
                                source = "/".join([configuration_macro.file_name, configuration_macro.name])
                                logger.error(
                                    "Adding macro resource (%s) into macro resource (%s) is not permitted",
                                    atom_name,
                                    macro.get_name(),
                                    extra={"source": source},
                                )
                            source = "/".join([configuration_macro.file_name, configuration_macro.name])
                            logger.warning("Ignoring %s for macro resource %s", atom_name, configuration_macro.name, extra={"source": source})
                    else:
                        source = "/".join([configuration_macro.file_name, configuration_macro.name])
                        logger.error("Macro '%s' uses multiply-defined resources %s", configuration_macro.name, atom_name, extra={"source": source})
                    if atom:
                        self._consume_parameters(macro, atom, atoms)
            if not macro.is_empty():
                if self._current_owner is not None and self._current_owner.get_id() == "BOARD":
                    ResourceDatabaseProvider.get_database().add_user_resource(macro)
                ResourceDatabaseProvider.get_database().add_macro_resource(macro)

    def parse_file(self, file_path: str) -> None:
        """Parses the CFG file.

        Args:
            file_path: Path to the CFG file to parse
        """
        absolute_file_path = os.path.abspath(file_path)
        if not os.path.isfile(absolute_file_path):
            logger.error("Cannot parse file '%s'", file_path, extra={"source": absolute_file_path})
            return
        logger.info("Parsing %s", absolute_file_path, extra={"source": absolute_file_path})
        directory, _ = os.path.split(absolute_file_path)
        try:
            self._parse_file(absolute_file_path, directory, file_path)
        except (CfgToolException, IOError) as e:
            logger.critical("CFG file '%s' cannot be parsed due to following problem: %s", absolute_file_path, str(e), extra={"source": absolute_file_path})

    def _parse_file(self, absolute_file_path: str, directory: str, file_path: str) -> None:
        """Parses the CFG file.

        Args:
            absolute_file_path: Absolute path to the CFG file
            directory: Directory containing the CFG file
            file_path: Original file path
        """
        self._current_file = absolute_file_path
        if not os.path.exists(absolute_file_path):
            logger.error("File not found: %s", absolute_file_path, extra={"source": absolute_file_path})
            return
        with open(absolute_file_path, "r", encoding="utf-8") as f:
            line = ""
            line_num = 0
            complete = True

            for ln in f.readlines():
                self._expanded_defines = []
                line_num = line_num + 1

                # was complete last time?
                if complete:
                    line = ""

                ln = ln.strip()
                if len(ln) == 0:
                    continue

                complete = ln[-1] != "\\"
                if complete:
                    line += ln
                else:
                    line += ln[:-1]
                    continue

                if _re_comment.match(line) or _re_blank.match(line):
                    continue

                # backup raw line and continue with expanded line
                line = self._expand_line(line)

                match_object = _re_include.match(line)
                if match_object:
                    fname2 = os.path.join(directory, match_object.group(1))
                    self._include_list.append(fname2)
                    self.parse_file(os.path.normpath(fname2))
                    self._include_list.pop()
                    # restore information about current file
                    self._current_file = absolute_file_path
                    continue

                # trim out comments
                line = line.split("#")[0].strip()
                if not line:
                    continue

                match_object = _re_macro.match(line)
                if match_object and isinstance(self._command_parser, CfgCommandParser):
                    macro = CfgFileMacro()
                    macro.name = match_object.group(1).strip()
                    macro.value = match_object.group(2).strip()
                    macro.file_name = file_path
                    macro.file_line = line_num
                    self._process_macro(macro)
                else:
                    try:
                        self._parse_line(line, file_path, line_num)
                    except Exception as e:
                        logger.critical("%s::%i: %s", file_path, line_num, e, extra={"source": file_path})
                        raise e
        self._current_file = None

    @classmethod
    def _consume_parameter_ipg_debug(cls, _: MacroResource, atom: AtomicResource, param: re.Match) -> bool:
        """Adds information from the atomic resource into the block control register model.

        Args:
            _: Macro resource (unused)
            atom: Atomic resource to process
            param: Regular expression match object containing parameter information

        Returns:
            True if parameter was successfully consumed
        """
        bctrl_id = param.group(1)
        regn = (int(param.group(3)) - 1) if param.group(3) else 0
        offset = int(param.group(5)[2:], 16) if param.group(5) else int(param.group(6))
        bctrl = ChipModelProvider.get_model().get_bctrl(bctrl_id)
        if bctrl is None:
            raise CfgToolException(f"There is no block control {bctrl_id}")
        bctrl.add_register_ipg_debug(atom.get_name(), regn, offset)
        return True

    @classmethod
    def _consume_parameter_mdac_dfm_tx(cls, macro: MacroResource, _: AtomicResource, param: re.Match) -> bool:
        """Adds the DFMT information into the macro resource.

        Args:
            macro: Macro resource to add DFMT information to
            _: Atomic resource (unused)
            param: Regular expression match object containing DFMT parameter

        Returns:
            True if parameter was successfully consumed
        """
        dfmt = param.group(1)
        macro.add_parameter(dfmt)
        return True

    def _consume_parameters(self, macro: MacroResource, atom: AtomicResource, atoms: List[str]) -> None:
        """For given atomic resource, consume parameters. E.g. CPU_M33P will consume BCTRL_A_IPG_DEBUG model info.

        Args:
            macro: Macro resource to add parameters to
            atom: Atomic resource to process parameters for
            atoms: List of atom strings to consume parameters from
        """
        parsers: Any = None
        consume = []

        if isinstance(atom, ApiResource) and atom.is_cpu():
            parsers = {_re_bctrl_a_ipg_debug: self._consume_parameter_ipg_debug}
        elif isinstance(atom, MdacResource):
            parsers = {_re_mdac_dfmt_x: self._consume_parameter_mdac_dfm_tx}

        if parsers:
            for parser in parsers:
                for atom_string in atoms:
                    match_object = parser.match(atom_string)
                    if match_object and parsers[parser](macro, atom, match_object):
                        consume.append(atom_string)
        for atom_string in consume:
            atoms.remove(atom_string)

    def parse_device(self, root_directory: str, device_name: str) -> None:
        """Parses the device file.

        Args:
            root_directory: Root directory containing device files
            device_name: Name of the device to parse
        """
        self.parse_file(os.path.join(root_directory, "devices", device_name, "configtool", "device.cfg"))

    @classmethod
    def add_static_resources(cls) -> None:
        """Adds static resources into the resource database."""
        sys = ApiResource({"name": "SYS", "type": "API", "cat": "SYS", "api": "SYS"})
        ResourceDatabaseProvider.get_database().add_automatic_resource(sys)
        fusa = ApiResource({"name": "FUSA", "type": "API", "cat": "FUSA", "api": "FUSA"})
        ResourceDatabaseProvider.get_database().add_automatic_resource(fusa)

    def get_include_list(self) -> List[str]:
        """Returns include list."""
        return self._include_list
