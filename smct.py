#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
import sys
import os

if __name__ == "__main__":
    if sys.version_info < (3, 10):
        print("Minimal required version of Python is 3.10", file=sys.stderr)
        exit(1)

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from smct import smct

"""Helper module that launches main function of the SMCT in src module"""

if __name__ == "__main__":
    smct.main()
