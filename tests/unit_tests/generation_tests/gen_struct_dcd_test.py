#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Unit tests for GenStructInit, GenStructInitInline, GenDcdInit, and GenCfgMacro helpers."""

import io

import pytest

from smct.generation.generator import (
    GenCfgMacro,
    GenDcdInit,
    GenStructInit,
    GenStructInitInline,
)


class TestGenStructInit:
    """Tests for GenStructInit structure initializer."""

    def test_setitem_getitem_round_trip(self) -> None:
        """Values set via __setitem__ can be retrieved with __getitem__."""
        gen = GenStructInit("STRUCT")
        gen["field"] = 99

        assert gen["field"] == 99

    def test_integer_member_gets_u_suffix(self) -> None:
        """Integer struct members are rendered with a U suffix."""
        gen = GenStructInit("S")
        gen["count"] = 5
        gen.print_members()

        assert "5U" in gen.get_members_string()

    def test_bool_member_converted_to_int(self) -> None:
        """Boolean struct members are rendered as 1U or 0U."""
        gen = GenStructInit("S")
        gen["flag"] = True
        gen.print_members()

        assert "1U" in gen.get_members_string()

    def test_set_sorting_changes_output_order(self) -> None:
        """set_sorting(True) sorts the members alphabetically."""
        gen = GenStructInit("S")
        gen.set_sorting(True)
        gen["z_field"] = 1
        gen["a_field"] = 2
        gen.print_members()

        result = gen.get_members_string()
        assert result.index("a_field") < result.index("z_field")

    def test_get_define_returns_name(self) -> None:
        """get_define() returns the macro name."""
        gen = GenStructInit("MY_STRUCT")

        assert gen.get_define() == "MY_STRUCT"

    def test_full_print_contains_define_and_braces(self) -> None:
        """Full print cycle produces #define, opening brace, and closing brace."""
        gen = GenStructInit("STRUCT_MACRO")
        gen["x"] = 1
        buf = io.StringIO()

        gen.print(file=buf)

        output = buf.getvalue()
        assert "#define STRUCT_MACRO" in output
        assert "{" in output
        assert "}" in output


class TestGenStructInitInline:
    """Tests for GenStructInitInline compact structure initializer."""

    def test_add_entry_values_appear_in_output(self) -> None:
        """Values added via add_entry() appear in rendered members."""
        gen = GenStructInitInline("INLINE")
        gen.add_entry("a", 1)
        gen.add_entry("b", "str_val")
        gen.print_members()

        result = gen.get_members_string()
        assert ".a = 1U" in result
        assert ".b = str_val" in result

    def test_add_break_line_inserts_continuation(self) -> None:
        """add_break_line() inserts a line-continuation marker."""
        gen = GenStructInitInline("INLINE")
        gen.add_entry("before", 0)
        gen.add_break_line()
        gen.add_entry("after", 1)
        gen.print_members()

        result = gen.get_members_string()
        assert "\\\n" in result

    def test_bool_entry_rendered_as_u_suffix_int(self) -> None:
        """Boolean entry values are rendered as 1U or 0U."""
        gen = GenStructInitInline("INLINE")
        gen.add_entry("flag", False)
        gen.print_members()

        assert "0U" in gen.get_members_string()

    def test_empty_entries_produces_empty_members(self) -> None:
        """No entries produces an empty members string."""
        gen = GenStructInitInline("INLINE")
        gen.print_members()

        assert gen.get_members_string() == ""


class TestGenDcdInit:
    """Tests for GenDcdInit DCD initializer helper."""

    def test_setitem_getitem_with_int_key(self) -> None:
        """Integer key can be set and retrieved."""
        gen = GenDcdInit("DCD")
        gen[0x40000000] = 0xDEAD

        assert gen[0x40000000] == 0xDEAD

    def test_contains_with_int_key(self) -> None:
        """__contains__ returns True for a stored integer key."""
        gen = GenDcdInit("DCD")
        gen[0x100] = 1

        assert 0x100 in gen

    def test_contains_with_string_key_after_set_key_name(self) -> None:
        """__contains__ uses the name-to-offset mapping for string keys."""
        gen = GenDcdInit("DCD")
        gen.set_key_name("MY_REG", 0x200)

        assert "MY_REG" in gen

    def test_setitem_with_string_key_after_set_key_name(self) -> None:
        """String key assignment resolves through the name-to-offset map."""
        gen = GenDcdInit("DCD")
        gen.set_key_name("REG", 0x300)
        gen["REG"] = 0xFF

        assert gen["REG"] == 0xFF

    def test_set_key_name_duplicate_with_same_offset_is_allowed(self) -> None:
        """Re-registering the same name with the same offset does not raise."""
        gen = GenDcdInit("DCD")
        gen.set_key_name("K", 10)
        gen.set_key_name("K", 10)  # should not raise

    def test_set_key_name_duplicate_with_different_offset_raises(self) -> None:
        """Re-registering the same name with a different offset raises KeyError."""
        gen = GenDcdInit("DCD")
        gen.set_key_name("K", 10)

        with pytest.raises(KeyError):
            gen.set_key_name("K", 20)

    def test_add_key_comment_stored_and_rendered(self) -> None:
        """Comments added via add_key_comment appear in the rendered output."""
        gen = GenDcdInit("DCD")
        gen.set_key_name("R", 0x0)
        gen["R"] = 0x1
        gen.add_key_comment("R", "register comment")
        gen.print_members()

        assert "register comment" in gen.get_members_string()

    def test_set_sort_false_preserves_insertion_order(self) -> None:
        """set_sort(False) preserves insertion order."""
        gen = GenDcdInit("DCD")
        gen.set_sort(False)
        gen[0x30] = 3
        gen[0x10] = 1
        gen[0x20] = 2
        gen.print_members()

        result = gen.get_members_string()
        assert result.index("0x00000030") < result.index("0x00000010")

    def test_empty_dcd_produces_empty_list_comment(self) -> None:
        """An empty DCD renders an '/* empty list */' comment."""
        gen = GenDcdInit("DCD")
        gen.print_members()

        assert "empty list" in gen.get_members_string()

    def test_full_print_contains_sm_cfg_macros(self) -> None:
        """Full print cycle for a non-empty DCD contains SM_CFG_W1 for a non-zero value."""
        gen = GenDcdInit("DCD")
        gen[0x10] = 0xABCD
        buf = io.StringIO()

        gen.print(file=buf)

        output = buf.getvalue()
        # When key=0x10 (non-zero address, non-zero value) SM_CFG_W1 is used
        assert "SM_CFG_W1(0x00000010U)" in output


class TestGenCfgMacro:
    """Tests for GenCfgMacro .cfg file macro formatter."""

    def test_get_returns_name_and_value(self) -> None:
        """get() returns name and value in the formatted string."""
        macro = GenCfgMacro("DEVICE", "imx95")

        result = macro.get()

        assert "DEVICE" in result
        assert "imx95" in result

    def test_append_comma_separates_multiple_values(self) -> None:
        """append() with default auto_comma adds a comma before the new value."""
        macro = GenCfgMacro("M", "first")
        macro.append("second")

        result = macro.get()

        assert "first, second" in result

    def test_append_no_auto_comma_when_disabled(self) -> None:
        """append() with auto_comma=False does not add a comma."""
        macro = GenCfgMacro("M", "a")
        macro.append("b", auto_comma=False)

        result = macro.get()

        assert "a, b" not in result
        assert "ab" in result

    def test_set_commented_out_adds_hash_prefix(self) -> None:
        """set_commented_out(True) prefixes output with '# '."""
        macro = GenCfgMacro("KEY", "val")
        macro.set_commented_out(True)

        result = macro.get()

        assert result.startswith("# ")

    def test_set_commented_out_false_removes_prefix(self) -> None:
        """set_commented_out(False) removes the comment prefix."""
        macro = GenCfgMacro("KEY", "val")
        macro.set_commented_out(True)
        macro.set_commented_out(False)

        result = macro.get()

        assert not result.startswith("# ")

    def test_colon_macro_appends_colon_to_name(self) -> None:
        """colon_macro=True appends a colon after the name."""
        macro = GenCfgMacro("LABEL", "", colon_macro=True)

        result = macro.get()

        assert "LABEL:" in result

    def test_str_equals_get(self) -> None:
        """__str__() produces the same output as get()."""
        macro = GenCfgMacro("X", "y")

        assert str(macro) == macro.get()

    def test_value_tab_position_pads_short_names(self) -> None:
        """Short names are padded to align the value at value_tab_pos."""
        macro = GenCfgMacro("AB", "val", value_tab_pos=12)

        result = macro.get()

        # 'AB' is 2 chars, tab_pos=12 → 10 spaces before value
        assert "AB" + " " * 10 + "val" == result
