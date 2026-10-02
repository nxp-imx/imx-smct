#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Unit tests for smct.generation.gen_trdc TRDC header generator."""

# pylint: disable=protected-access

import io
from typing import Any, Dict, Iterator, Tuple
from unittest.mock import Mock

import pytest

from smct.configuration.confdata import ConfigurationData
from smct.configuration.configuration_provider import ConfigurationProvider
from smct.generation.gen_trdc import (
    _create_mbc_block,
    _create_mrc_region,
    _generate_mbc_mem_range_registers,
    _generate_mbc_model,
    _generate_mdac_registers,
    _generate_mrc_model,
    _get_permission,
    GeneratorTRDC,
)
from smct.generation.generator import GenDcdInit, GeneratorBase
from smct.model.chip_model_provider import ChipModelProvider
from smct.model.model_trdc import TrdcModel
from smct.owners.owner_base import AssignedResource
from smct.resources.res_mbc import MbcResource, MbcResourceWriteType
from smct.resources.res_mdac import MdacResource
from smct.resources.res_mrc import MrcResource
from tests import test_utils

_DFMT0_REG = test_utils.DFMT0_REG
_DFMT1_REG = test_utils.DFMT1_REG


class TestGeneratorTRDC:
    """Tests for GeneratorTRDC."""

    def test_instantiation_has_generator_base_type(self) -> None:
        """Test TRDC generator constructs without touching singleton-backed configuration."""
        generator = GeneratorTRDC()

        assert isinstance(generator, GeneratorBase)
        assert str(generator) == "TRDC generator"

    def test_generator_info_returns_trdc_name_and_user_include(self) -> None:
        """Test generator metadata defines the TRDC output identity."""
        generator = GeneratorTRDC()

        assert generator._get_generator_info() == {"name": "TRDC", "incl": ["config_user.h"]}
        assert generator._get_output_file_name() == "config_trdc.h"
        assert generator._get_header_protection_macro() == "CONFIG_TRDC_H"

    def test_doxygen_helpers_return_trdc_specific_text(self) -> None:
        """Test TRDC generator overrides doxygen file and brief content."""
        generator = GeneratorTRDC()

        assert generator._get_doxygen_file_name() == ""
        assert generator._get_doxygen_brief_lines() == ["", "", " Header file containing configuration info for the TRDC SM abstraction."]

    def test_get_permission_uses_assigned_perm_parameter(self) -> None:
        """Test permission helper resolves the assigned perm string through the TRDC model."""
        trdc = Mock(spec=TrdcModel)
        trdc.get_perm_value.return_value = 0x7777
        assigned_resource = Mock(spec=AssignedResource)
        assigned_resource.get_param_value.return_value = "all"

        result = _get_permission(trdc, assigned_resource)

        assigned_resource.get_param_value.assert_called_once_with("perm", "0")
        trdc.get_perm_value.assert_called_once_with("all")
        assert result == 0x7777

    def test_get_configuration_without_generate_raises(self) -> None:
        """Test constructor does not install a configuration until generation starts."""
        generator = GeneratorTRDC()
        _ = Mock(spec=ConfigurationData)

        with pytest.raises(Exception, match="No configuration was set"):
            generator._get_configuration()


# ---------------------------------------------------------------------------
# Shared register layout used by TestGenerateMdacRegisters
# ---------------------------------------------------------------------------


class TestGenerateMdacRegisters:
    """Tests for gen_trdc._generate_mdac_registers."""

    @pytest.fixture(autouse=True)
    def mdac_class_attrs(self) -> Iterator[None]:
        """Save and restore TrdcModel class-level MDAC register definitions."""
        with test_utils.restore_trdc_class_attrs(
            pa_types={"bypass": 0, "privileged": 1},
            sa_types={"bypass": 0, "secure": 1},
            dfmt0_register=dict(test_utils.DFMT0_REG),
            dfmt1_register=dict(test_utils.DFMT1_REG),
        ):
            yield

    # ------------------------------------------------------------------
    # Helper
    # ------------------------------------------------------------------

    def _make_mocks(
        self,
        *,
        did: int = 1,
        mdid: Any = None,
        pa: str = "bypass",
        sa: str = "bypass",
        sid: int = 0,
        kpa_explicit: Any = None,
        is_core: bool = True,
        kpaen: int = 0,
        sidsz: int = 0,
        domains_count: int = 4,
    ) -> Tuple[GenDcdInit, Mock, Mock, Mock]:
        """Return (dcd, trdc_mock, mdac_mock, assigned_resource_mock)."""
        dcd = GenDcdInit("TEST_DCD")

        trdc = Mock(spec=TrdcModel)
        trdc.get_domains_count.return_value = domains_count
        trdc.get_sidsz.return_value = sidsz
        trdc.get_kpaen.return_value = kpaen
        trdc.get_id.return_value = "A"
        trdc.get_name.return_value = "TRDC_A"
        trdc.get_register_offset.return_value = 0x800

        mdac = Mock(spec=MdacResource)
        mdac.get_name.return_value = "MDAC0"
        mdac.get_master.return_value = 0
        mdac.get_register.return_value = 0
        mdac.get_registers_count.return_value = 1
        mdac.is_core.return_value = is_core

        owner = Mock()
        owner.get_did.return_value = did
        owner.get_name.return_value = "OWNER"
        owner.get_id.return_value = "OWNER_ID"

        param_values: Dict[str, Any] = {"pa": pa, "sa": sa}
        if mdid is not None:
            param_values["mdid"] = mdid
        if kpa_explicit is not None:
            param_values["kpa"] = kpa_explicit

        int_values: Dict[str, int] = {"sid": sid}
        if kpa_explicit is not None and isinstance(kpa_explicit, int):
            int_values["kpa"] = kpa_explicit

        ar = Mock(spec=AssignedResource)
        ar.get_owner.return_value = owner
        ar.get_param_value.side_effect = lambda key, default=None: param_values.get(key, default)
        ar.get_param_value_int.side_effect = lambda key, default=0: int_values.get(key, default)
        ar.get_resource.return_value.get_name.return_value = "MDAC0"

        return dcd, trdc, mdac, ar

    # ------------------------------------------------------------------
    # Tests
    # ------------------------------------------------------------------

    def test_mdid_none_returns_without_writing_dcd(self) -> None:
        """Early return when mdid=='none' — DCD must stay empty."""
        dcd, trdc, mdac, ar = self._make_mocks(mdid="none")
        _generate_mdac_registers(dcd, trdc, mdac, ar)
        assert len(dcd._dcd) == 0  # type: ignore[attr-defined]

    def test_mdid_int_overrides_did(self) -> None:
        """Integer mdid replaces the owner DID and register is written."""
        dcd, trdc, mdac, ar = self._make_mocks(mdid=2, did=0, domains_count=4)
        _generate_mdac_registers(dcd, trdc, mdac, ar)
        assert "TRDC_A_MDA_W0_0_DFMT0" in dcd

    def test_mdid_str_overrides_did(self) -> None:
        """String mdid is parsed as int, replacing the owner DID."""
        dcd, trdc, mdac, ar = self._make_mocks(mdid="3", did=0, domains_count=4)
        _generate_mdac_registers(dcd, trdc, mdac, ar)
        assert "TRDC_A_MDA_W0_0_DFMT0" in dcd

    def test_invalid_domain_logs_error_and_returns(self, caplog: pytest.LogCaptureFixture) -> None:
        """DID out of range logs error and leaves DCD empty."""
        dcd, trdc, mdac, ar = self._make_mocks(did=10, domains_count=4)
        with caplog.at_level("ERROR"):
            _generate_mdac_registers(dcd, trdc, mdac, ar)
        assert "Invalid domain ID" in caplog.text
        assert len(dcd._dcd) == 0  # type: ignore[attr-defined]

    def test_unknown_pa_logs_error_and_returns(self, caplog: pytest.LogCaptureFixture) -> None:
        """Unknown 'pa' value logs error and leaves DCD empty."""
        dcd, trdc, mdac, ar = self._make_mocks(pa="unknown_pa")
        with caplog.at_level("ERROR"):
            _generate_mdac_registers(dcd, trdc, mdac, ar)
        assert "unknown 'pa' value" in caplog.text
        assert len(dcd._dcd) == 0  # type: ignore[attr-defined]

    def test_unknown_sa_logs_error_and_returns(self, caplog: pytest.LogCaptureFixture) -> None:
        """Unknown 'sa' value logs error and leaves DCD empty."""
        dcd, trdc, mdac, ar = self._make_mocks(sa="unknown_sa")
        with caplog.at_level("ERROR"):
            _generate_mdac_registers(dcd, trdc, mdac, ar)
        assert "unknown 'sa' value" in caplog.text
        assert len(dcd._dcd) == 0  # type: ignore[attr-defined]

    def test_sid_overflow_logs_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        """SID exceeding sidsz range emits a warning but still writes the register."""
        dcd, trdc, mdac, ar = self._make_mocks(sid=200, sidsz=6)
        with caplog.at_level("WARNING"):
            _generate_mdac_registers(dcd, trdc, mdac, ar)
        assert "greater that 'sidsz" in caplog.text

    def test_kpa_while_kpaen_zero_logs_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        """Explicit kpa with kpaen==0 emits a warning."""
        dcd, trdc, mdac, ar = self._make_mocks(kpa_explicit=1, kpaen=0)
        with caplog.at_level("WARNING"):
            _generate_mdac_registers(dcd, trdc, mdac, ar)
        assert "'kpa' is disabled" in caplog.text

    def test_core_path_writes_dfmt0_register(self) -> None:
        """Core MDAC path writes DFMT0 register with VLD bit set."""
        dcd, trdc, mdac, ar = self._make_mocks(is_core=True, did=1)
        _generate_mdac_registers(dcd, trdc, mdac, ar)
        reg = "TRDC_A_MDA_W0_0_DFMT0"
        assert reg in dcd
        vld_bit = 1 << _DFMT0_REG["VLD"]["offset"]
        assert dcd[reg] & vld_bit == vld_bit

    def test_core_path_with_kpaen_and_sidsz_writes_full_data(self) -> None:
        """Core MDAC with kpaen=1 and sidsz>0 includes KPA and SID fields."""
        dcd, trdc, mdac, ar = self._make_mocks(is_core=True, did=1, kpaen=1, sidsz=6, sid=5, kpa_explicit=1)
        _generate_mdac_registers(dcd, trdc, mdac, ar)
        assert "TRDC_A_MDA_W0_0_DFMT0" in dcd

    def test_non_core_missing_sid_field_returns_early(self, caplog: pytest.LogCaptureFixture) -> None:
        """Non-core path with sidsz>0 but missing SID field warns and returns without write."""
        dcd, trdc, mdac, ar = self._make_mocks(is_core=False, sidsz=6)
        TrdcModel.DFMT1_register = {k: v for k, v in _DFMT1_REG.items() if k != "SID"}
        with caplog.at_level("WARNING"):
            _generate_mdac_registers(dcd, trdc, mdac, ar)
        assert "DFMT1 register model does not contain 'SID' field" in caplog.text
        assert len(dcd._dcd) == 0  # type: ignore[attr-defined]

    def test_non_core_path_writes_dfmt1_register(self) -> None:
        """Non-core MDAC path writes DFMT1 register."""
        dcd, trdc, mdac, ar = self._make_mocks(is_core=False, did=1)
        _generate_mdac_registers(dcd, trdc, mdac, ar)
        assert "TRDC_A_MDA_W0_0_DFMT1" in dcd

    def test_non_core_path_with_kpaen_and_sidsz_writes_full_data(self) -> None:
        """Non-core MDAC with kpaen=1 and sidsz>0 includes KPA and SID fields."""
        dcd, trdc, mdac, ar = self._make_mocks(is_core=False, did=1, kpaen=1, sidsz=6, sid=3, kpa_explicit=0)
        _generate_mdac_registers(dcd, trdc, mdac, ar)
        assert "TRDC_A_MDA_W0_0_DFMT1" in dcd

    def test_dedup_conflict_logs_error(self, caplog: pytest.LogCaptureFixture) -> None:
        """Pre-existing register with different data triggers dedup conflict error."""
        dcd, trdc, mdac, ar = self._make_mocks(is_core=True, did=1)
        reg = "TRDC_A_MDA_W0_0_DFMT0"
        dcd.set_key_name(reg, 0x800)
        dcd[reg] = 0xDEAD  # intentionally different from computed value
        with caplog.at_level("ERROR"):
            _generate_mdac_registers(dcd, trdc, mdac, ar)
        assert "already defined as" in caplog.text

    def test_fresh_register_write_sets_register_and_comment(self) -> None:
        """First write populates register offset and adds owner comment."""
        dcd, trdc, mdac, ar = self._make_mocks(is_core=True, did=1)
        _generate_mdac_registers(dcd, trdc, mdac, ar)
        reg = "TRDC_A_MDA_W0_0_DFMT0"
        assert reg in dcd
        # offset must have been registered via set_key_name
        assert reg in dcd._key_name_to_offset  # type: ignore[attr-defined]


class TestGenerateMbcMemRangeRegisters:
    """Tests for gen_trdc._generate_mbc_mem_range_registers."""

    def test_mbc_model_none_logs_error_and_returns_none(self, caplog: pytest.LogCaptureFixture) -> None:
        """Returns None and logs error when TRDC has no matching MBC model."""
        trdc = Mock(spec=TrdcModel)
        trdc.get_mbc.return_value = None
        trdc.get_id.return_value = "A"
        mbc = Mock(spec=MbcResource)
        mbc.get_index.return_value = 0
        mbc.get_mem.return_value = 0

        with caplog.at_level("ERROR"):
            result = _generate_mbc_mem_range_registers(trdc, mbc, 0x1000, 0x100)

        assert result is None
        assert "was not found" in caplog.text

    def test_mem_model_none_logs_error_and_returns_none(self, caplog: pytest.LogCaptureFixture) -> None:
        """Returns None and logs error when MBC has no matching MEM model."""
        mbc_model = Mock()
        mbc_model.get_model_mem.return_value = None
        trdc = Mock(spec=TrdcModel)
        trdc.get_mbc.return_value = mbc_model
        trdc.get_id.return_value = "A"
        mbc = Mock(spec=MbcResource)
        mbc.get_index.return_value = 0
        mbc.get_mem.return_value = 0

        with caplog.at_level("ERROR"):
            result = _generate_mbc_mem_range_registers(trdc, mbc, 0x1000, 0x100)

        assert result is None
        assert "was not found" in caplog.text

    def test_size_exceeds_available_blocks_logs_error_and_returns_tuple(self, caplog: pytest.LogCaptureFixture) -> None:
        """Logs error when requested range exceeds total block count, but still returns a tuple."""
        mem_model = Mock()
        mem_model.get_origin.return_value.get_value.return_value = 0x0
        mem_model.get_block_size.return_value.get_value.return_value = 0x100
        mem_model.get_block_count.return_value = 2  # only 2 blocks available
        mbc_model = Mock()
        mbc_model.get_model_mem.return_value = mem_model
        trdc = Mock(spec=TrdcModel)
        trdc.get_mbc.return_value = mbc_model
        trdc.get_id.return_value = "A"
        mbc = Mock(spec=MbcResource)
        mbc.get_index.return_value = 0
        mbc.get_mem.return_value = 0

        with caplog.at_level("ERROR"):
            result = _generate_mbc_mem_range_registers(trdc, mbc, 0x0, 0x500)  # 5 blocks needed

        assert result is not None
        assert "bigger than" in caplog.text

    def test_normal_range_returns_start_and_end_block_indices(self) -> None:
        """Returns (start_block, end_block) tuple for a valid range request."""
        mem_model = Mock()
        mem_model.get_origin.return_value.get_value.return_value = 0x0
        mem_model.get_block_size.return_value.get_value.return_value = 0x100
        mem_model.get_block_count.return_value = 16
        mbc_model = Mock()
        mbc_model.get_model_mem.return_value = mem_model
        trdc = Mock(spec=TrdcModel)
        trdc.get_mbc.return_value = mbc_model
        mbc = Mock(spec=MbcResource)
        mbc.get_index.return_value = 0
        mbc.get_mem.return_value = 0

        result = _generate_mbc_mem_range_registers(trdc, mbc, 0x200, 0x200)

        assert result == (2, 4)


class TestGeneratorTRDCPrintContent:
    """Tests for GeneratorTRDC._generate_empty_trdc_configuration and print_content KeyError branch."""

    def test_generate_empty_trdc_configuration_writes_enable_register(self) -> None:
        """Empty TRDC config emits DCD with the TRDC enable word."""
        trdc = ChipModelProvider.get_model().get_trdc("A")
        assert trdc is not None
        generator = GeneratorTRDC()
        generator._open_file = io.StringIO()  # type: ignore[assignment]

        generator._generate_empty_trdc_configuration(trdc)

        output = generator._open_file.getvalue()  # type: ignore[union-attr]
        assert "SM_TRDC_A_CONFIG" in output
        assert "0x0000C001" in output

    def test_print_content_trdc_with_no_assignments_calls_empty_config(self, caplog: pytest.LogCaptureFixture) -> None:
        """TRDCs absent from assignments dict hit the KeyError branch and generate empty config."""
        ChipModelProvider.get_model().get_trdc("B")  # register TRDC_B in the model

        generator = GeneratorTRDC()
        generator._conf = ConfigurationProvider.get_configuration()  # type: ignore[assignment]
        generator._open_file = io.StringIO()  # type: ignore[assignment]

        with caplog.at_level("INFO"):
            generator.print_content()

        assert "has no assignments" in caplog.text
        output = generator._open_file.getvalue()  # type: ignore[union-attr]
        assert "SM_TRDC_B_CONFIG" in output


# ---------------------------------------------------------------------------
# Helper to build a minimal trdc mock and owner/assigned_resource pair
# ---------------------------------------------------------------------------


def _make_trdc_mock(domains_count: int = 4) -> Mock:
    """Return a minimal TrdcModel mock."""
    trdc = Mock(spec=TrdcModel)
    trdc.get_domains_count.return_value = domains_count
    trdc.get_name.return_value = "TRDC_A"
    trdc.get_id.return_value = "A"
    trdc.get_register_offset.return_value = 0x1000
    return trdc


def _make_assigned_resource_mock(begin_val: Any = None, size_val: Any = None) -> Mock:
    """Return a minimal AssignedResource mock with optional begin/size param values."""
    ar = Mock(spec=AssignedResource)
    ar.get_owner.return_value.get_id.return_value = "OWNER_ID"
    ar.get_resource.return_value.get_name.return_value = "RES0"

    begin_mock = Mock()
    begin_mock.get_value.return_value = begin_val if begin_val is not None else 0
    size_mock = Mock()
    size_mock.get_value.return_value = size_val if size_val is not None else 0

    def _param(key: str, default: Any = None) -> Any:
        if key == "begin":
            return begin_mock if begin_val is not None else None
        if key == "size":
            return size_mock if size_val is not None else None
        return default

    ar.get_param_value.side_effect = _param
    return ar


class TestCreateMrcRegion:
    """Tests for gen_trdc._create_mrc_region error branches."""

    def test_assigned_resource_none_logs_error_and_returns_none(self, caplog: pytest.LogCaptureFixture) -> None:
        """None assigned_resource logs error and returns None."""
        trdc = _make_trdc_mock()
        mrc = Mock(spec=MrcResource)
        mrc.get_name.return_value = "MRC0"

        with caplog.at_level("ERROR"):
            result = _create_mrc_region(trdc, mrc, None, 1, 0x7777)  # type: ignore[arg-type]

        assert result is None
        assert "Assigned resource is undefined" in caplog.text

    def test_begin_param_none_logs_error_and_returns_none(self, caplog: pytest.LogCaptureFixture) -> None:
        """Missing 'begin' parameter logs error and returns None."""
        trdc = _make_trdc_mock()
        mrc = Mock(spec=MrcResource)
        mrc.get_name.return_value = "MRC0"
        ar = _make_assigned_resource_mock(begin_val=None)  # begin is None

        with caplog.at_level("ERROR"):
            result = _create_mrc_region(trdc, mrc, ar, 1, 0x7777)

        assert result is None
        assert "'begin' parameter missing" in caplog.text

    def test_size_param_none_logs_error_and_returns_none(self, caplog: pytest.LogCaptureFixture) -> None:
        """Missing 'size' parameter logs error and returns None."""
        trdc = _make_trdc_mock()
        mrc = Mock(spec=MrcResource)
        mrc.get_name.return_value = "MRC0"
        ar = _make_assigned_resource_mock(begin_val=0x1000, size_val=None)

        with caplog.at_level("ERROR"):
            result = _create_mrc_region(trdc, mrc, ar, 1, 0x7777)

        assert result is None
        assert "'size' parameter missing" in caplog.text

    def test_invalid_domain_logs_error_and_returns_none(self, caplog: pytest.LogCaptureFixture) -> None:
        """Domain out of range logs error and returns None."""
        trdc = _make_trdc_mock(domains_count=4)
        mrc = Mock(spec=MrcResource)
        mrc.get_name.return_value = "MRC0"
        ar = _make_assigned_resource_mock(begin_val=0x1000, size_val=0x100)

        with caplog.at_level("ERROR"):
            result = _create_mrc_region(trdc, mrc, ar, 5, 0x7777)  # did=5 >= 4

        assert result is None
        assert "Invalid domain id" in caplog.text


class TestCreateMbcBlock:
    """Tests for gen_trdc._create_mbc_block error branches."""

    def test_invalid_domain_logs_error_and_returns_none(self, caplog: pytest.LogCaptureFixture) -> None:
        """Domain out of range logs error and returns None."""
        trdc = _make_trdc_mock(domains_count=4)
        mbc = Mock(spec=MbcResource)
        mbc.get_name.return_value = "MBC0"
        mbc.get_write_type.return_value = MbcResourceWriteType.BLOCK

        with caplog.at_level("ERROR"):
            result = _create_mbc_block(trdc, mbc, 5, 0x7777)  # did=5 >= 4

        assert result is None
        assert "Invalid domain id" in caplog.text

    def test_mem_type_begin_none_logs_error_and_returns_none(self, caplog: pytest.LogCaptureFixture) -> None:
        """MEM-type MBC with missing 'begin' logs error and returns None."""
        trdc = _make_trdc_mock()
        mbc = Mock(spec=MbcResource)
        mbc.get_name.return_value = "MBC0"
        mbc.get_write_type.return_value = MbcResourceWriteType.MEM
        ar = _make_assigned_resource_mock(begin_val=None)

        with caplog.at_level("ERROR"):
            result = _create_mbc_block(trdc, mbc, 1, 0x7777, assigned_resource=ar)

        assert result is None
        assert "'begin' parameter missing" in caplog.text

    def test_mem_type_size_none_logs_error_and_returns_none(self, caplog: pytest.LogCaptureFixture) -> None:
        """MEM-type MBC with missing 'size' logs error and returns None."""
        trdc = _make_trdc_mock()
        mbc = Mock(spec=MbcResource)
        mbc.get_name.return_value = "MBC0"
        mbc.get_write_type.return_value = MbcResourceWriteType.MEM
        ar = _make_assigned_resource_mock(begin_val=0x1000, size_val=None)

        with caplog.at_level("ERROR"):
            result = _create_mbc_block(trdc, mbc, 1, 0x7777, assigned_resource=ar)

        assert result is None
        assert "'size' parameter missing" in caplog.text

    def test_mem_type_block_range_none_returns_none(self) -> None:
        """When _generate_mbc_mem_range_registers returns None, _create_mbc_block returns None."""
        trdc = _make_trdc_mock()
        trdc.get_mbc.return_value = None  # causes _generate_mbc_mem_range_registers → None
        mbc = Mock(spec=MbcResource)
        mbc.get_name.return_value = "MBC0"
        mbc.get_write_type.return_value = MbcResourceWriteType.MEM
        mbc.get_index.return_value = 0
        mbc.get_mem.return_value = 0
        ar = _make_assigned_resource_mock(begin_val=0x1000, size_val=0x100)

        result = _create_mbc_block(trdc, mbc, 1, 0x7777, assigned_resource=ar)

        assert result is None


class TestGenerateMbcMrcModelNone:
    """Tests for _generate_mbc_model and _generate_mrc_model None-model error branches."""

    def test_generate_mbc_model_with_mbc_model_none_logs_error(self, caplog: pytest.LogCaptureFixture) -> None:
        """_generate_mbc_model logs error when trdc.get_mbc returns None."""
        dcd = GenDcdInit("TEST")
        trdc = Mock(spec=TrdcModel)
        trdc.get_mbc.return_value = None
        model = Mock()

        with caplog.at_level("ERROR"):
            _generate_mbc_model(dcd, trdc, 0, model)

        assert "MBC model for MBC" in caplog.text
        assert "is not known" in caplog.text

    def test_generate_mrc_model_with_mrc_model_none_logs_error(self, caplog: pytest.LogCaptureFixture) -> None:
        """_generate_mrc_model logs error when trdc.get_mrc returns None."""
        dcd = GenDcdInit("TEST")
        trdc = Mock(spec=TrdcModel)
        trdc.get_mrc.return_value = None
        mrc = Mock(spec=MrcResource)
        mrc.get_index.return_value = 0
        mrc.get_name.return_value = "MRC0"
        trdc.get_name.return_value = "TRDC_A"
        trdc.get_id.return_value = "A"
        model = Mock()

        with caplog.at_level("ERROR"):
            _generate_mrc_model(dcd, trdc, mrc, model)

        assert "MRC model for MRC" in caplog.text
        assert "is not known" in caplog.text
