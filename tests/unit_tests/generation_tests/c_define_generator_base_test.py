#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Unit tests for smct.generation.c_define_generator_base.CDefineGeneratorBase."""

import io

import pytest

from smct.generation.c_define_generator_base import CDefineGeneratorBase


class _ConcreteGenerator(CDefineGeneratorBase):
    """Minimal concrete subclass that writes fixed content to all three sections."""

    def print_head(self) -> None:
        """Write a fixed head line."""
        self.add_to_head("HEAD_LINE")

    def print_members(self) -> None:
        """Write a fixed members line."""
        self.add_to_members("MEMBERS_LINE")

    def print_tail(self) -> None:
        """Write a fixed tail line."""
        self.add_to_tail("TAIL_LINE")


class TestCDefineGeneratorBase:
    """Tests for CDefineGeneratorBase buffer accumulation and rendering."""

    def test_add_to_head_accumulates_text(self) -> None:
        """add_to_head() appends text to the head buffer."""
        gen = CDefineGeneratorBase()

        gen.add_to_head("line1")
        gen.add_to_head("line2")

        result = gen.get_head_string()
        assert "line1" in result
        assert "line2" in result

    def test_add_to_members_accumulates_text(self) -> None:
        """add_to_members() appends text to the members buffer."""
        gen = CDefineGeneratorBase()

        gen.add_to_members("member1")
        gen.add_to_members("member2")

        result = gen.get_members_string()
        assert "member1" in result
        assert "member2" in result

    def test_add_to_tail_accumulates_text(self) -> None:
        """add_to_tail() appends text to the tail buffer."""
        gen = CDefineGeneratorBase()

        gen.add_to_tail("tail1")
        gen.add_to_tail("tail2")

        result = gen.get_tail_string()
        assert "tail1" in result
        assert "tail2" in result

    def test_get_head_string_empty_initially(self) -> None:
        """Head buffer is empty before any writes."""
        gen = CDefineGeneratorBase()

        assert gen.get_head_string() == ""

    def test_get_members_string_empty_initially(self) -> None:
        """Members buffer is empty before any writes."""
        gen = CDefineGeneratorBase()

        assert gen.get_members_string() == ""

    def test_get_tail_string_empty_initially(self) -> None:
        """Tail buffer is empty before any writes."""
        gen = CDefineGeneratorBase()

        assert gen.get_tail_string() == ""

    def test_add_to_head_custom_end_character(self) -> None:
        """add_to_head() respects a custom end character."""
        gen = CDefineGeneratorBase()

        gen.add_to_head("part", end="")

        assert gen.get_head_string() == "part"

    def test_add_to_members_custom_end_character(self) -> None:
        """add_to_members() respects a custom end character."""
        gen = CDefineGeneratorBase()

        gen.add_to_members("val", end=",\\\n")

        assert "val,\\\n" in gen.get_members_string()

    def test_get_string_concatenates_all_sections_in_order(self) -> None:
        """get_string() returns head + members + tail in that order."""
        gen = CDefineGeneratorBase()
        gen.add_to_head("HEAD")
        gen.add_to_members("BODY")
        gen.add_to_tail("TAIL")

        result = gen.get_string()

        head_pos = result.index("HEAD")
        body_pos = result.index("BODY")
        tail_pos = result.index("TAIL")
        assert head_pos < body_pos < tail_pos

    def test_print_calls_subclass_methods_and_writes_to_file(self) -> None:
        """print() triggers print_head/members/tail and writes combined output to the given IO."""
        gen = _ConcreteGenerator()
        buf = io.StringIO()

        gen.print(file=buf)

        output = buf.getvalue()
        assert "HEAD_LINE" in output
        assert "MEMBERS_LINE" in output
        assert "TAIL_LINE" in output

    def test_print_to_stdout_uses_sys_stdout_when_none(self, capsys: pytest.CaptureFixture[str]) -> None:
        """print(file=None) falls back to sys.stdout."""
        gen = _ConcreteGenerator()

        gen.print(file=None)

        captured = capsys.readouterr()
        assert "HEAD_LINE" in captured.out

    def test_print_output_order_is_head_then_members_then_tail(self) -> None:
        """print() produces head before members before tail in the output stream."""
        gen = _ConcreteGenerator()
        buf = io.StringIO()

        gen.print(file=buf)

        output = buf.getvalue()
        head_pos = output.index("HEAD_LINE")
        members_pos = output.index("MEMBERS_LINE")
        tail_pos = output.index("TAIL_LINE")
        assert head_pos < members_pos < tail_pos

    def test_base_print_head_is_no_op(self) -> None:
        """Base print_head() does not write anything to the head buffer."""
        gen = CDefineGeneratorBase()
        gen.print_head()

        assert gen.get_head_string() == ""

    def test_base_print_members_is_no_op(self) -> None:
        """Base print_members() does not write anything to the members buffer."""
        gen = CDefineGeneratorBase()
        gen.print_members()

        assert gen.get_members_string() == ""

    def test_base_print_tail_is_no_op(self) -> None:
        """Base print_tail() does not write anything to the tail buffer."""
        gen = CDefineGeneratorBase()
        gen.print_tail()

        assert gen.get_tail_string() == ""
