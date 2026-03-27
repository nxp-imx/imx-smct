#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause

from smct.resources.resdb import ResourceDb
from smct.resources.resource_base import AtomicResource, MacroResource
from smct.resources.resource_database_provider import ResourceDatabaseProvider


def test_identity() -> None:
    instance = ResourceDatabaseProvider.get_database()
    assert isinstance(instance, ResourceDb)
    instance2 = ResourceDatabaseProvider.get_database()
    assert instance == instance2


def test_clear_configuration() -> None:
    ResourceDatabaseProvider.clear_database()
    db = ResourceDatabaseProvider.get_database()
    assert db.is_empty()
    atom_resource = AtomicResource({"name": "Ipsum", "type": "MRC"})
    macro_resource = MacroResource("Lorem")
    db.add_atomic_resource(atom_resource)
    assert db.is_empty()
    db.add_macro_resource(macro_resource)
    assert db.find_macro_resource("Lorem") is not None
    assert db.find_atomic_resource_by("name", "Ipsum") is not None
    assert not db.is_empty()
    db = ResourceDatabaseProvider.get_database()
    assert db.find_macro_resource("Lorem") is not None
    assert db.find_atomic_resource_by("name", "Ipsum") is not None
    assert not db.is_empty()
    ResourceDatabaseProvider.clear_database()
    db = ResourceDatabaseProvider.get_database()
    assert db.find_macro_resource("Lorem") is None
    assert len(db.find_atomic_resource_by("name", "Ipsum")) == 0
    assert db.is_empty()
