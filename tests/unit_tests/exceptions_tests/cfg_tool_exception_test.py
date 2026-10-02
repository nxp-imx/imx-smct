#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Unit tests for smct.exceptions.cfg_tool_exception.CfgToolException."""

import pytest

from smct.exceptions.cfg_tool_exception import CfgToolException


class TestCfgToolException:
    """Tests for the CfgToolException base exception class."""

    def test_non_empty_message_is_prefixed(self) -> None:
        """Verify a non-empty message is prefixed with 'SM CfgTool: '."""
        exc = CfgToolException("boom")

        assert str(exc) == "SM CfgTool: boom"

    def test_empty_message_uses_default(self) -> None:
        """Verify an empty message defaults to 'Unknown Exception' before prefixing."""
        exc = CfgToolException("")

        assert str(exc) == "SM CfgTool: Unknown Exception"

    def test_is_instance_of_exception(self) -> None:
        """Verify CfgToolException is a subclass of the built-in Exception."""
        assert isinstance(CfgToolException("x"), Exception)

    def test_raise_contains_prefixed_message(self) -> None:
        """Verify the raised exception carries the full prefixed message."""
        with pytest.raises(CfgToolException) as excinfo:
            raise CfgToolException("oops")

        assert "SM CfgTool: oops" in str(excinfo.value)
