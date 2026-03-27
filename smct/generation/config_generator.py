#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause

"""Module for generation of content based on the configuration"""

from typing import List

from smct.configuration.confdata import ConfigurationData
from smct.generation.gen_bctrl import GeneratorBCTRL
from smct.generation.gen_board import GeneratorBoard
from smct.generation.gen_dev import GeneratorDev
from smct.generation.gen_dox import GeneratorDoxygen
from smct.generation.gen_fusa import GeneratorFusa
from smct.generation.gen_lmm import GeneratorLMM
from smct.generation.gen_mak import GeneratorMakeFile
from smct.generation.gen_mb_loopback import GeneratorMailboxLoopback
from smct.generation.gen_mb_mu import GeneratorMBMU
from smct.generation.gen_scmi import GeneratorSCMI
from smct.generation.gen_smt import GeneratorSMT
from smct.generation.gen_test import GeneratorTest
from smct.generation.gen_trdc import GeneratorTRDC
from smct.generation.gen_user import GeneratorUser
from smct.generation.generator import GeneratorBase


class ConfigGenerator:
    """Collection of generators which generate all needed configuration files"""

    def __init__(self, populate: bool = True) -> None:
        """Initialize the ConfigGenerator.

        Args:
            populate: Whether to populate the generators list with default generators.
        """
        self._gens: List[GeneratorBase] = []
        self._device: str | None = None
        self._board: str | None = None

        if populate:
            self._gens = [
                GeneratorSCMI(),
                GeneratorSMT(),
                GeneratorMBMU(),
                GeneratorMailboxLoopback(),
                GeneratorLMM(),
                GeneratorBCTRL(),
                GeneratorTRDC(),
                GeneratorDoxygen(),
                GeneratorMakeFile(),
                GeneratorDev(),
                GeneratorUser(),
                GeneratorBoard(),
                GeneratorTest(),
                GeneratorFusa(),
            ]

    def generate(self, conf: ConfigurationData, output_directory: str, force: bool = False) -> None:
        """Generates content of all generators to the given folder.

        Args:
            conf: Configuration data to use for generation.
            output_directory: Directory path where generated files will be written.
            force: Whether to force overwrite existing files.
        """
        for generator in self._gens:
            generator.generate(conf, output_directory, force=force)
