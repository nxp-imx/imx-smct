#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Unit tests for GenHeading, GenMacroValue, GenMacroPresence, and GenMacroList helpers."""

import io

from smct.generation.generator import (
    GenHeading,
    GenMacroList,
    GenMacroPresence,
    GenMacroValue,
)


class TestGenHeading:
    """Tests for GenHeading section comment helper."""

    def test_get_string_contains_comment_text(self) -> None:
        """Rendered output contains the heading comment."""
        gen = GenHeading("My Heading")
        gen.print_head()

        result = gen.get_string()

        assert "My Heading" in result

    def test_get_string_contains_separator_dashes(self) -> None:
        """Rendered output contains the separator border."""
        gen = GenHeading("Test")
        gen.print_head()

        result = gen.get_string()

        assert "/*" in result
        assert "*/" in result

    def test_custom_comment_chars_are_used(self) -> None:
        """Custom comment characters appear in the rendered output."""
        gen = GenHeading("Section", comment_chars=("#", "#"))
        gen.print_head()

        result = gen.get_string()

        assert "#" in result
        assert "Section" in result

    def test_print_writes_output_to_file(self) -> None:
        """print(file=...) populates the buffer and writes to the given file."""
        gen = GenHeading("Header")
        buf = io.StringIO()

        gen.print(file=buf)

        assert "Header" in buf.getvalue()


class TestGenMacroValue:
    """Tests for GenMacroValue C define with value helper."""

    def test_integer_value_formatted_with_u_suffix(self) -> None:
        """Integer values are rendered with a U suffix."""
        gen = GenMacroValue("MY_MACRO", 42)
        gen.print_members()

        assert "42U" in gen.get_members_string()

    def test_string_value_rendered_verbatim(self) -> None:
        """String values are rendered without modification."""
        gen = GenMacroValue("MY_MACRO", "some_string_val")
        gen.print_members()

        assert "some_string_val" in gen.get_members_string()

    def test_comment_appears_in_head(self) -> None:
        """A non-empty comment is emitted to the head section."""
        gen = GenMacroValue("M", 1, comment="A description")
        gen.print_head()

        assert "A description" in gen.get_head_string()

    def test_no_comment_produces_empty_head(self) -> None:
        """No comment means head section stays empty."""
        gen = GenMacroValue("M", 1)
        gen.print_head()

        assert gen.get_head_string() == ""

    def test_tail_adds_blank_line(self) -> None:
        """print_tail() appends a trailing newline."""
        gen = GenMacroValue("M", 1)
        gen.print_tail()

        assert gen.get_tail_string() == "\n"

    def test_define_name_in_members(self) -> None:
        """The define name appears in the rendered members."""
        gen = GenMacroValue("DEFINE_NAME", 0)
        gen.print_members()

        assert "DEFINE_NAME" in gen.get_members_string()


class TestGenMacroPresence:
    """Tests for GenMacroPresence bare C define helper."""

    def test_define_name_in_members(self) -> None:
        """The define name appears in the rendered members."""
        gen = GenMacroPresence("PRESENCE_MACRO")
        gen.print_members()

        assert "#define PRESENCE_MACRO" in gen.get_members_string()

    def test_comment_appears_in_head(self) -> None:
        """A non-empty comment is emitted to the head section."""
        gen = GenMacroPresence("M", comment="Presence comment")
        gen.print_head()

        assert "Presence comment" in gen.get_head_string()

    def test_no_comment_produces_empty_head(self) -> None:
        """No comment means head section stays empty."""
        gen = GenMacroPresence("M")
        gen.print_head()

        assert gen.get_head_string() == ""

    def test_tail_adds_blank_line(self) -> None:
        """print_tail() appends a trailing newline."""
        gen = GenMacroPresence("M")
        gen.print_tail()

        assert gen.get_tail_string() == "\n"

    def test_full_print_to_buffer(self) -> None:
        """Full print() cycle writes expected content."""
        gen = GenMacroPresence("FULL_MACRO", comment="desc")
        buf = io.StringIO()

        gen.print(file=buf)

        output = buf.getvalue()
        assert "FULL_MACRO" in output
        assert "desc" in output


class TestGenMacroList:
    """Tests for GenMacroList macro with list of items."""

    def test_add_value_appends_to_list(self) -> None:
        """add_value() adds items; len() reflects count."""
        gen = GenMacroList("MY_LIST")

        gen.add_value("item1")
        gen.add_value("item2")

        assert len(gen) == 2

    def test_add_value_keeps_duplicates(self) -> None:
        """Duplicate values are appended, not silently dropped."""
        gen = GenMacroList("MY_LIST")

        gen.add_value("dup")
        gen.add_value("dup")

        assert len(gen) == 2

    def test_set_values_replaces_list(self) -> None:
        """set_values() replaces the internal list."""
        gen = GenMacroList("LIST")
        gen.add_value("old")

        gen.set_values(["a", "b", "c"])

        assert len(gen) == 3

    def test_members_contain_all_values(self) -> None:
        """All added values appear in the rendered members section."""
        gen = GenMacroList("LIST")
        gen.add_value("VAL_A")
        gen.add_value("VAL_B")
        gen.print_members()

        result = gen.get_members_string()
        assert "VAL_A" in result
        assert "VAL_B" in result

    def test_empty_list_produces_empty_list_comment(self) -> None:
        """An empty list renders an '/* empty list */' comment."""
        gen = GenMacroList("EMPTY")
        gen.print_members()

        assert "empty list" in gen.get_members_string()

    def test_head_contains_define_name(self) -> None:
        """print_head() includes the macro name."""
        gen = GenMacroList("NAMED_LIST")
        gen.add_value("v")
        gen.print_head()

        assert "NAMED_LIST" in gen.get_head_string()

    def test_comment_in_head(self) -> None:
        """A comment is included in head output."""
        gen = GenMacroList("L", comment="List comment")
        gen.add_value("v")
        gen.print_head()

        assert "List comment" in gen.get_head_string()
