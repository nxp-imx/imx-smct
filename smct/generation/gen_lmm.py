#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause

"""Module for generating file config_lmm.h"""

from typing import Any, Dict, List

from smct.configuration.confdata import ConfigurationData
from smct.generation.generator import GeneratorBase, GenHeading, GenMacroList, GenMacroValue, GenStructInit, GenStructInitInline
from smct.owners.owner_lm import LM, MSEL, StartStop


def _group_start_stops(conf: ConfigurationData, start_stops_input: List[StartStop], starts: bool) -> Dict[int, List[StartStop]]:
    """Groups all starts/stops from given list by LM ID, order of defined startstops, and then msel index.

    Args:
        conf: Configuration data object.
        start_stops_input: List of start/stop objects to group.
        starts: Boolean indicating if these are starts (True) or stops (False).

    Returns:
        Dictionary mapping LM ID to list of grouped StartStop objects.
    """
    result: Dict[int, List[StartStop]] = {}
    for start_stop in start_stops_input:
        lm_id = conf.get_lm_id(start_stop.get_msel().get_lm())
        if lm_id not in result:
            result[lm_id] = []
        result[lm_id].append(start_stop)

    for lm in result:
        result[lm] = sorted(result[lm], key=lambda ss: (ss.get_msel().get_all_start_stops(starts).index(ss), ss.get_msel().get_msel()))
    return result


def _get_lm_start_stop_index(ss_all: Dict[int, List[StartStop]], lm_index: int) -> int:
    """Returns first index of start/stop for given LM.

    Args:
        ss_all: Dictionary mapping LM ID to list of StartStop objects.
        lm_index: Index of the logical machine.

    Returns:
        First index of start/stop for the given LM.
    """
    counter = 0
    for i in range(0, lm_index):
        if i in ss_all:
            counter += len(ss_all[i])
    return counter


def _print_msel(struct: GenStructInit, msel: MSEL) -> None:
    """Adds MSEL into the struct init.

    Args:
        struct: Structure initialization generator object.
        msel: MSEL object to add to the struct.
    """
    boot = msel.get_boot()
    if boot is not None:
        struct[f"boot[{msel.get_msel()}]"] = boot
    skip = msel.get_skip()
    if skip is not None:
        struct[f"bootSkip[{msel.get_msel()}]"] = skip


class GeneratorLMM(GeneratorBase):
    """Generator of config_lmm.h"""

    def _get_generator_info(self) -> Dict[str, Any]:
        return {"name": "LMM", "incl": ["config_user.h"]}

    def _get_doxygen_file_name(self) -> str:
        return ""

    def _get_doxygen_brief_lines(self) -> List[str]:
        return ["", "", " Header file containing configuration info for the logical machine manager."]

    def _print_lm(self, lm: LM) -> None:
        """Generates the logical machine configuration defines.

        Args:
            lm: Logical machine object to generate configuration for.
        """
        conf = self._get_configuration()

        lm_inst = conf.get_lm_id(lm)
        starts = lm.get_all_start_stops(True)
        stops = lm.get_all_start_stops(False)

        self.print_generator(GenHeading(f"LM{lm_inst} Config ({lm.get_name()})"))

        struct_generator = GenStructInit(f"SM_LM{lm_inst}_CONFIG", f"Config for LM{lm_inst} ({lm.get_name()})")
        struct_generator["name"] = f'"{lm.get_name()}"'
        struct_generator["rpcType"] = lm.get_rpc_define()
        if lm.get_rpc() != "none":
            struct_generator["rpcInst"] = conf.get_lm_rpc_inst(lm)
        msels = lm.get_msels()
        if len(msels) > 0:
            _print_msel(struct_generator, msels[0])
        rtime = lm.get_rtime()
        if rtime is not None:
            struct_generator["rtime"] = f"{rtime}U"
        safe = lm.get_safe()
        if safe != "nseenv":
            struct_generator["safeType"] = lm.get_safe_define()
        group = lm.get_group()
        if group is not None:
            struct_generator["group"] = f"{group}U"
        if lm.get_auto() is not None:
            struct_generator["autoBoot"] = lm.get_auto_define()
        if starts:
            ss_all = _group_start_stops(conf, conf.get_all_lm_start_stops(True), True)
            struct_generator["start"] = _get_lm_start_stop_index(ss_all, lm_inst) + 1
        if stops:
            ss_all = _group_start_stops(conf, conf.get_all_lm_start_stops(False), False)
            struct_generator["stop"] = _get_lm_start_stop_index(ss_all, lm_inst) + 1
        for m in msels[1:]:
            _print_msel(struct_generator, m)
        self.print_generator(struct_generator)

    def _print_lms_summary(self) -> None:
        """Generates defines with summary of logical machines."""
        conf = self._get_configuration()
        lm_all = conf.get_all_lms()
        lm_len = len(lm_all)
        msel_num = conf.get_max_msel_num() + 1
        seenv_len = len(conf.get_all_seenv_agents())
        lm_default = conf.get_default_lm()
        lm_default_id = conf.get_lm_id(lm_default) if lm_default else 0

        self.print_generator(GenHeading("LM Config"))
        self.print_generator(GenMacroValue("SM_NUM_LM", lm_len, "Config for number of LM"))

        if lm_len:
            lm_data_list_define = GenMacroList("SM_LM_CONFIG_DATA", "Config data array for LM")
            for i in range(0, lm_len):
                lm_data_list_define.add_value(f"SM_LM{i}_CONFIG")
            self.print_generator(lm_data_list_define)

        self.print_generator(GenMacroValue("SM_LM_NUM_MSEL", msel_num, "Number of  mSel"))
        self.print_generator(GenMacroValue("SM_LM_NUM_SEENV", seenv_len, "Number of  S-EENV"))
        self.print_generator(GenMacroValue("SM_LM_CFG_NAME", f'"{conf.get_config_name()}"', "Config name"))
        self.print_generator(GenMacroValue("SM_LM_DEFAULT", lm_default_id, "Default LM for monitor"))

    def _print_start_stop(self, start: bool) -> None:
        """Generates start and stop defines.

        Args:
            start: Boolean indicating if generating starts (True) or stops (False).
        """
        conf = self._get_configuration()
        start_stop_type = "start" if start else "stop"
        start_stops_list = conf.get_all_lm_start_stops(start)

        if start:
            self.print_generator(GenHeading("LM Start/Stop Lists"))

        self.print_generator(GenMacroValue(f"SM_LM_NUM_{start_stop_type.upper()}", len(start_stops_list), f"Config for number of {start_stop_type}"))
        start_stop_list_define = GenMacroList(f"SM_LM_{start_stop_type.upper()}_DATA", f"LM {start_stop_type} list", suffix=",")

        start_stops_grouped = _group_start_stops(conf, start_stops_list, start)
        for lm_start_stops in start_stops_grouped.values():
            for start_stop in lm_start_stops:
                struct_generator = GenStructInitInline(None)
                struct_generator.add_entry("lmId", conf.get_lm_id(start_stop.get_msel().get_lm()))
                struct_generator.add_entry("mSel", start_stop.get_msel().get_msel())
                struct_generator.add_entry("ss", start_stop.get_resources().get_start_stop_type())
                struct_generator.add_entry("rsrc", start_stop.get_resources().get_api_id())
                suffix = ""
                if start_stop.get_args():
                    struct_generator.add_break_line()
                    struct_generator.add_entry("numArg", str(len(start_stop.get_args())))
                    for argument_index in range(0, len(start_stop.get_args())):
                        struct_generator.add_entry(f"arg[{argument_index}]", start_stop.get_args()[argument_index])
                        suffix = ", "
                struct_generator.print_members()
                start_stop_list_define.add_value(f"{{{struct_generator.get_members_string()}{suffix}}}")
        self.print_generator(start_stop_list_define)

    def _print_faults(self) -> None:
        """Generates fault configuration defines."""
        self.print_generator(GenHeading("LM Fault Lists"))
        start_stop_list_define = GenMacroList("SM_LM_FAULT_DATA", "LM fault reactions", suffix=",")

        for lm in self._get_configuration().get_all_lms():
            lm_id = self._get_configuration().get_lm_id(lm)
            for assigned_resource in lm.get_all_faults():
                for fault_resource in assigned_resource.get_fault_resources():
                    struct_generator = GenStructInitInline(None)
                    reaction = assigned_resource.get_react_type()
                    if reaction is not None:
                        struct_generator.add_entry("reaction", reaction)
                        struct_generator.add_entry("lm", lm_id)
                        struct_generator.print_members()
                        start_stop_list_define.add_value(f"[{fault_resource.get_api_id()}] = {{{struct_generator.get_members_string()}}}")
        self.print_generator(start_stop_list_define)

    def print_content(self) -> None:
        """Generates logical machine configuration defines."""
        for lm in self._get_configuration().get_all_lms():
            self._print_lm(lm)

        self._print_lms_summary()
        self._print_start_stop(True)
        self._print_start_stop(False)
        self._print_faults()

    def __str__(self) -> str:
        """Returns string representation of the generator.

        Returns:
            String representation of the LMM generator.
        """
        return "LMM generator"
