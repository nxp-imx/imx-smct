#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Module with all common utils and generic classes"""

import json
import logging
import os
import re
from typing import Any, Dict, List, Tuple, TypeVar

import fastjsonschema

_re_attr = re.compile(r'^([a-z0-9]+)=(("[^"]*?")|(\S*))')  # lowercase key=val or key="quoted val"

logger = logging.getLogger()

# atom is anything separated by comma or whitespace, but the separator must not be in quotes
REGEXP_PARSE_LINE_TO_ATOMS = re.compile(r"(((\".*?\")|([^, \r\n\t]))+)")


def convert_to_hex(number: int, digits: int = 8, upper_case: bool = True) -> str:
    """Returns number in hexadecimal format.

    Args:
        number: The integer number to convert.
        digits: Number of digits to pad with zeros.
        upper_case: Whether to use uppercase letters for hex digits.

    Returns:
        The hexadecimal representation of the number as a string.
    """
    h = hex(number)[2:].zfill(digits)
    return "0x" + (h.upper() if upper_case else h.lower())


def is_hex(s: str) -> bool:
    """Returns if number is hex.

    Args:
        s: The string to check.

    Returns:
        True if the string represents a hexadecimal number, False otherwise.
    """
    return re.fullmatch(r"^(0[xX])?[0-9a-fA-F]+$", s or "") is not None


def convert_enum_value(value: str | int) -> int:
    """Returns value for enum dictionary, converted to hex if possible otherwise unchanged.

    Args:
        value: The value to convert, either string or integer.

    Returns:
        The converted integer value.
    """
    return int(value, 16) if isinstance(value, str) and is_hex(value) else int(value)


def parse_int(text: str, allow_units: bool = False) -> int:
    """Parses integer out of the provided string. Units might be present if allowed.

    Args:
        text: The string to parse.
        allow_units: Whether to allow unit suffixes (K, M, G).

    Returns:
        The parsed integer value.
    """
    if len(text) > 2 and text[0:2].lower() == "0x":
        return int(text[2:], 16)
    mult = 1
    if allow_units and text[-1].isalpha():
        units = {"K": 1024, "k": 1024, "M": 1024 * 1024, "G": 1024 * 1024 * 1024}
        unit = text[-1]
        text = text[:-1]
        mult = units[unit]
    return int(text) * mult


class FormatedInt:
    """Class used for storing integer with its base for backwards conversion"""

    def __init__(self, formated_int: str | int) -> None:
        if isinstance(formated_int, str):
            if len(formated_int) > 2:
                base = formated_int[0:2].lower()
                if base == "0b":
                    value = int(formated_int[2:], 2)
                elif base == "0x":
                    value = int(formated_int[2:], 16)
                else:
                    value = parse_int(formated_int, allow_units=True)
                    base = ""
            else:
                value = parse_int(formated_int, allow_units=True)
                base = ""
        else:
            value = formated_int
            base = ""
        self.__base = base
        self.__value = value

    def __int__(self) -> int:
        return self.__value

    def __str__(self) -> str:
        if self.__base == "0x":
            return hex(self.__value)
        if self.__base == "0b":
            return bin(self.__value)
        return str(self.__value)

    def get_value(self) -> int:
        """Returns integer value of the formated integer.

        Returns:
            The integer value.
        """
        return self.__value

    def get_base(self) -> str:
        """Returns base of the formated integer.

        Returns:
            The base string ("0x", "0b", or empty string).
        """
        return self.__base


class FormatedIntEncoder(json.JSONEncoder):
    """For encoding FormatedInt class into JSON"""

    def default(self, o: Any) -> Any:
        if isinstance(o, FormatedInt):
            if o.get_base() == "0x":
                return hex(o.get_value())
            if o.get_base() == "0b":
                return bin(o.get_value())
            return o.get_value()
        return json.JSONEncoder.default(self, o)


def parse_int_or_default(text: str, default_value: int, allow_units: bool = False) -> int:
    """Parses integer out of the provided string. Returns default value if parsing is not possible.
     Units might be present if allowed.

     Args:
        text: The string to parse.
        default_value: The value to return if parsing fails.
        allow_units: Whether to allow unit suffixes (K, M, G).

    Returns:
        The parsed integer value or the default value if parsing fails.
    """
    try:
        if len(text) > 2 and text[0:2].lower() == "0x":
            return int(text[2:], 16)
        mult = 1
        if allow_units and text[-1].isalpha():
            units = {"K": 1024, "k": 1024, "M": 1024 * 1024, "G": 1024 * 1024 * 1024}
            unit = text[-1]
            text = text[:-1]
            mult = units[unit]
        return int(text) * mult
    except (ValueError, KeyError):
        return default_value


def is_numeric_literal(value: Any) -> bool:
    """Check if value is a numeric literal (int or string ending with C numeric suffixes).

    Args:
        value: The value to check

    Returns:
        bool: True if value is an int or string ending with numeric suffix where prefix is parsable as int
    """
    if isinstance(value, int):
        return True

    value_str = str(value)
    for suffix in ["ULL", "LL", "UL", "L", "U"]:  # Check longer suffixes first
        if value_str.endswith(suffix):
            prefix = value_str[: -len(suffix)]
            try:
                int(prefix, 0)  # Support hex (0x), octal (0o), binary (0b), and decimal
                return True
            except ValueError:
                continue
    # Check if it's a hexadecimal or binary string without suffix
    if value_str.lower().startswith(("0x", "0b")):
        try:
            int(value_str, 0)
            return True
        except ValueError:
            pass
    return False


def parse_int_or_return_str(value: Any) -> int | str:
    """Parses integer out of the provided value. Returns the original value as string if parsing is not possible.

    Args:
        value: The value to parse.

    Returns:
        The parsed integer value or the original value as string if parsing fails.
    """
    parsed: int | str
    try:
        parsed = int(value)
    except (TypeError, ValueError):  # TypeError when None, ValueError when non numeric string

        parsed = str(value)
    return parsed


def parse_int_range(text: str, allow_single: bool = True, allow_units: bool = False) -> Tuple[int, int]:
    """Parses integer range from the input. Units might be present if allowed. If single integer is present and
    allowed then the resulting tuple contains the same value.

    Args:
        text: The string containing the range (e.g., "1-10" or "5").
        allow_single: Whether to allow single integers instead of ranges.
        allow_units: Whether to allow unit suffixes (K, M, G).

    Returns:
        A tuple containing the start and end values of the range.
    """
    parts = text.split("-")
    if len(parts) == 1:
        if allow_single:
            val = parse_int(text, allow_units=allow_units)
            return val, val
        raise ValueError()
    if len(parts) == 2:
        val1 = parse_int(parts[0], allow_units=allow_units)
        val2 = parse_int(parts[1], allow_units=allow_units)
        return val1, val2
    raise ValueError()


def parse_line_to_atoms(line: str) -> List[str]:
    """Parses the line by regexp into list of atoms.

    Args:
        line: The line to parse.

    Returns:
        A list of parsed atoms from the line.
    """
    atoms = REGEXP_PARSE_LINE_TO_ATOMS.findall(line)
    return [a[0] for a in atoms]


def contains_attribute_in_list(atoms: List[str], key: str, no_value: bool = False, remove: bool = False) -> bool:
    """Helper to find key=value from list of atoms. Return assignment value if found.

    Args:
        atoms: List of atom strings to search in.
        key: The key to search for.
        no_value: Whether to search for key without value.
        remove: Whether to remove the found atom from the list.

    Returns:
        True if the key is found, False otherwise.
    """
    if no_value:
        if key in atoms:
            if remove:
                atoms.remove(key)
            return True
        return False
    for atom in atoms:
        match = _re_attr.match(atom)
        if match and match.group(1) == key:
            if remove:
                atoms.remove(atom)
            return True
    return False


def get_attribute_value_from_list(atoms: List[str], key: str, remove: bool = False) -> str | None:
    """Helper to find key=value from list of atoms. Return assignment value if found.

    Args:
        atoms: List of atom strings to search in.
        key: The key to search for.
        remove: Whether to remove the found atom from the list.

    Returns:
        The value associated with the key, or None if not found.
    """
    result = None
    for atom in atoms:
        match = _re_attr.match(atom)
        if match and match.group(1) == key:
            value = match.group(2).strip().strip('"')
            if remove:
                atoms.remove(atom)
            if result is not None and result != value:
                logger.error(
                    "There are multiple atoms with name '%s' and they have different values '%s' and '%s'. The first value will be used.",
                    key,
                    result,
                    value,
                    extra={"source": key},
                )
                return result
            result = value
    return result


def get_variable_from_list(atoms: List[str], remove: bool = False) -> str | None:
    """Helper to find var=value from list of atoms. Return assignment value if found.

    Args:
        atoms: List of atom strings to search in.
        remove: Whether to remove the found atom from the list.

    Returns:
        The value of the var attribute, or None if not found.
    """
    for atom in atoms:
        match = _re_attr.match(atom)
        if match and match.group(1) == "var":
            value = match.group(2).strip().strip('"')
            if remove:
                atoms.remove(atom)
            return value
    return None


def set_at_index(list_to_change: List[Any], index: int, value: Any) -> None:
    """Sets a value in list at specific index, growing the list with None values if necessary.

    Args:
        list_to_change: The list to modify.
        index: The index at which to set the value.
        value: The value to set.
    """
    while len(list_to_change) <= index:
        list_to_change.append(None)
    list_to_change[index] = value


def safe_string(input_string: str | None) -> str:
    """Returns input string if it is not None, otherwise returns empty string.

    Args:
        input_string: The input string to check.

    Returns:
        The input string or empty string if input is None.
    """
    if input_string is None:
        return ""
    return input_string


def get_bool(obj: Any) -> bool:
    """Returns True if given object is True or string 'True' or 'true' and returns False in other cases.

    Args:
        obj: The object to evaluate as boolean.

    Returns:
        True if the object represents a true value, False otherwise.
    """
    if isinstance(obj, bool):
        return bool(obj)
    if isinstance(obj, str):
        string = str(obj).lower().strip()
        return string == "true"
    return False


REGEXP_PARSE_FLOAT_WITH_UNITS = re.compile(r"^(\d+(?:\.\d+)?)\s*([a-zA-Z]+)?$")

TIME_MS_UNIT_MULTIPLIERS = {
    None: 1,
    "ms": 1,
    "s": 1000,
    "sec": 1000,
    "min": 60 * 1000,
    "hr": 60 * 60 * 1000,
    "hour": 60 * 60 * 1000,
    "hrs": 60 * 60 * 1000,
    "hours": 60 * 60 * 1000,
    "day": 24 * 60 * 60 * 1000,
    "days": 24 * 60 * 60 * 1000,
}


def parse_time_to_ms(period: str, throw: bool = False) -> int | None:
    """Converts time period string to milliseconds. String can have units in ms, sec, min, hours, or days.

    Args:
        period: Time period string

    Returns:
        Time in milliseconds otherwise None for mis-formatted inputs
    """
    match = REGEXP_PARSE_FLOAT_WITH_UNITS.match(period)
    time_ms = None

    if match:
        try:
            units = match.group(2)
            multiplier = 1
            if units:
                if units in TIME_MS_UNIT_MULTIPLIERS:
                    multiplier = TIME_MS_UNIT_MULTIPLIERS[units]
                else:
                    raise ValueError(f"Invalid time unit: {units}")
            time_ms = int(float(match.group(1)) * multiplier + 0.5)
        except (NameError, TypeError, ValueError) as e:
            time_ms = None
            if throw:
                raise e

    return time_ms


def are_all_numbers_present(input_list: List[int]) -> bool:
    """Returns True if all numbers from minimum to maximum (inferred from the list) are present and there is no gap,
     False otherwise.

    Args:
        input_list: List of integers to check.

    Returns:
        True if all numbers in the range are present, False otherwise.
    """
    start = min(input_list)
    stop = max(input_list)
    for x in range(start, stop - start):
        if x not in input_list:
            return False
    return True


def make_enum_int_dictionary(enum_types: List) -> Dict[str, int]:
    """Return dictionary of types from resources JSON.

    Args:
        enum_types: List of enum type definitions.

    Returns:
        Dictionary mapping enum IDs to integer values.
    """
    return dict(map(lambda enum_type: (enum_type["id"], convert_enum_value(enum_type["value"])), enum_types))


def make_enum_str_dictionary(enum_types: List) -> Dict[str, str]:
    """Return dictionary of types from resources JSON.

    Args:
        enum_types: List of enum type definitions.

    Returns:
        Dictionary mapping enum IDs to string values.
    """
    return dict(map(lambda enum_type: (enum_type["id"], enum_type["value"]), enum_types))


def are_numbers_consecutive(input_list: List[int]) -> bool:
    """Returns whether all numbers in the list are consecutive (sequence of numbers is incrementing by 1).

    Args:
        input_list: List of integers to check.

    Returns:
        True if all numbers are consecutive, False otherwise.
    """
    if len(input_list) <= 1:
        return True
    return all(num2 - num1 == 1 for num1, num2 in zip(input_list[:-1], input_list[1:]))


def find_firmware_root_dir(root_dir: str) -> str | None:
    """Returns found System Manager firmware root directory or None if SM FW directory was not found.

    Args:
        root_dir: The root directory to search in.

    Returns:
        Path to the firmware root directory, or None if not found.
    """
    default_dir = os.path.join(root_dir, "imx-sm")
    # first search for default folder name of the SM firmware
    if os.path.exists(default_dir) and os.path.exists(os.path.join(default_dir, "sm")):
        return default_dir

    # try to find in different directories
    for file in os.listdir(root_dir):
        path_to_check = os.path.join(root_dir, file)
        if os.path.isdir(path_to_check) and os.path.exists(os.path.join(path_to_check, "sm")):
            return path_to_check
    return None


def get_all_files_in_folder(folder: str) -> List[str]:
    """Returns all files in given folder and all subfolders. Files in subfolders have the subfolder prefix.

    Args:
        folder: The folder path to scan.

    Returns:
        List of file paths relative to the input folder.
    """
    result = []
    scan_result = os.scandir(folder)
    for entry in scan_result:
        if entry.is_file():
            result.append(entry.name)
        elif entry.is_dir():
            recurse = get_all_files_in_folder(os.path.join(folder, entry.name))
            for f in recurse:
                result.append(os.path.join(entry.name, f))
    return result


K = TypeVar("K")
V = TypeVar("V")


class DictOrdered(Dict[K, V]):
    """Ordered dictionary - Keys are stored in order they were added."""

    def __init__(self) -> None:
        super().__init__()
        self._keys: List[Any] = []

    def __setitem__(self, key: Any, value: Any) -> None:
        if key not in self._keys:
            self._keys.append(key)
        return super().__setitem__(key, value)

    def ordered_keys(self) -> List[Any]:
        """Returns list of the keys in order of their addition to this dictionary.

        Returns:
            List of keys in insertion order.
        """
        return self._keys

    def sort_keys(self) -> None:
        """Sorts the keys by alphabetical order."""
        s = sorted(self._keys).copy()
        self._keys = s


def validate_json(json_object: dict, json_path: str, schema_file: str, level: str) -> None:
    """Returns list of the keys in order of their addition to this dictionary"""
    schema_dir = os.path.join(os.path.dirname(__file__), "validation", "schemas")
    schema_path = os.path.join(schema_dir, schema_file)
    if not os.path.exists(schema_path):
        logger.warning("Schema file not found: %s", schema_path, extra={"source": schema_path})
        return
    with open(schema_path, "r", encoding="utf-8") as schema:
        schema = json.load(schema)
    try:
        fastjsonschema.validate(schema, json_object)
    except fastjsonschema.JsonSchemaValueException as e:
        message = f"""Failed validation of JSON file: {json_path}
                        On instance:
                            {e.value}
                        Reason:
                            {e.message}"""
        if level == "warning":
            logger.warning(message)
        if level == "critical":
            logger.critical(message)
        for handler in logger.handlers:
            handler.close()


class DataTypeConstraints:
    """Class for storing max values and default values of certain data types as read-only properties."""

    MAX_VALUE: int
    DEFAULT_VALUE: int

    def __init_subclass__(cls) -> None:
        """Validate that subclasses define required class attributes."""
        if not hasattr(cls, "MAX_VALUE"):
            raise AttributeError(f"{cls.__name__} must define MAX_VALUE")
        if not hasattr(cls, "DEFAULT_VALUE"):
            raise AttributeError(f"{cls.__name__} must define DEFAULT_VALUE")

    @property
    def max_value(self) -> int:
        """Returns the maximum value (read-only).

        Returns:
            The maximum allowed value.
        """
        return self.MAX_VALUE

    @property
    def default_value(self) -> int:
        """Returns the default value (read-only).

        Returns:
            The default value.
        """
        return self.DEFAULT_VALUE


class UInt32Constraints(DataTypeConstraints):
    """Class used to store maximal value of uint32 data type for
    validation and default value if the max value is exceeded."""

    MAX_VALUE = 0xFFFFFFFF
    DEFAULT_VALUE = 0xFFFFFFFF


class UInt64Constraints(DataTypeConstraints):
    """Class used to store maximal value of uint64 data type for
    validation and default value if the max value is exceeded."""

    MAX_VALUE = 0xFFFFFFFFFFFFFFFF
    DEFAULT_VALUE = 0xFFFFFFFFFFFFFFFF
