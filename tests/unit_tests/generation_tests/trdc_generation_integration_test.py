#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Integration tests for GeneratorTRDC._generate_trdc_configuration.

Drives MBC and MDAC assignments through the full generation path and
asserts observable generated #define / struct output content.

Split from trdc_generation_test.py (already >400 lines) per tests.instructions.md.
"""

# pylint: disable=protected-access

import io
from typing import Iterator
from unittest.mock import Mock

import pytest

from smct.configuration.configuration_provider import ConfigurationProvider
from smct.generation.gen_trdc import GeneratorTRDC
from smct.model.chip_model_provider import ChipModelProvider
from smct.model.model_trdc import TrdcModel
from smct.owners.owner_base import AssignedResource
from smct.resources.res_mbc import MbcResource
from smct.resources.res_mdac import MdacResource
from tests import test_utils


@pytest.fixture(autouse=True)
def restore_class_attrs() -> Iterator[None]:
    """Save and restore TrdcModel/MbcModel/MrcModel class-level attrs."""
    with test_utils.restore_trdc_class_attrs(
        pa_types={"bypass": 0, "privileged": 1},
        sa_types={"bypass": 0, "secure": 1},
        permission_types={"none": 0, "ro": 0x4444, "all": 0x7777},
        dfmt0_register=dict(test_utils.DFMT0_REG),
        dfmt1_register=dict(test_utils.DFMT1_REG),
        debug_domain_permission=0x7777,
    ):
        with test_utils.restore_mbc_mrc_class_attrs(block_size=4):
            yield


def _build_trdc(nmbc: int = 2, nmrc: int = 1) -> TrdcModel:
    """Create and return a TrdcModel 'A' with basic model params."""
    trdc = ChipModelProvider.get_model().get_trdc("A")
    assert trdc is not None
    trdc.set_model_params(ndid=4, nmstr=8, nmbc=nmbc, nmrc=nmrc, kpaen=0, sidsz=0)
    return trdc


def _mock_assigned_mbc(mbc: MbcResource, did: int = 1) -> AssignedResource:
    """Return a mock AssignedResource for the given MBC resource."""
    owner = Mock()
    owner.get_did.return_value = did
    owner.get_name.return_value = f"DOM{did}"
    owner.get_id.return_value = f"DOM{did}"
    ar = Mock(spec=AssignedResource)
    ar.get_owner.return_value = owner
    ar.get_trdc_resources.return_value = [mbc]
    ar.get_resource.return_value = mbc
    ar.get_params.return_value = {}
    ar.get_param_value.side_effect = lambda key, default=None: "all" if key == "perm" else default
    ar.get_param_value_int.side_effect = lambda key, default=0: default
    ar.should_generate_debug.return_value = False
    return ar


def _mock_assigned_mdac(mdac: MdacResource, did: int = 1) -> AssignedResource:
    """Return a mock AssignedResource for the given MDAC resource."""
    owner = Mock()
    owner.get_did.return_value = did
    owner.get_name.return_value = f"DOM{did}"
    owner.get_id.return_value = f"DOM{did}"
    ar = Mock(spec=AssignedResource)
    ar.get_owner.return_value = owner
    ar.get_trdc_resources.return_value = [mdac]
    ar.get_resource.return_value = mdac
    ar.get_params.return_value = {}
    ar.get_param_value.side_effect = lambda key, default=None: "bypass" if key in ("pa", "sa") else default
    ar.get_param_value_int.side_effect = lambda key, default=0: default
    ar.should_generate_debug.return_value = False
    return ar


def _run_generate(trdc: TrdcModel, assigned_resources: list) -> str:
    """Run _generate_trdc_configuration and return the string output."""
    generator = GeneratorTRDC()
    generator._open_file = io.StringIO()  # type: ignore[assignment]
    generator._conf = ConfigurationProvider.get_configuration()  # type: ignore[assignment]
    generator._generate_trdc_configuration(trdc, assigned_resources)
    return generator._open_file.getvalue()  # type: ignore[union-attr]


class TestIntegrateTrdcMdac:
    """Integration tests: MDAC assignments produce correct register entries."""

    def test_core_mdac_assignment_produces_dfmt0_register_in_output(self) -> None:
        """A core MDAC assignment writes a TRDC_A_MDA_W*_*_DFMT0 entry in the DCD."""
        trdc = _build_trdc()
        mdac = MdacResource({"name": "MDAC_TEST", "type": "MDAC", "trdc": "A", "master": 0, "core": True, "reg": 0, "rcnt": 1})
        ar = _mock_assigned_mdac(mdac, did=1)

        output = _run_generate(trdc, [ar])

        assert "TRDC_A_MDA_W0_0_DFMT0" in output
        assert "SM_TRDC_A_CONFIG" in output

    def test_mdac_assignment_always_includes_trdc_enable_word(self) -> None:
        """_generate_trdc_configuration always emits the 0x0000C001 TRDC enable word."""
        trdc = _build_trdc()
        mdac = MdacResource({"name": "MDAC_EN", "type": "MDAC", "trdc": "A", "master": 1, "core": True, "reg": 0, "rcnt": 1})
        ar = _mock_assigned_mdac(mdac, did=1)

        output = _run_generate(trdc, [ar])

        assert "0x0000C001" in output

    def test_non_core_mdac_assignment_produces_dfmt1_register(self) -> None:
        """A non-core MDAC assignment writes a DFMT1 register entry in the DCD."""
        trdc = _build_trdc()
        mdac = MdacResource({"name": "MDAC_NC", "type": "MDAC", "trdc": "A", "master": 2, "core": False, "reg": 0, "rcnt": 1})
        ar = _mock_assigned_mdac(mdac, did=1)

        output = _run_generate(trdc, [ar])

        assert "TRDC_A_MDA_W0_2_DFMT1" in output


class TestIntegrateTrdcMbc:
    """Integration tests: MBC assignments produce correct output."""

    def test_mbc_block_assignment_produces_sm_trdc_config_macro(self) -> None:
        """A single MBC block assignment produces the SM_TRDC_A_CONFIG macro in output."""
        trdc = _build_trdc(nmbc=2)
        trdc.get_mbc(0, create_if_needed=True)  # instantiate MBC model slot

        mbc = MbcResource({"name": "MBC_A_M0_B1", "type": "MBC", "trdc": "A", "mbc": 0, "mem": 0, "blk": 1})
        ar = _mock_assigned_mbc(mbc, did=1)

        output = _run_generate(trdc, [ar])

        assert "SM_TRDC_A_CONFIG" in output
        assert "0x0000C001" in output

    def test_empty_assigned_resources_generates_only_enable_word(self) -> None:
        """With no assignments, only the 0x0000C001 enable word is emitted."""
        trdc = _build_trdc()

        output = _run_generate(trdc, [])

        assert "SM_TRDC_A_CONFIG" in output
        assert "0x0000C001" in output
        # No block or master register entries expected
        assert "MBC_DOM" not in output
        assert "DFMT0" not in output

    def test_two_mbc_blocks_generate_write_macros(self) -> None:
        """Two block assignments in distinct domains each produce their SM_CFG write macro."""
        trdc = _build_trdc(nmbc=2)
        trdc.get_mbc(0, create_if_needed=True)

        mbc1 = MbcResource({"name": "MBC_B0", "type": "MBC", "trdc": "A", "mbc": 0, "mem": 0, "blk": 0})
        mbc2 = MbcResource({"name": "MBC_B4", "type": "MBC", "trdc": "A", "mbc": 0, "mem": 0, "blk": 4})
        ar1 = _mock_assigned_mbc(mbc1, did=1)
        ar2 = _mock_assigned_mbc(mbc2, did=2)

        output = _run_generate(trdc, [ar1, ar2])

        assert "SM_TRDC_A_CONFIG" in output
        assert "SM_CFG_W1" in output
        assert "SM_CFG_Z1" in output
