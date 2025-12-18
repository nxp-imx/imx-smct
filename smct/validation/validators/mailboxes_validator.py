#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Module related to validation of mailboxes"""
import logging
import typing
from typing import Dict, List

from smct.configuration.confdata import ConfigurationData
from smct.expcetions.cfg_tool_exception import CfgToolException
from smct.owners.owner_agent import MailboxMu, ScmiAgent
from smct.validation.validation_entry import ValidationEntry
from smct.validation.validator_base import ValidatorBase


class MailboxesValidator(ValidatorBase):
    """Validator of mailboxes"""

    @classmethod
    def check_mu_mailboxes(cls, configuration: ConfigurationData, result: List[ValidationEntry]) -> None:
        """Checks all MU mailboxes for problems.

        Args:
            configuration: The configuration data to validate.
            result: List to append validation entries to.
        """
        used_mus: Dict[int, List[ScmiAgent]] = {}
        for lm in configuration.get_all_lms():
            for agent in lm.get_all_agents():
                mailbox = agent.get_mailbox()
                if isinstance(mailbox, MailboxMu):
                    mailbox_mu = typing.cast(MailboxMu, mailbox)
                    mu = mailbox_mu.get_mu()
                    if mu not in used_mus:
                        used_mus[mu] = []
                        if mu > lm.mu_max_count:
                            raise CfgToolException(f"MU{mu} index is out of expected range 0 - {lm.mu_max_count}")
                    used_mus[mu].append(agent)

        for mu, agents in used_mus.items():
            if len(agents) > 1:
                for agent in agents:
                    source = "/".join(["user_config", agent.get_owner().get_name(), agent.get_name(), "MU" + str(mu)])
                    validation_id = ".".join([agent.get_id(), "MAILBOX", "MU"])
                    result.append(ValidationEntry(logging.ERROR, source, f"Duplicate MU {mu} used in agent {agent.get_name()}", validation_id))

    def validate(self, configuration: ConfigurationData) -> List[ValidationEntry]:
        """Validates mailboxes.

        Args:
            configuration: The configuration data to validate.

        Returns:
            List of validation entries containing any issues found.
        """
        result: List[ValidationEntry] = []
        self.check_mu_mailboxes(configuration, result)
        return result
