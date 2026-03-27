#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Helper module that launches main function of the SMCT development"""
import sys
import os

if __name__ == "__main__":
    if sys.version_info < (3, 10):
        print("Minimal required version of Python is 3.10", file=sys.stderr)
        sys.exit(1)

    sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

    from smct import smct
    sys.exit(smct.main())
