#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Module related to logical machines"""
import logging
from typing import Any, Dict, List, Tuple

from smct import utils
from smct.expcetions.cfg_tool_exception import CfgToolException
from smct.resources.res_api import ApiResource
from smct.resources.resource_base import AtomicResource, MacroResource

from .owner_agent import Channel, ScmiAgent
from .owner_base import AssignedResource
from .owner_dom import DOM

logger = logging.getLogger()


class StartStop:
    """One start or stop operation within mSel"""

    def __init__(self, msel: "MSEL", res: AtomicResource, test: bool, args: List[int]):
        self._msel: "MSEL" = msel  # our parent MSEL
        self._rsrc: AtomicResource = res  # atomic resource affected
        self._args: List[int] = args.copy()  # operation arguments
        self._test: bool = test

    def get_assignment_json(self) -> Dict[str, Any]:
        """Returns JSON object with raw data.

        Returns:
            JSON object containing resource name, arguments, and test flag.
        """
        ret: Dict[str, Any] = {
            "rsrc": self._rsrc.get_name(),
        }
        if self._args:
            ret |= {"args": self._args}
        if self._test:
            ret |= {"test": self._test}
        return ret

    def get_resources(self) -> "AtomicResource":
        """Returns affected atomic resources.

        Returns:
            AtomicResource: The atomic resource affected by this start/stop operation.
        """
        return self._rsrc

    def get_msel(self) -> "MSEL":
        """Returns parent MSEL.

        Returns:
            MSEL: The parent MSEL object.
        """
        return self._msel

    def get_args(self) -> List[int]:
        """Returns list of operation arguments.

        Returns:
            List[int]: List of operation arguments.
        """
        return self._args

    def get_test(self) -> bool:
        """Returns test.

        Returns:
            bool: The test flag value.
        """
        return self._test

    def __eq__(self, __value: Any) -> bool:
        """Equals for class StartStop.

        Args:
            __value (Any): Object to compare with.

        Returns:
            bool: True if objects are equal, False otherwise.
        """
        if isinstance(__value, self.__class__):
            return self._args == __value._args and self._test == __value._test and self._rsrc.get_name() == __value._rsrc.get_name()
        return False


class StartStopSequence:
    """Sequence of starts/stops in one LM"""

    def __init__(self, ss_index: int, lm_name: str, start_stops: List[StartStop | None]):
        self._ss_index: int = ss_index
        self._ss_name: str = lm_name + " start stop " + str(ss_index)
        self._ss_resources: List[StartStop] = [startstop for startstop in start_stops if startstop is not None]

    def get_assignment_json(self) -> object:
        """Returns JSON object with raw data.

        Returns:
            JSON object containing sequence index, name, and resources.
        """
        ret = {"ss": self._ss_index, "ss_name": self._ss_name, "resources": [start_stop.get_assignment_json() for start_stop in self._ss_resources]}
        return ret


class MSEL:
    """One MSEL mode of logical machine"""

    def __init__(self, lm: "LM", msel: int, boot: int | None, skip: bool | None):
        self._lm: "LM" = lm  # our parent LM
        self._msel: int = msel  # index of operation mode
        self._boot: int | None = boot  # 0=no-boot, >0 means LM boot order number
        self._skip: bool | None = skip  # when True, silently ignore missing code image
        self._start: List[StartStop | None] = []
        self._stop: List[StartStop | None] = []
        self._start_sequence_index: int | None = None
        self._stop_sequence_index: int | None = None

    def set_start_sequence_index(self, index: int) -> None:
        """Sets index for the sequence of starts.

        Args:
            index (int): The index to set for the start sequence.
        """
        self._start_sequence_index = index

    def set_stop_sequence_index(self, index: int) -> None:
        """Sets index for the sequence of stops.

        Args:
            index (int): The index to set for the stop sequence.
        """
        self._stop_sequence_index = index

    def get_all_start_stops(self, start: bool) -> List[StartStop | None]:
        """Returns list of all start or stop information.

        Args:
            start (bool): If True, returns start operations; if False, returns stop operations.

        Returns:
            List[StartStop | None]: List of start or stop operations.
        """
        return self._start if start else self._stop

    def get_all_test_start_stops(self) -> List[Tuple[bool, AtomicResource]]:
        """Returns list of all start or stop information with test argument.

        Returns:
            List[Tuple[bool, AtomicResource]]: List of tuples containing test flag and atomic resource.
        """
        start_stops = [x for x in (self._start + self._stop) if x is not None]
        return list(set(map(lambda start_stop: (start_stop.get_test(), start_stop.get_resources()), start_stops)))

    def add_start_stop(self, is_start: bool, has_test: bool, res: AtomicResource, value: str) -> None:
        """Adds start or stop information.

        Args:
            is_start (bool): True for start operation, False for stop operation.
            has_test (bool): Whether the operation has a test flag.
            res (AtomicResource): The atomic resource to operate on.
            value (str): The operation value string containing order and arguments.
        """
        (order_string, *args_string) = value.split("|")
        order = utils.parse_int(order_string)
        args = [utils.parse_int(x) for x in args_string]

        if order <= 0 or order > 100:
            mode = "Start" if is_start else "Stop"
            raise CfgToolException(f"Invalid {mode} order number({order}) for mSel mode")
        order -= 1  # make order zero-based

        ss = StartStop(self, res, has_test, args)
        dest = self._start if is_start else self._stop
        while len(dest) <= order:
            dest.append(None)
        if not dest[order]:
            dest[order] = ss
        else:
            source = "/".join(["user_config", self._lm.get_id(), "MSEL" + str(self._msel)])
            validation_id = ".".join([self._lm.get_id(), "MSEL" + str(self._msel)])
            logger.error(
                "Resource command '%s' is called multiple times in start/stop sequence of %s in MSEL%s",
                res.get_name(),
                self._lm.get_id(),
                self._msel,
                extra={"source": source, "validation_id": validation_id},
            )

    def get_start_stop_list_json(self, is_start: bool) -> List[object]:
        """Returns JSON list of all start or stop information.

        Args:
            is_start (bool): True for start operations, False for stop operations.

        Returns:
            List[object]: JSON list of start or stop operations.
        """
        src = self._start if is_start else self._stop
        ret: List[Any] = []
        i = 0
        for ss in src:
            if ss:
                ret.append(ss.get_assignment_json())
            else:
                start_stop_str = "Start" if is_start else "Stop"
                source = "/".join(["user_config", self._lm.get_id(), "MSEL" + str(self._msel)])
                validation_id = ".".join([self._lm.get_id(), "MSEL" + str(self._msel)])
                logger.warning(
                    "Unused index %i in %s operation for LM %s, mSel=%s",
                    i,
                    start_stop_str,
                    self._lm.get_id(),
                    self._msel,
                    extra={"source": source, "validation_id": validation_id},
                )
            i += 1
        return ret

    def get_assignment_json(self) -> Dict[str, Any]:
        """Returns JSON object with raw data.

        Returns:
            object: JSON object containing MSEL configuration data.
        """
        ret = {
            "msel": self._msel,
            "boot": self._boot,
            "skip": self._skip,
            "start": self._start_sequence_index,
            "stop": self._stop_sequence_index,
        }
        return ret

    def get_start(self) -> List[StartStop | None]:
        """Returns list of all start information.

        Returns:
            List[StartStop | None]: List of start operations.
        """
        return self._start

    def get_stop(self) -> List[StartStop | None]:
        """Returns list of all stop information.

        Returns:
            List[StartStop | None]: List of stop operations.
        """
        return self._stop

    def get_skip(self) -> bool | None:
        """Returns True for silently ignore missing code image or False otherwise.

        Returns:
            bool | None: Skip flag value.
        """
        return self._skip

    def get_msel(self) -> int:
        """Returns index of operation mode.

        Returns:
            int: The MSEL index.
        """
        return self._msel

    def get_lm(self) -> "LM":
        """Returns parent LM.

        Returns:
            LM: The parent logical machine.
        """
        return self._lm

    def get_boot(self) -> int | None:
        """Returns boot order number (0 for no-boot).

        Returns:
            int | None: Boot order number.
        """
        return self._boot


class LM(DOM):
    """Represents a DOMAIN to which we can assign resources (only TRDC resources)"""

    # dict of allowed safety types assignment
    safety_types: Dict[str, str]
    # dict of allowed autoboot types assignment
    auto_boot_types: Dict[str, str]
    # expected DID of SM
    sm_did: int
    # max MU count
    mu_max_count: int
    # list of tuples containing protocol prefixes and tests
    protocols: list[tuple[str, str]]

    def __init__(
        self, lm_id: str, did: int, name: str, rpc: str | None, rtime: int | None, safe: str | None, group: int | None, auto: str | None, dflt: bool
    ) -> None:
        super().__init__(lm_id, did)
        super().set_name(name)
        self._rpc: str = "none"
        if rpc in Channel.rpc_types:
            self._rpc = rpc
        elif rpc is not None:
            source = "/".join(["user_config", self.get_id()])
            validation_id = ".".join([self.get_id(), "RPC"])
            logger.error("Invalid LM rcp type '%s'", rpc, extra={"source": source, "validation_id": validation_id})
        self._rtime: int | None = rtime
        self._safe: str = "nseenv"
        if safe in self.safety_types:
            self._safe = safe
        elif safe is not None:
            source = "/".join(["user_config", self.get_id()])
            validation_id = ".".join([self.get_id(), "SAFE"])
            logger.error("Invalid LM safety type '%s'", safe, extra={"source": source, "validation_id": validation_id})
        self._group: int | None = group
        self._auto: str | None = None
        if auto in self.auto_boot_types:
            self._auto = auto
        elif auto is not None:
            source = "/".join(["user_config", self.get_id()])
            validation_id = ".".join([self.get_id(), "BOOT"])
            logger.error("Unknown LM Auto Boot type %s", auto, extra={"source": source, "validation_id": validation_id})
        self._default: bool = dflt
        self._agents: List[ScmiAgent] = []
        self._msels: List[MSEL] = []

    def add_agent(self, agent: ScmiAgent) -> None:
        """Adds given agent to this logical machine.

        Args:
            agent (ScmiAgent): The SCMI agent to add.
        """
        self._agents.append(agent)
        if not agent.get_owner():
            agent.set_owner(self)
        elif agent.get_owner() != self:
            raise CfgToolException(f"Cannot re-assign agent {agent.get_name()} to different LM")

    def get_all_agents(self) -> List[ScmiAgent]:
        """Returns all SCMI agents in this logical machine.

        Returns:
            List[ScmiAgent]: List of all SCMI agents.
        """
        return self._agents

    def get_all_msels(self) -> List[MSEL]:
        """Returns all MSEL objects in this logical machine.

        Returns:
            List[MSEL]: List of all MSEL objects.
        """
        return self._msels

    def get_max_msel_num(self) -> int:
        """Returns maximal msel number in all assigned MSELs.

        Returns:
            int: Maximum MSEL number.
        """
        ret = 0
        for m in self._msels:
            ret = max(ret, m.get_msel())
        return ret

    def get_all_faults(self) -> List[AssignedResource]:
        """Returns list of all faults in this logical machine.

        Returns:
            List[AssignedResource]: List of assigned resources with faults.
        """
        ret = []
        # resources assigned to LM
        for assr in self._resources:
            if len(assr.get_fault_resources()) > 0:
                ret.append(assr)
        # resources assigned to our child agents
        for ag in self._agents:
            for assr in ag.get_owned_resources():
                if len(assr.get_fault_resources()) > 0:
                    ret.append(assr)
        return ret

    def get_all_assignments(self, also_agents: bool = True) -> List[AssignedResource]:
        """Returns list of all assignments.

        Args:
            also_agents (bool): Whether to include agent assignments. Defaults to True.

        Returns:
            List[AssignedResource]: List of all assigned resources.
        """
        result = []
        # resources assigned to LM
        result += self._resources
        # resources assigned to our child agents
        if also_agents:
            for agent in self._agents:
                result += agent.get_owned_resources()
        return result

    def get_all_cpus(self) -> List[ApiResource]:
        """Returns list of all CPU resources in this logical machine.

        Returns:
            List[ApiResource]: List of CPU resources.
        """
        result = []
        for assigned_resource in self.get_all_assignments():
            for atomic_resource in assigned_resource.get_atomic_resources():
                if isinstance(atomic_resource, ApiResource) and atomic_resource.is_cpu():
                    result.append(atomic_resource)
        return result

    def get_all_start_stops(self, start: bool) -> List[StartStop]:
        """Returns list of all starts or stops in this logical machine.

        Args:
            start (bool): If True, returns start operations; if False, returns stop operations.

        Returns:
            List[StartStop]: List of start or stop operations.
        """
        result = []
        for msel in self._msels:
            if msel:
                result += msel.get_all_start_stops(start)
        return [start_stop for start_stop in result if start_stop is not None]

    def is_scmi(self) -> bool:
        """Returns True if this logical machine is set to work with SCMI protocol.

        Returns:
            bool: True if using SCMI protocol, False otherwise.
        """
        return self._rpc == "scmi"

    def get_msels(self) -> List[MSEL]:
        """Returns list of all MSEL objects in this logical machine.

        Returns:
            List[MSEL]: List of MSEL objects.
        """
        return self._msels

    def get_msel(self, msel_index: int, boot: int | None = None, skip: bool | None = None) -> MSEL:
        """Returns MSEL object based on its number. Creates the MSEL when it does not exist yet.

        Args:
            msel_index (int): The MSEL index to retrieve or create.
            boot (int | None): Boot order number. Defaults to None.
            skip (bool | None): Skip flag. Defaults to None.

        Returns:
            MSEL: The MSEL object.
        """
        for msel in self._msels:
            if msel.get_msel() == msel_index:
                source = "/".join(["user_config", self.get_id()])
                if boot is not None and boot != msel.get_boot():
                    validation_id = ".".join([self.get_id(), f"MSEL{msel_index}", "BOOT"])
                    logger.error("Redefining 'boot' for msel '%i'", msel_index, extra={"source": source, "validation_id": validation_id})
                if skip is not None and skip != msel.get_skip():
                    validation_id = ".".join([self.get_id(), f"MSEL{msel_index}", "SKIP"])
                    logger.error("Redefining 'skip' for msel '%i'", msel_index, extra={"source": source, "validation_id": validation_id})
                return msel
        msel = MSEL(self, msel_index, boot, skip)
        self._msels.append(msel)
        return msel

    def handle_start_stops(self, resource: AtomicResource | MacroResource, params: List[str]) -> bool:
        """Handles start and stop actions for API resources.

        Args:
            resource (AtomicResource | MacroResource): The resource to handle start/stop for.
            params (List[str]): List of parameters containing start/stop configuration.
        """
        if isinstance(resource, AtomicResource):
            start = utils.get_attribute_value_from_list(params, "start")
            stop = utils.get_attribute_value_from_list(params, "stop")
            has_test = "test" in params

            if start or stop:
                msel_param = utils.get_attribute_value_from_list(params, "msel")
                msel_index = utils.parse_int(msel_param) if msel_param else 0
                msel = self.get_msel(msel_index)
                if start:
                    msel.add_start_stop(True, has_test, resource, start)
                if stop:
                    msel.add_start_stop(False, has_test, resource, stop)
                return True
        return False

    def _collect_start_stop_sequences(self) -> List[StartStopSequence]:
        result = []
        # collect set of start stop lists
        for msel in self._msels:
            starts = msel.get_all_start_stops(start=True)
            if starts and starts not in result:
                result.append(starts)
            stops = msel.get_all_start_stops(start=False)
            if stops and stops not in result:
                result.append(stops)

        # add to msel
        for msel in self._msels:
            starts = msel.get_all_start_stops(start=True)
            stops = msel.get_all_start_stops(start=False)
            if starts:
                msel.set_start_sequence_index(result.index(starts))
            if stops:
                msel.set_stop_sequence_index(result.index(stops))

        return list(map(lambda start_stop: StartStopSequence(start_stop[0], self.get_name(), start_stop[1]), enumerate(result)))

    def get_assignment_json(self) -> Dict[str, Any]:
        """Returns JSON object with raw data.

        Returns:
            Dict[str, Any]: JSON object containing LM configuration data.
        """
        ret = super().get_assignment_json()
        ret |= {
            "type": "LM",
            "rtime": self._rtime,
            "group": self._group,
            "auto": self._auto,
            "default": self._default,
            "rpc": self._rpc,
            "safe": self._safe,
            "ss_sequences": [seq.get_assignment_json() for seq in self._collect_start_stop_sequences()],
            "msels": [m.get_assignment_json() for m in self._msels],
        }

        if self._rpc == "scmi":
            ret |= {"agents": [a.get_assignment_json() for a in self._agents]}
            ret |= {"resources": []}

        return ret

    def get_safe(self) -> str:
        """Returns the safe type of the logical machine.

        Returns:
            str: The safety type.
        """
        return self._safe

    def get_safe_define(self) -> str:
        """Returns safety define value.

        Returns:
            str: The safety define value.
        """
        return self.safety_types[self._safe]

    def get_boot(self) -> int:
        """Returns boot order of this logical machine.

        Returns:
            int: Boot order number.
        """
        msel_boot = self._msels[0].get_boot()
        return msel_boot if msel_boot is not None else 0

    def get_skip(self) -> bool:
        """Returns skip flag.

        Returns:
            bool: The skip flag value.
        """
        msel_skip = self._msels[0].get_skip()
        return msel_skip if msel_skip is not None else False

    def get_rpc(self) -> str:
        """Returns RPC type of this logical machine.

        Returns:
            str: The RPC type.
        """
        return self._rpc

    def get_rpc_define(self) -> str:
        """Returns RPC type define value.

        Returns:
            str: The RPC type define value.
        """
        if self._rpc in Channel.rpc_types:
            return Channel.rpc_types[self._rpc]
        return Channel.rpc_types["none"]

    def get_default(self) -> bool:
        """Returns default value.

        Returns:
            bool: The default flag value.
        """
        return self._default

    def get_rtime(self) -> int | None:
        """Returns relative boot time value.

        Returns:
            int | None: Relative boot time.
        """
        return self._rtime

    def get_auto(self) -> str | None:
        """Returns auto boot value.

        Returns:
            str | None: Auto boot type.
        """
        return self._auto

    def get_auto_define(self) -> str:
        """Returns auto boot define value.

        Returns:
            str: The auto boot define value.
        """
        if self._auto is None:
            return self.auto_boot_types["none"]
        return self.auto_boot_types[self._auto]

    def get_group(self) -> int | None:
        """Returns LM group value.

        Returns:
            int | None: The LM group number.
        """
        return self._group

    def __str__(self) -> str:
        """Returns string representation.

        Returns:
            str: String representation of the LM.
        """
        return self._id

    def __repr__(self) -> str:
        """Returns representation of this object.

        Returns:
            str: Detailed string representation of the LM.
        """
        auto_str = f"'{self._auto}'" if self._auto is not None else "''"
        return (
            f"{self.__class__.__name__}"
            f"('{self.get_id()}', '{self._name}', {self.get_boot()}, {self.get_skip()}, "
            f"'{self._rpc}', {self._rtime}, {self._group}, {auto_str}, {self._default})"
        )
