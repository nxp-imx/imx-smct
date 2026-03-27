#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause

"""Unit tests for utility functions"""

import unittest

import pytest

from smct import utils
from smct.utils import FormatedInt


def test_safe_string() -> None:
    """Test safe_string function"""
    assert utils.safe_string("") == ""
    assert utils.safe_string(None) == ""
    assert utils.safe_string("Lorem") == "Lorem"


def test_hex() -> None:
    """Test convert_to_hex function"""
    assert utils.convert_to_hex(0) == "0x00000000"
    assert utils.convert_to_hex(16) == "0x00000010"
    assert utils.convert_to_hex(15) == "0x0000000F"
    assert utils.convert_to_hex(0xF) == "0x0000000F"
    assert utils.convert_to_hex(255, digits=4) == "0x00FF"
    assert utils.convert_to_hex(255, digits=4, upper_case=False) == "0x00ff"
    assert utils.convert_to_hex(255, digits=1) == "0xFF"
    assert utils.convert_to_hex(255, digits=-1) == "0xFF"


def test_parse_int() -> None:
    """Test parse_int function"""
    assert utils.parse_int("0") == 0
    assert utils.parse_int("-128") == -128
    assert utils.parse_int("10") == 10
    assert utils.parse_int("10K", allow_units=True) == 10 * 1024
    assert utils.parse_int("10M", allow_units=True) == 10 * 1024 * 1024
    assert utils.parse_int("10G", allow_units=True) == 10 * 1024 * 1024 * 1024
    with pytest.raises(ValueError):
        assert utils.parse_int("")
    with pytest.raises(ValueError):
        assert utils.parse_int("lorem")


class TestFormatedInt(unittest.TestCase):
    """Test cases for FormatedInt class"""

    def test_init_with_different_formats(self) -> None:
        """Test initialization with various input formats"""
        test_cases: list[tuple[str | int, int, str, str]] = [
            # (input, expected_value, expected_base, expected_str)
            ("0x10", 16, "0x", "0x10"),
            ("0X20", 32, "0x", "0x20"),
            ("0xABCD", 43981, "0x", "0xabcd"),
            ("0b1010", 10, "0b", "0b1010"),
            ("0B1111", 15, "0b", "0b1111"),
            ("123", 123, "", "123"),
            ("1K", 1024, "", "1024"),
            ("2M", 2 * 1024 * 1024, "", str(2 * 1024 * 1024)),
            ("1G", 1024 * 1024 * 1024, "", str(1024 * 1024 * 1024)),
            (42, 42, "", "42"),
            (0, 0, "", "0"),
            (-10, -10, "", "-10"),
            ("5", 5, "", "5"),
        ]

        for input_val, expected_value, expected_base, expected_str in test_cases:
            with self.subTest(input=input_val):
                fi = FormatedInt(input_val)
                self.assertEqual(fi.get_value(), expected_value)
                self.assertEqual(fi.get_base(), expected_base)
                self.assertEqual(str(fi), expected_str)

    def test_edge_cases(self) -> None:
        """Test edge cases and boundary values"""
        # Zero values in different formats
        fi = FormatedInt("0x0")
        self.assertEqual(fi.get_value(), 0)
        self.assertEqual(str(fi), "0x0")

        fi = FormatedInt("0b0")
        self.assertEqual(fi.get_value(), 0)
        self.assertEqual(str(fi), "0b0")

        # Large hex value
        fi = FormatedInt("0xFFFFFFFF")
        self.assertEqual(fi.get_value(), 4294967295)
        self.assertEqual(str(fi), "0xffffffff")

        # Negative integer
        fi = FormatedInt(-1)
        self.assertEqual(fi.get_value(), -1)
        self.assertEqual(str(fi), "-1")

    def test_case_insensitive_inputs(self) -> None:
        """Test that case variations produce same results"""
        # Hex case insensitivity
        fi1 = FormatedInt("0x10")
        fi2 = FormatedInt("0X10")
        self.assertEqual(fi1.get_value(), fi2.get_value())
        self.assertEqual(fi1.get_base(), fi2.get_base())

        # Binary case insensitivity
        fi1 = FormatedInt("0b10")
        fi2 = FormatedInt("0B10")
        self.assertEqual(fi1.get_value(), fi2.get_value())
        self.assertEqual(fi1.get_base(), fi2.get_base())

        # Unit case insensitivity
        fi1 = FormatedInt("1k")
        fi2 = FormatedInt("1K")
        self.assertEqual(fi1.get_value(), fi2.get_value())


def test_parse_int_range() -> None:
    """Test parse_int_range function"""
    assert utils.parse_int_range("1") == (1, 1)
    assert utils.parse_int_range("1-10") == (1, 10)
    assert utils.parse_int_range("1 - 10") == (1, 10)
    assert utils.parse_int_range("1\t-\t10") == (1, 10)
    assert utils.parse_int_range("1-10", allow_single=False) == (1, 10)
    assert utils.parse_int_range("1K-10M", allow_units=True) == (1 * 1024, 10 * 1024 * 1024)
    with pytest.raises(ValueError):
        utils.parse_int_range("1", allow_single=False)
    with pytest.raises(ValueError):
        utils.parse_int_range("")
    with pytest.raises(ValueError):
        utils.parse_int_range("lorem")


def test_parse_line_to_atoms() -> None:
    """Test parse_line_to_atoms function"""
    assert utils.parse_line_to_atoms("") == []
    assert utils.parse_line_to_atoms("lorem ipsum -1") == ["lorem", "ipsum", "-1"]
    assert utils.parse_line_to_atoms("lorem,ipsum,-1") == ["lorem", "ipsum", "-1"]


def test_contains_attribute_in_list() -> None:
    """Test contains_attribute_in_list function"""
    atoms = ["lorem=42", "ipsum=7", "dolor=13", "test"]
    assert utils.contains_attribute_in_list(atoms, "ipsum", remove=True)
    assert "ipsum=7" not in atoms
    assert utils.contains_attribute_in_list(atoms, "test", no_value=True, remove=True)
    assert "test" not in atoms
    assert utils.contains_attribute_in_list(atoms, "lorem")
    assert "lorem=42" in atoms


def test_get_attribute_value_from_list() -> None:
    """Test get_attribute_value_from_list function"""
    atoms = ["lorem=42", "ipsum=7", "dolor=13"]
    assert utils.get_attribute_value_from_list(atoms, "ipsum", remove=True) == "7"
    assert "ipsum=7" not in atoms
    assert utils.get_attribute_value_from_list(atoms, "lorem") == "42"
    assert "lorem=42" in atoms


def test_set_at_index() -> None:
    """Test set_at_index function"""
    test_list: list[str] = []
    utils.set_at_index(test_list, 2, "lorem")
    assert test_list == [None, None, "lorem"]
    test_list = ["a", "b", "c", "d"]
    utils.set_at_index(test_list, 2, "lorem")
    assert test_list == ["a", "b", "lorem", "d"]


def test_get_bool() -> None:
    """Test get_bool function"""
    assert utils.get_bool(True)
    assert utils.get_bool("True")
    assert utils.get_bool("true")
    assert not utils.get_bool(False)
    assert not utils.get_bool("False")
    assert not utils.get_bool("false")

    assert not utils.get_bool("lorem")
    assert not utils.get_bool("Ipsum")


def test_parse_time_to_ms() -> None:
    """Test parse_time_to_ms function"""
    # keep spaces in all test vectors, will be tested without spaces too
    vectors = {
        "0": 0,
        "0 ms": 0,
        "0 sec": 0,
        "0 s": 0,
        "0 min": 0,
        "0 hr": 0,
        "0 hrs": 0,
        "0 hour": 0,
        "0 hours": 0,
        "1": 1,
        "1 ms": 1,
        "1.1": 1,
        "1.1 ms": 1,
        "1.5": 2,
        "1.5 ms": 2,
        "1 sec": 1000,
        "1 s": 1000,
        "1.5 sec": 1500,
        "1.5 s": 1500,
        "30 sec": 30000,
        "30 s": 30000,
        "1 min": 60000,
        "1.5 min": 90000,
        "1 hr": 3600000,
        "1 hrs": 3600000,
        "1 hour": 3600000,
        "1 hours": 3600000,
        "1.5 hr": 5400000,
        "1 day": 86400000,
        "1 days": 86400000,
    }
    invalid = [
        "",
        "xyz",
        "1x",
        "1.2.3",
        "1 xyz",
    ]

    for spaced in (True, False):
        for v in vectors:
            vec = v if spaced else v.replace(" ", "")
            assert utils.parse_time_to_ms(vec) == vectors[v]

    for i in invalid:
        assert utils.parse_time_to_ms(i) is None
