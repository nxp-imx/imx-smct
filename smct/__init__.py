#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""System Manager Configuration Tool (SMCT) initialization.

This module provides the main entry point and package metadata for SMCT.
"""

from smct._version import __version__

__title__: str = "smct"
__author__: str = "NXP Semiconductors"
__copyright__: str = "Copyright 2025-2026 NXP"
__license__: str = "BSD-3-Clause"
__url__: str = "https://github.com/nxp-imx/imx-smct/"
__description__: str = "System Manager Configuration Tool for NXP SM firmware"

__all__ = ["__version__", "__title__", "__author__", "__copyright__", "__license__", "__url__", "__description__"]
