#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Module for generating file config_test.h."""

import logging
from typing import Any, Dict, List

from smct.generation.generator import GeneratorBase, GenHeading, GenMacroList, GenMacroValue, GenStructInit, GenStructInitInline
from smct.owners.owner_agent import MailboxMu, SmtChannel
from smct.resources.res_api import ApiResource

logger = logging.getLogger()


class GeneratorTest(GeneratorBase):
    """Generator for config_test.h file."""

    def _get_generator_info(self) -> Dict[str, Any]:
        """Gets generator information.

        Returns:
            Dict[str, Any]: Dictionary containing generator name and includes.
        """
        # This must be overridden to avoid exception
        return {"name": "test", "incl": ["config_user.h"]}

    def _get_doxygen_file_name(self) -> str:
        """Gets the doxygen file name.

        Returns:
            str: Empty string for doxygen file name.
        """
        return ""

    def _get_doxygen_brief_lines(self) -> List[str]:
        """Gets the doxygen brief description lines.

        Returns:
            List[str]: List of brief description lines for doxygen.
        """
        return ["", "", " Header file containing configuration info for the unit tests."]

    def _get_all_tests(self) -> List[str]:
        """Returns all SCMI channel tests in order of occurrence.

        Returns:
            List[str]: List of all SCMI channel test structures.
        """
        result = []

        channel_counter = 0
        default_a2p_value = -1
        a2p = default_a2p_value
        rsrc_overwrite = {"TEST_SYS", "TEST_FUSA", "TEST_LMM"}

        for lm in self._get_configuration().get_all_scmi_lms():
            for msel in lm.get_all_msels():
                starts_stops = msel.get_all_test_start_stops()
                for has_test, rsrc in starts_stops:
                    for protocol, test in lm.protocols:
                        rsrc_name = rsrc.get_name().upper()
                        if rsrc_name.startswith((protocol, "BRD_SM_" + protocol)) and has_test:
                            if a2p == default_a2p_value:
                                source = "/".join(["user_config", lm.get_id(), "MSEL" + str(msel.get_msel()), rsrc.get_name().upper()])
                                validation_id = ".".join([lm.get_id(), "SS_RESOURCES", rsrc.get_name().upper(), "TEST"])
                                logger.error(
                                    "Test resource '%s' of %s is ignored. LM is not set to default debugging monitor.",
                                    rsrc.get_name().upper(),
                                    lm.get_id(),
                                    extra={"source": source, "validation_id": validation_id},
                                )
                            else:
                                struct = GenStructInitInline("")
                                struct.add_entry("testId", test)
                                struct.add_entry("channel", f"{a2p}U")
                                if test in rsrc_overwrite:
                                    struct.add_entry("rsrc", f"{rsrc_name[4:]}U" if test == "TEST_LMM" else "0U")
                                else:
                                    struct.add_entry("rsrc", rsrc_name if rsrc_name.startswith("BRD_SM_") else f"DEV_SM_{rsrc_name}")
                                struct.print_members()
                                entry = "{" + struct.get_members_string() + "}"
                                result.append(entry)
            for scmi_agent in lm.get_all_agents():
                for scmi_channel in scmi_agent.get_all_scmi_channels():
                    if scmi_channel.get_channel_type() == "a2p":
                        a2p = channel_counter
                    channel_counter += 1
                if scmi_agent.get_dup() is not None:
                    continue
                for protocol, test in lm.protocols:
                    for assignment in scmi_agent.get_assigned_resources():
                        atomic_resources = assignment.get_atomic_resources()
                        for atomic in atomic_resources:
                            if (
                                atomic.get_name().upper().startswith((protocol, "BRD_SM_" + protocol))
                                and assignment.should_generate_test()
                                and (isinstance(atomic, ApiResource) and not atomic.is_auto())
                            ):
                                if a2p == default_a2p_value:
                                    source = "/".join(["user_config", lm.get_name(), scmi_agent.get_name()])
                                    validation_id = ".".join([scmi_agent.get_id(), "RPC_CHANNELS"])
                                    logger.error("There is no SCMI A2P protocol channel", extra={"source": source, "validation_id": validation_id})
                                    return []
                                name = atomic.get_name().upper()
                                struct = GenStructInitInline("")
                                struct.add_entry("testId", test)
                                struct.add_entry("channel", f"{a2p}U")
                                if test in rsrc_overwrite:
                                    struct.add_entry("rsrc", f"{name[4:]}U" if test == "TEST_LMM" else "0U")
                                else:
                                    struct.add_entry("rsrc", name if name.startswith("BRD_SM_") else f"DEV_SM_{name}")
                                struct.print_members()
                                entry = "{" + struct.get_members_string() + "}"
                                result.append(entry)
        return result

    def _generate_test_configs(self, test_structures_macro: GenMacroList) -> None:
        """Generates the test configuration structures and fills the test configs list macro.

        Args:
            test_structures_macro (GenMacroList): Macro list to populate with test structure names.
        """
        agent_counter = 0
        mailbox_counter = -1
        all_logical_machines = self._get_configuration().get_all_lms()
        for lm in all_logical_machines:
            self.print_generator(GenHeading(f"LM{all_logical_machines.index(lm)} Test Config ({lm.get_name().upper()})"))
            all_agents = lm.get_all_agents()
            for agent in all_agents:
                used_mailboxes = []
                for xport_channel in agent.get_all_xport_channels():
                    test_index = len(test_structures_macro)
                    name = f"SM_TEST_CHN{test_index}_CONFIG"
                    generator = GenStructInit(name, f"Config for test channel {test_index}")
                    if isinstance(xport_channel, SmtChannel):
                        mailbox = xport_channel.get_mailbox()
                        if mailbox is not None:
                            test = mailbox.get_test()
                            if test is not None:
                                mailbox_counter = test
                            else:
                                if mailbox not in used_mailboxes:
                                    # Increase only when new mailbox is used by the channel
                                    mailbox_counter += 1
                                    used_mailboxes.append(mailbox)
                            generator["mbInst"] = f"{mailbox_counter}U"
                        if isinstance(mailbox, MailboxMu):
                            sma = mailbox.get_sma()
                            if sma is not None:
                                generator["sma"] = f"{sma}U"
                        doorbell = xport_channel.get_doorbell()
                        generator["mbDoorbell"] = f"{doorbell}U"
                    generator["agentId"] = f"{agent_counter}U"
                    self.print_generator(generator)
                    test_structures_macro.add_value(name)
                agent_counter += 1

    def _print_test_data(self) -> None:
        """Generates the content of the test file."""
        test_structures_macro = GenMacroList("SM_TEST_CHN_CONFIG_DATA", "Config data array for test channels")
        self._generate_test_configs(test_structures_macro)
        tests = self._get_all_tests()
        tests.sort()

        self.print_generator(GenHeading("Test Channel Config"))
        self.print_generator(GenMacroValue("SM_NUM_TEST_CHN", f"{len(test_structures_macro)}U", "Config for number of test channels"))
        self.print_generator(test_structures_macro)

        self.print_generator(GenHeading("Test Config"))

        scmi_test_structures_macro = GenMacroList("SM_SCMI_TEST_CONFIG_DATA", "Config data array for tests")
        scmi_test_structures_macro.set_values(tests)
        self.print_generator(GenMacroValue("SM_SCMI_NUM_TEST", f"{len(scmi_test_structures_macro)}U", "Config for number of tests"))
        self.print_generator(scmi_test_structures_macro)
        default_channel = self._get_configuration().get_default_test_channel()
        if default_channel >= 0:
            self.print_generator(GenMacroValue("SM_TEST_DEFAULT_CHN", f"{default_channel}U", "Default channel for non-agent specific tests"))

    def print_content(self) -> None:
        """Prints content of this file."""
        self._print_test_data()

    def __str__(self) -> str:
        """Returns string representation of the generator.

        Returns:
            str: String representation of the TEST generator.
        """
        return "TEST generator"
