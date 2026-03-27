#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause

from smct.model.chip_model_provider import ChipModelProvider
from smct.model.model_chip import ChipModelImx9


def test_identity() -> None:
    instance = ChipModelProvider.get_model()
    assert isinstance(instance, ChipModelImx9)
    instance2 = ChipModelProvider.get_model()
    assert instance == instance2


def test_clear_configuration() -> None:
    ChipModelProvider.clear_model()
    model = ChipModelProvider.get_model()
    model.add_mix("mix1")
    assert len(model.get_mixes()) == 1
    assert model.get_mixes()[0] == "mix1"
    model = ChipModelProvider.get_model()
    assert len(model.get_mixes()) == 1
    assert model.get_mixes()[0] == "mix1"
    ChipModelProvider.clear_model()
    model = ChipModelProvider.get_model()
    assert len(model.get_mixes()) == 0
