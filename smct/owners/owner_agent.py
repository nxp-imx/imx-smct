#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Module related to SCMI agents"""
import logging
from typing import Any, Dict, List

from smct import utils
from smct.expcetions.cfg_tool_exception import CfgToolException

from ..utils import FormatedInt
from .owner_base import ResourceOwner

logger = logging.getLogger()


class Mailbox:
    """Abstract mailbox with doorbells mapped to abstract upstream channels"""

    mailbox_types: Dict[str, str]
    mailbox_priority_types: Dict[str, str]

    def __init__(self, mailbox_type: str, test: int | None, priority: str | None) -> None:
        # our owner, this is typically SCMI_AGENT, but it may change in future (e.g. LM can own it)
        self._owner: Any = None
        if mailbox_type in self.mailbox_types:
            self._type: str = mailbox_type  # mailbox type
        else:
            source = "/".join(["user_config", "MAILBOX_" + mailbox_type])
            logger.error("Invalid MB type '%s'", mailbox_type, extra={"source": source})
            self._type = "none"
        self._doorbell_channel: List["Channel"] = []  # upstream channels for each doorbell
        self._test: int | None = test
        self._priority: str | None = None

        if priority is not None:
            if priority not in self.mailbox_priority_types:
                source = "/".join(["user_config", "MAILBOX_" + mailbox_type])
                logger.error("Unknown MAILBOX_MU priority type '%s'", priority, extra={"source": source})
            self._priority = priority

    def set_doorbell_channel(self, doorbell: int, channel: "Channel") -> None:
        """Sets doorbell channel.

        Args:
            doorbell: The doorbell index to set
            channel: The channel to associate with the doorbell
        """
        if doorbell < 0:
            source = "/".join(["user_config", "MAILBOX_" + self._type, channel.get_type() + "_channel"])
            extra = {"source": source}
            if self._owner is not None:
                validation_id = ".".join([self._owner.get_id(), "MAILBOX", "DB"])
                extra["validation_id"] = validation_id
            logger.error("Parameter 'db' cannot be negative", extra=extra)
            return
        utils.set_at_index(self._doorbell_channel, doorbell, channel)

    def get_owner(self) -> Any:
        """Returns owner of the mailbox.

        Returns:
            The owner object of the mailbox
        """
        return self._owner

    def get_type(self) -> str:
        """Returns type of the mailbox.

        Returns:
            The mailbox type as a string
        """
        return self._type

    def get_type_define(self) -> str:
        """Returns mailbox type define value.

        Returns:
            The define value for the mailbox type
        """
        if self._type in self.mailbox_types:
            return self.mailbox_types[self._type]
        return self.mailbox_types["none"]

    def get_doorbell_channels(self) -> List["Channel"]:
        """Returns list of doorbell channels.

        Returns:
            List of channels associated with doorbells
        """
        return self._doorbell_channel

    def get_test(self) -> int | None:
        """Returns test mailbox or None if none is specified.

        Returns:
            Test mailbox value or None
        """
        return self._test

    def get_priority(self) -> str | None:
        """Returns priority of this agent.

        Returns:
            Priority string or None if not set
        """
        return self._priority

    def get_priority_define(self) -> str:
        """Returns priority type define value.

        Returns:
            The define value for the priority type
        """
        if self._priority in self.mailbox_priority_types:
            return self.mailbox_priority_types[self._priority]
        return self.mailbox_priority_types["very_low"]

    def set_owner(self, owner: Any) -> None:
        """Sets owner of the mailbox.

        Args:
            owner: The owner object to assign to the mailbox
        """
        self._owner = owner

    def get_assignment_json(self) -> Dict[str, Any]:
        """Returns JSON object with raw data.

        Returns:
            Dictionary containing the mailbox assignment data
        """
        return {"type": self._type, "test": self._test, "priority": self._priority}


class MailboxMu(Mailbox):
    """MU mailbox of an SCMI_AGENT"""

    def __init__(self, mu: int, test: int | None, sma: FormatedInt | None, priority: str | None) -> None:
        super().__init__("mu", test, priority)
        self._mu: int = mu
        self._sma: FormatedInt | None = sma

    def get_sma(self) -> FormatedInt | None:
        """Returns shared memory address of MU.

        Returns:
            The shared memory address or None if not set
        """
        return self._sma

    def get_mu(self) -> int:
        """Returns number of MU.

        Returns:
            The message unit number
        """
        return self._mu

    def get_assignment_json(self) -> Dict[str, Any]:
        """Returns JSON object with raw data.

        Returns:
            Dictionary containing the MU mailbox assignment data
        """
        ret = super().get_assignment_json()
        ret |= {
            "mu": self._mu,
            "sma": self._sma,
        }
        return ret


class MailboxLoopback(Mailbox):
    """Loopback mailbox of an SCMI_AGENT"""

    def __init__(self, test: int | None, priority: str | None) -> None:
        super().__init__("loopback", test, priority)


##########################################################################
# Channel is fully abstracted, used for both RPC and XPORT channels


class Channel:
    """Generic CHANNEL"""

    # dict of allowed rpc types assignment
    rpc_types: Dict[str, str]
    # dict of allowed rpc types assignment
    xport_types: Dict[str, str]

    def __init__(self) -> None:
        super().__init__()
        self._type: str = "none"  # channel type for filtering ("smt", "scmi", ...)

    def get_assignment_json(self) -> Dict[str, Any]:
        """Returns JSON object with raw data.

        Returns:
            Dictionary containing the channel assignment data
        """
        ret = {
            "type": self._type,
        }
        return ret

    def get_type(self) -> str:
        """Returns type of the channel.

        Returns:
            The channel type as a string
        """
        return self._type

    def get_xport_type(self) -> str:
        """Returns xport type of the channel.

        Returns:
            The transport type define value for the channel
        """
        if self._type in self.xport_types:
            return self.xport_types[self._type]
        source = "/".join(["user_config", self._type + "_channel"])
        logger.error("Invalid Channel xport type '%s'", self._type, extra={"source": source})
        return self.xport_types["none"]

    def get_rpc_type(self) -> str:
        """Returns rpc type of the channel.

        Returns:
            The RPC type define value for the channel
        """
        if self._type in self.rpc_types:
            return self.rpc_types[self._type]
        source = "/".join(["user_config", self._type + "_channel"])
        logger.error("Invalid Channel rpc type '%s'", self._type, extra={"source": source})
        return self.rpc_types["none"]


class SmtChannel(Channel):
    """SMT channel"""

    smt_crc_types: Dict[str, str]

    def __init__(self, db: int, check: str | None) -> None:
        super().__init__()
        self._type: str = "smt"
        self._mailbox: Mailbox | None = None  # our downstream mailbox
        self._rpc_channel: Channel | None = None  # our upstream RPC channel

        self._doorbell: int = db  # doorbell id for the mailbox
        if check is not None and check not in self.smt_crc_types:
            source = "/".join(["user_config", "smt_channel"])
            logger.error("Unknown SMT_CHANNEL check type '%s'", check, extra={"source": source})
        self._check: str | None = check  # CRC or other check type

    def get_mailbox(self) -> Mailbox | None:
        """Returns downstream mailbox.

        Returns:
            The associated mailbox or None if not set
        """
        return self._mailbox

    def get_rpc_channel(self) -> Channel | None:
        """Returns upstream RPC channel.

        Returns:
            The upstream RPC channel or None if not set
        """
        return self._rpc_channel

    def get_doorbell(self) -> int:
        """Returns doorbell ID for the mailbox.

        Returns:
            The doorbell ID
        """
        return self._doorbell

    def get_check(self) -> str | None:
        """Returns check type.

        Returns:
            The check type string or None if not set
        """
        return self._check

    def get_check_define(self) -> str:
        """Returns CRC type define value.

        Returns:
            The define value for the CRC type
        """
        if self._check in self.smt_crc_types:
            return self.smt_crc_types[self._check]
        return self.smt_crc_types["none"]

    def set_mailbox(self, mb: Mailbox) -> None:
        """Sets mailbox for this SMT channel.

        Args:
            mb: The mailbox to associate with this channel
        """
        self._mailbox = mb
        mb.set_doorbell_channel(self._doorbell, self)

    def set_rpc_channel(self, ch: Channel) -> None:
        """Sets RPC channel of this SMT channel.

        Args:
            ch: The RPC channel to set
        """
        self._rpc_channel = ch

    def get_assignment_json(self) -> Dict[str, Any]:
        """Returns JSON object with raw data.

        Returns:
            Dictionary containing the SMT channel assignment data
        """
        ret = super().get_assignment_json()
        ret |= {
            "doorbell": self._doorbell,
            "check": self._check,
        }
        return ret


class ScmiChannel(Channel):
    """SCMI channel object"""

    # dict of allowed SCMI channel types
    channel_types: Dict[str, str]
    # dict of allowed SCMI sequence types
    sequence_types: Dict[str, str]

    def __init__(self, agent: "ScmiAgent", channel_type: str, sequence: str | None, test: str | None, notify: str | None) -> None:
        super().__init__()
        self._type = "scmi"
        self._agent: "ScmiAgent" = agent
        self._xport_channel: Channel | None = None
        if channel_type not in self.channel_types:
            raise CfgToolException(f"Unknown SCMI CHANNEL type '{type}'")
        self._sequence: str | None = sequence
        if sequence is not None and sequence not in self.sequence_types:
            source = "/".join(["user_config", agent.get_id(), "scmi_channel"])
            logger.error("Unknown CHANNEL SEQUENCE type %s", sequence, extra={"source": source})
        self._channel_type: str = channel_type
        self._test: str | None = test
        self._notify: int = 0
        if notify is not None:
            self._notify = utils.parse_int_or_default(notify, 0)

    def set_xport_channel(self, xport_channel: Channel) -> None:
        """Sets XPORT channel.

        Args:
            xport_channel: The transport channel to set
        """
        self._xport_channel = xport_channel

    def get_assignment_json(self) -> Dict[str, Any]:
        """Returns JSON object with raw data.

        Returns:
            Dictionary containing the SCMI channel assignment data
        """
        ret = super().get_assignment_json()
        ret |= {
            "chtype": self._channel_type,
            "sequence": self._sequence,
            "test": self._test,
            "notify": self._notify,
        }
        if self._xport_channel is not None:
            ret |= {
                "xport": self._xport_channel.get_assignment_json(),
            }
        return ret

    def get_channel_type(self) -> str:
        """Returns type of the channel.

        Returns:
            The channel type string
        """
        return self._channel_type

    def get_channel_type_define(self) -> str | None:
        """Returns channel type define value.

        Returns:
            The define value for the channel type or None if not found
        """
        if self._channel_type in self.channel_types:
            return self.channel_types[self._channel_type]
        return None

    def get_sequence(self) -> str | None:
        """Returns scmi channel sequence.

        Returns:
            The sequence string or None if not set
        """
        return self._sequence

    def get_channel_sequence_define(self) -> str:
        """Returns channel sequence define value.

        Returns:
            The define value for the channel sequence
        """
        if self._sequence in self.sequence_types:
            return self.sequence_types[self._sequence]
        return self.sequence_types["none"]

    def get_xport_channel(self) -> Channel | None:
        """Returns transport channel.

        Returns:
            The transport channel or None if not set
        """
        return self._xport_channel

    def get_notify(self) -> int:
        """Returns notify channel.

        Returns:
            The notify value
        """
        return self._notify

    def get_test(self) -> str | None:
        """Returns test property.

        Returns:
            The test property string or None if not set
        """
        return self._test

    def get_agent(self) -> "ScmiAgent":
        """Returns agent of this channel.

        Returns:
            The SCMI agent that owns this channel
        """
        return self._agent

    def set_agent(self, agent: "ScmiAgent") -> None:
        """Sets agent for this channel.

        Args:
            agent: The SCMI agent to assign to this channel
        """
        self._agent = agent


##########################################################################
# SCMI_AGENT


class ScmiAgent(ResourceOwner):
    """SCMI agent object representation"""

    def __init__(self, agent_id: str, owner: Any, name: str, secure: bool, safe: str = "nseenv", did: int = -1) -> None:
        super().__init__(agent_id)
        self.set_name(name)
        self._owner: Any = owner
        self._secure: bool = secure
        self._channels: List[ScmiChannel] = []
        self._mailbox: Mailbox | None = None
        self._safe: str = safe
        self._did: int = did

    def get_did(self) -> int:
        """Returns domain ID of the agent's owner.

        Returns:
            The domain ID
        """
        return self._did

    def get_secure(self) -> int:
        """Returns 1 if the agent is secure, 0 otherwise.

        Returns:
            1 if secure, 0 otherwise
        """
        return 1 if self._secure else 0

    def get_owner(self) -> Any:
        """Returns assigned owner.

        Returns:
            The owner object
        """
        return self._owner

    def get_all_scmi_channels(self) -> List[ScmiChannel]:
        """Returns all SCMI channels in this agent.

        Returns:
            List of all SCMI channels
        """
        return self._channels

    def get_all_xport_channels(self) -> List[Channel]:
        """Returns all XPORT channels in this agent.

        Returns:
            List of all transport channels
        """
        result = []
        for ch in self._channels:
            xport = ch.get_xport_channel()
            if xport is not None:
                result.append(xport)
        return result

    def get_all_channels(self) -> List[Channel]:
        """Return all used CHANNELS, both SCMI and their used transport ones such as all SMT ones.

        Returns:
            List of all channels (SCMI and transport)
        """
        return self.get_all_scmi_channels() + self.get_all_xport_channels()

    def get_mailbox(self) -> Mailbox | None:
        """Returns mailbox of the SCMI agent.

        Returns:
            The mailbox or None if not set
        """
        return self._mailbox

    def get_safe_type(self) -> str:
        """Returns safety type of the agent's owner.

        Returns:
            The safety type string
        """
        return self._safe

    def add_mailbox(self, mb: Mailbox) -> None:
        """Sets mailbox to this agent.

        Args:
            mb: The mailbox to add to this agent

        Raises:
            CfgToolException: If mailbox is already assigned to another agent or if agent already has a different mailbox
        """
        if mb.get_owner() and mb.get_owner() != self:
            raise CfgToolException("Cannot re-assign already used MAILBOX to SCMI_AGENT")
        if self._mailbox and self._mailbox != mb:
            raise CfgToolException("SCMI_AGENT can only handle one MAILBOX in current version")
        self._mailbox = mb
        mb.set_owner(self)

    def add_channel(self, ch: ScmiChannel) -> None:
        """Adds channel to this agent.

        Args:
            ch: The SCMI channel to add

        Raises:
            CfgToolException: If channel is already assigned to a different agent
        """
        if ch.get_agent() and ch.get_agent() != self:
            raise CfgToolException("Cannot re-assign CHANNEL to a different agent")
        self._channels.append(ch)
        ch.set_agent(self)

    def set_owner(self, owner: Any) -> None:
        """Sets LM for this agent.

        Args:
            owner: The owner object to assign
        """
        self._owner = owner

    def get_assignment_json(self) -> Dict[str, Any]:
        """Returns JSON object with raw data.

        Returns:
            Dictionary containing the agent assignment data
        """
        ret = super().get_assignment_json()
        mailbox = self._mailbox
        ret |= {
            "type": "SCMI_AGENT",
            "secure": self._secure,
            "channels": [c.get_assignment_json() for c in self._channels],
        }

        if mailbox is not None:
            ret["mailbox"] = mailbox.get_assignment_json()
        return ret

    def __str__(self) -> str:
        """Returns string representation.

        Returns:
            String representation of the agent
        """
        return self.get_id()

    def __repr__(self) -> str:
        """Returns representation of this object.

        Returns:
            Detailed string representation of the agent
        """
        return f"{self.__class__.__name__}" f"('{self._id}', {self._did}, '{self._name}', {self._secure}, '{self._safe}', {self._did})"
