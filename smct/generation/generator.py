#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025-2026 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Module with base generator implementation"""

import logging
import os.path
import typing
from datetime import datetime
from typing import Any, Dict, IO, List, Optional, Tuple

from smct import utils
from smct.configuration.confdata import ConfigurationData
from smct.exceptions.cfg_tool_exception import CfgToolException
from smct.generation.c_define_generator_base import CDefineGeneratorBase
from smct.utils import DictOrdered

logger = logging.getLogger()

COPYRIGHT_YEAR = datetime.now().year


class GeneratorBase:
    """Base class for different configuration header file generators"""

    def __init__(self) -> None:
        self._conf: ConfigurationData | None = None
        self._open_file: IO | None = None

    def _print(self, text: str, end: str = "\n") -> None:
        file = self.get_open_file()
        if file is None:
            logger.error("Cannot print text '%s' because file is not open", text, extra={"source": "general"})
        print(text, end=end, file=file)

    def print_generator(self, generator: CDefineGeneratorBase) -> None:
        """Writes the content of the generator into the open file.

        Args:
            generator: The generator whose content should be written to the file.
        """
        file = self.get_open_file()
        if file is None:
            logger.error("Cannot print content of generator '%s' because file is not open", generator, extra={"source": "general"})
        generator.print(file=file)

    def _get_generator_info(self) -> Dict[str, Any]:
        """Returns generator info.

        Returns:
            Dictionary containing generator information.
        """
        raise CfgToolException("Each generator must override this function")

    def _get_generator_name(self) -> str:
        """Get the generator name such as DEV, LMM, SCMI, ... This name is used to generate filename, protection
        macro etc.

        Returns:
            The generator name string.
        """
        info = self._get_generator_info()
        return info["name"]

    def _get_generator_includes(self) -> List[str]:
        """Returns list of includes.

        Returns:
            List of include file names.
        """
        info = self._get_generator_info()
        return info["incl"] if "incl" in info else []

    def _should_defines_comment_be_generated(self) -> bool:
        """Returns True when comment before defines should be generated.

        Returns:
            True if defines comment should be generated, False otherwise.
        """
        return True

    def _should_doxygen_be_generated(self) -> bool:
        """Returns True in case doxygen header should be generated, False otherwise.

        Returns:
            True if doxygen header should be generated, False otherwise.
        """
        return True

    def _get_output_file_name(self) -> str:
        """Returns the output file name.

        Returns:
            The output file name string.
        """
        return f"config_{self._get_generator_name().lower()}.h"

    def _get_header_protection_macro(self) -> str | None:
        """Returns the header protection macro name or None in case the protection is not needed.

        Returns:
            The header protection macro name or None if not needed.
        """
        return f"CONFIG_{self._get_generator_name().upper()}_H"

    def _get_copyright_comment_beginning(self) -> str:
        """Returns the copyright comment beginning.

        Returns:
            The copyright comment beginning string.
        """
        return "/*"

    def _get_copyright_comment_prefix(self) -> str:
        """Returns the copyright comment line prefix.

        Returns:
            The copyright comment line prefix string.
        """
        return "**"

    def _get_copyright_comment_ending(self) -> str:
        """Returns the copyright comment ending.

        Returns:
            The copyright comment ending string.
        """
        return "*/"

    def _print_copyright_comment_line(self, comment: str) -> None:
        """Prints copyright comment line.

        Args:
            comment: The comment text to print.
        """
        spacing = " " if len(comment) > 1 else ""
        self._print(f"{self._get_copyright_comment_prefix()}{spacing}{comment}")

    def _print_copyright(self) -> None:
        """Prints the copyright section of the file."""
        if len(self._get_copyright_comment_beginning()) > 1:
            self._print(self._get_copyright_comment_beginning())
        self._print_copyright_comment_line("###################################################################")
        self._print_copyright_comment_line("")
        self._print_copyright_comment_line(f"Copyright {COPYRIGHT_YEAR} NXP")
        self._print_copyright_comment_line("")
        self._print_copyright_comment_line("Redistribution and use in source and binary forms, with or without modification,")
        self._print_copyright_comment_line("are permitted provided that the following conditions are met:")
        self._print_copyright_comment_line("")
        self._print_copyright_comment_line("o Redistributions of source code must retain the above copyright notice, this list")
        self._print_copyright_comment_line("  of conditions and the following disclaimer.")
        self._print_copyright_comment_line("")
        self._print_copyright_comment_line("o Redistributions in binary form must reproduce the above copyright notice, this")
        self._print_copyright_comment_line("  list of conditions and the following disclaimer in the documentation and/or")
        self._print_copyright_comment_line("  other materials provided with the distribution.")
        self._print_copyright_comment_line("")
        self._print_copyright_comment_line("o Neither the name of the copyright holder nor the names of its")
        self._print_copyright_comment_line("  contributors may be used to endorse or promote products derived from this")
        self._print_copyright_comment_line("  software without specific prior written permission.")
        self._print_copyright_comment_line("")
        self._print_copyright_comment_line('THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND')
        self._print_copyright_comment_line("ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED")
        self._print_copyright_comment_line("WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE")
        self._print_copyright_comment_line("DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR")
        self._print_copyright_comment_line("ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES")
        self._print_copyright_comment_line("(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;")
        self._print_copyright_comment_line("LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON")
        self._print_copyright_comment_line("ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT")
        self._print_copyright_comment_line("(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS")
        self._print_copyright_comment_line("SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.")
        self._print_copyright_comment_line("")
        self._print_copyright_comment_line("")
        self._print_copyright_comment_line("###################################################################")
        if len(self._get_copyright_comment_ending()) > 1:
            self._print(self._get_copyright_comment_ending())

    def _get_doxygen_group_name(self) -> str:
        return f"CONFIG_{self._get_configuration().get_doxygen_name().upper().replace(' ', '_')}"

    def _get_doxygen_file_name(self) -> str:
        return self._get_output_file_name()

    def _get_doxygen_brief_lines(self) -> List[str]:
        doxygen_desc = self._get_configuration().get_doxygen_description()
        result = [
            f" The {self._get_generator_name().upper()} configuration file for '{doxygen_desc}'",
            f"  - Config: '{self._get_configuration().get_doxygen_name()}'",
            f"  - Device: '{self._get_configuration().get_device_name()}'",
            f"  - Board: '{self._get_configuration().get_board_name()}'",
        ]
        return result

    def _get_doxygen_brief(self) -> str:
        lines = self._get_doxygen_brief_lines()
        if len(lines) == 0:
            return ""
        result = lines[0] + "\n"
        prefix = " *"
        for line in lines[1:-1]:
            result += f"{prefix}{line}\n"
        result += f"{prefix}{lines[-1]}"
        return result

    def _print_header(self) -> None:
        """Prints the header of the generated file."""
        self._print_copyright()
        # print("")
        if self._should_doxygen_be_generated():
            self._print("")
            self._print("/*==========================================================================*/")
            self._print("/*!")
            self._print(f" * @addtogroup {self._get_doxygen_group_name()}")
            self._print(" * @{")
            self._print(" *")
            file_name = self._get_doxygen_file_name()
            spacing = " " if len(file_name) > 0 else ""
            self._print(f" * @file{spacing}{file_name}")
            self._print(f" * @brief{self._get_doxygen_brief()}")
            self._print(" */")
            self._print("/*==========================================================================*/")
            self._print("")
        header_protection_macro = self._get_header_protection_macro()
        if header_protection_macro is not None:
            self._print(f"#ifndef {header_protection_macro}")
            self._print(f"#define {header_protection_macro}")
            self._print("")

        incl = self._get_generator_includes()
        if len(incl) > 0:
            self._print("/* Includes */")
            self._print("")
            for i in incl:
                self._print(f'#include "{i}"')

        self._print("")
        if self._should_defines_comment_be_generated():
            self._print("/* Defines */")
            self._print("")

    def print_content(self) -> None:
        """This is the main generator function, needs to be overridden."""
        self._print("#error No content generated")

    def print_footer(self) -> None:
        """Generates footer section of this generator."""
        header_protection_macro = self._get_header_protection_macro()
        if header_protection_macro is not None:
            self._print(f"#endif /* {self._get_header_protection_macro()} */")
        if self._should_doxygen_be_generated():
            self._print("")
            self._print("/** @} */")
            self._print("")

    def can_file_open(self, _: str, __: bool) -> bool:
        """Returns True if the file can be opened, False if not.

        Args:
            _: File path (unused).
            __: Force flag (unused).

        Returns:
            True if file can be opened, False otherwise.
        """
        return True

    @classmethod
    def _test_file_opening(cls, path: str, force: bool) -> None:
        """Tests whether the file can be opened or not.

        Args:
            path: Path to the file to test.
            force: Whether to force opening even if file exists.
        """
        if os.path.exists(path) and not force:
            raise FileExistsError(f"File {path} already exists, use --force option to override.")

    def generate(self, conf: ConfigurationData, output_directory: str, file_name: Optional[str | None] = None, force: bool = False) -> None:
        """Wrapper for running the generator in inherited class.

        Args:
            conf: Configuration data to use for generation.
            output_directory: Directory where to generate the output file.
            file_name: Optional custom file name, uses default if None.
            force: Whether to force generation even if file exists.
        """
        if not os.path.isdir(output_directory):
            if not force:
                raise CfgToolException(f"Output directory '{output_directory}' does not exist")
            os.mkdir(output_directory)
            if not os.path.isdir(output_directory):
                raise CfgToolException(f"Cannot create output directory '{output_directory}'")

        if not file_name:
            file_name = self._get_output_file_name()
        output_path = os.path.join(output_directory, file_name)

        try:
            self._conf = conf
            if not self.can_file_open(output_path, force):
                # Skip generation of file that cannot be open
                return
            self._test_file_opening(output_path, force)
            with open(output_path, "w", encoding="utf-8") as file:
                self._open_file = file
                self._print_header()
                self.print_content()
                self.print_footer()
        finally:
            self._open_file = None
            self._conf = None

    def _get_configuration(self) -> ConfigurationData:
        """Returns configuration of this generator. Raises exception when the configuration was not set.

        Returns:
            The configuration data for this generator.
        """
        conf = self._conf
        if conf is None:
            raise CfgToolException("No configuration was set to this generator")
        return conf

    def get_open_file(self) -> IO | None:
        """Returns the currently opened file or None if no file is open.

        Returns:
            The currently opened file or None if no file is open.
        """
        return self._open_file


class GenHeading(CDefineGeneratorBase):
    """Helper class as section heading in the generated file, typically used by generators"""

    def __init__(self, comment: str, comment_chars: Tuple[str, str] = ("/*", "*/")) -> None:
        super().__init__()
        self._comment = comment
        self._left = comment_chars[0]
        self._right = comment_chars[1]

    def print_head(self) -> None:
        """Prints the heading section with formatted comment borders"""
        comment_start = f"{self._left}{'-' * 74}{self._right}"
        self.add_to_head("")
        self.add_to_head(comment_start)
        padded_comment = str.ljust(f"{self._left} {self._comment}", len(comment_start) - len(self._right), " ")
        self.add_to_head(padded_comment + self._right)
        self.add_to_head(comment_start)
        self.add_to_head("")


class GenMacroValue(CDefineGeneratorBase):
    """Helper class as C define with value, typically used by generators"""

    def __init__(self, define: str, value: Any, comment: str = "") -> None:
        super().__init__()
        self._define: str = define  # name of macro
        self._value: Any = value  # macro value
        self._comment: str = comment  # heading comment

    def print_head(self) -> None:
        if self._comment:
            self.add_to_head(f"/*! {self._comment} */")

    def print_members(self) -> None:
        v = self._value
        if isinstance(v, int):
            v = f"{v}U"
        self.add_to_members(f"#define {self._define}  {v}")

    def print_tail(self) -> None:
        self.add_to_tail("")


class GenMacroPresence(CDefineGeneratorBase):
    """Helper class as C define without value, typically used by generators"""

    def __init__(self, define: str, comment: str = "") -> None:
        super().__init__()
        self._define: str = define  # name of macro
        self._comment: str = comment  # heading comment

    def print_head(self) -> None:
        if self._comment:
            self.add_to_head(f"/*! {self._comment} */")

    def print_members(self) -> None:
        self.add_to_members(f"#define {self._define}")

    def print_tail(self) -> None:
        self.add_to_tail("")


class GenMacroList(CDefineGeneratorBase):
    """Helper class for macro initializer with value as list of items, each put to a separate line"""

    def __init__(self, define: str, comment: str | None = None, suffix: str = "") -> None:
        super().__init__()
        self._define: str | None = define  # name of macro
        self._comment: str | None = comment  # heading comment
        self._values: List[str] = []  # values in the macro
        self._suffix = suffix  # suffix after each value
        self._indent: int = 4  # indentation step, default 4

    def add_value(self, value: Any) -> None:
        """Adds value that will be generated.

        Args:
            value: The value to add to the macro list.
        """
        self._values.append(value)

    def print_head(self) -> None:
        """Generates the comment and define name."""
        if self._comment:
            self.add_to_head(f"/*! {self._comment} */")

        end = " \\\n" if len(self._values) > 0 else "\n"
        self.add_to_head(f"#define {self._define}", end=end)

    def print_members(self) -> None:
        """Generates the members in this define."""
        indent = " " * self._indent

        if len(self._values) > 0:
            for v in self._values[:-1]:
                self.add_to_members(f"{indent}{v}", end=", \\\n")
            self.add_to_members(f"{indent}{self._values[-1]}{self._suffix}")
        else:
            self.add_to_members(f"{indent}/* empty list */")

    def print_tail(self) -> None:
        """Generates the tail after all defines."""
        self.add_to_tail("")

    def __len__(self) -> int:
        return len(self._values)


class GenStructInit(DictOrdered, CDefineGeneratorBase):
    """Helper class as structure initializer, typically used by generators"""

    def __init__(self, define: str | None, comment: str | None = None) -> None:
        DictOrdered.__init__(self)
        CDefineGeneratorBase.__init__(self)
        self._define: str | None = define  # name of the initializer macro
        self._comment: str | None = comment  # heading comment
        self._indent: int = 4  # indentation step, default 4
        self._sort: bool = False  # flag whether the members should be sorted during generation

    def set_sorting(self, sort: bool = True) -> None:
        """Sets flag whether the elements should be sorted before generation.

        Args:
            sort: Whether to sort elements before generation.
        """
        self._sort = sort

    def print_head(self) -> None:
        """Generates comment and define name."""
        if self._comment:
            self.add_to_head(f"/*! {self._comment} */")

        end = " \\\n"
        indent = " " * self._indent
        self.add_to_head(f"#define {self._define}", end=end)
        self.add_to_head(f"{indent}{{", end=end)

    def print_members(self) -> None:
        """Generates structure members values into the C define."""
        end = ", \\\n"
        indent = " " * (2 * self._indent)
        keys = sorted(self.keys()) if self._sort else self.ordered_keys()

        # Backward compatibility: Assigns using dictionary
        for k in keys:
            v = self[k]
            if isinstance(v, bool):
                v = f"{1 if v else 0}U"
            elif isinstance(v, int):
                v = f"{v}U"
            self.add_to_members(f"{indent}.{k} = {v}", end=end)

    def print_tail(self) -> None:
        """Generates the tail section after define was generated."""
        indent = " " * self._indent
        self.add_to_tail(f"{indent}}}")
        self.add_to_tail("")

    def get_define(self) -> str | None:
        """Returns define name.

        Returns:
            The define name or None if not set.
        """
        return self._define


class GenStructInitInline(GenStructInit):
    """Helper class as structure initializer, typically used by generators"""

    def __init__(self, define: str | None, comment: str | None = None) -> None:
        super().__init__(define, comment)
        self._entries: List[Tuple[str, Any]] = []  # list of entries to the structure

    def add_entry(self, name: str, value: Any) -> None:
        """Adds new entry to the generator.

        Args:
            name: The name of the structure member.
            value: The value to assign to the member.
        """
        self._entries.append((name, value))

    def add_break_line(self) -> None:
        """Adds break line entry to the generator."""
        self._entries.append(("\\", None))

    def print_members(self) -> None:
        """Generates structure members values into the C define."""
        formatted_members = []

        if len(self._entries) > 0:
            member_prefix = ""
            for entry in self._entries:
                name, value = entry
                if isinstance(value, bool):
                    value = f"{1 if value else 0}U"
                elif isinstance(value, int):
                    value = f"{value}U"
                if name == "\\":
                    member_prefix = "\\\n" + (" " * (self._indent + 1))
                else:
                    formatted_members.append(f"{member_prefix}.{name} = {value}")
                    member_prefix = ""
            self.add_to_members(", ".join(formatted_members), end="")


class GenDcdInit(CDefineGeneratorBase):
    """Helper class as DCD initializer, typically used by generators"""

    def __init__(self, define: str, comment: str | None = None) -> None:
        super().__init__()
        self._define: str = define  # name of the initializer macro
        self._comment: str | None = comment  # heading comment
        self._indent: int = 4  # indentation step, default 4
        self._sort: bool = True  # flag whether the keys should be sorted
        self._dcd: DictOrdered[Any, int] = DictOrdered()
        self._key_name_to_offset: Dict[str, int] = {}
        self._key_offset_to_name: Dict[int, str] = {}
        self._key_comments: Dict[Any, List[str]] = {}
        self._generate_upper_case_offset: bool = False
        self._generate_upper_case_value: bool = True
        self._value_alignments_for_address: Dict[int, int] = {}

    def __setitem__(self, key: Any, value: Any) -> None:
        if isinstance(key, str):
            key = self._key_name_to_offset[key]  # string name should have been translated to offset
        if isinstance(value, tuple):
            self.add_key_comment(key, value[1])
            value = value[0]
        self._dcd[key] = value

    def __getitem__(self, key: Any) -> Any:
        if isinstance(key, str):
            key = self._key_name_to_offset[key]
        return self._dcd[key]

    def __contains__(self, key: Any) -> bool:
        if isinstance(key, str):
            return key in self._key_name_to_offset
        return key in self._dcd

    def _get_key_name_2_offset(self) -> Dict[str, int]:
        """Returns name to offset dictionary.

        Returns:
            Dictionary mapping key names to offsets.
        """
        return self._key_name_to_offset

    def _get_key_offset_2_name(self) -> Dict[int, str]:
        """Returns offset to name dictionary.

        Returns:
            Dictionary mapping offsets to key names.
        """
        return self._key_offset_to_name

    def _get_key_comments(self) -> Dict[Any, List[str]]:
        """Returns key comments dictionary.

        Returns:
            Dictionary mapping keys to their comment lists.
        """
        return self._key_comments

    def _get_dcd(self) -> DictOrdered[Any, int]:
        """Returns dcd.

        Returns:
            The DCD ordered dictionary.
        """
        return self._dcd

    def _get_sort(self) -> bool:
        """Returns whether the keys should be sorted.

        Returns:
            True if keys should be sorted, False otherwise.
        """
        return self._sort

    def set_sort(self, sort: bool) -> None:
        """Sets whether the keys should be sorted.

        Args:
            sort: Whether to sort the keys.
        """
        self._sort = sort

    def set_upper_case_for_offset(self, upper_case: bool) -> None:
        """Sets flag whether the offset should be formatted in upper case letters.

        Args:
            upper_case: Whether to format offset in upper case.
        """
        self._generate_upper_case_offset = upper_case

    def set_upper_case_for_value(self, upper_case: bool) -> None:
        """Sets flag whether the value should be formatted in upper case letters.

        Args:
            upper_case: Whether to format value in upper case.
        """
        self._generate_upper_case_value = upper_case

    def set_value_alignment_for_address(self, address: int, alignment: int) -> None:
        """Sets alignment of generated value for given address. For example GLBAC registers have only alignment = 4.

        Args:
            address: The address for which to set alignment.
            alignment: The alignment value to set.
        """
        self._value_alignments_for_address[address] = alignment

    def sort_keys(self) -> None:
        """Sorts keys in this generator."""
        self._dcd.sort_keys()

    def set_key_name(self, key: Any, off: int) -> None:
        """Sets name and offset pair. Use before assigning into the generator.

        Args:
            key: The key name.
            off: The offset value.
        """
        if key in self._key_name_to_offset and self._key_name_to_offset[key] != off:
            raise KeyError()
        self._key_name_to_offset[key] = off
        self._key_offset_to_name[off] = key

    def add_key_comment(self, key: Any, comment: str) -> None:
        """Adds comment for given entry name.

        Args:
            key: The key for which to add a comment.
            comment: The comment text to add.
        """
        if isinstance(key, str):
            key = self._key_name_to_offset[key]
        if key not in self._key_comments:
            self._key_comments[key] = []
        if comment not in self._key_comments[key]:
            self._key_comments[key].append(comment)

    def print_head(self) -> None:
        """Generates comment and define name."""
        if self._comment:
            self.add_to_head(f"/*! {self._comment} */")

        end = " \\\n"
        indent = " " * self._indent
        self.add_to_head(f"#define {self._define}", end=end)
        self.add_to_head(f"{indent}{{", end=end)

    def print_members(self) -> None:
        """Generates all added entries with their comments."""
        indent = " " * (2 * self._indent)
        keys = sorted(self._dcd.keys()) if self._sort else self._dcd.ordered_keys()

        if len(keys):
            end = ", \\\n"
            for key in keys:
                key = typing.cast(int, key)
                val = self._dcd[key]
                if isinstance(key, str):
                    raise KeyError()

                # key name as the first word in comment line
                if key in self._key_offset_to_name:
                    comment = f"{self._key_offset_to_name[key]}: "
                else:
                    comment = ""

                # also add value comments
                if key in self._key_comments:
                    for v in self._key_comments[key]:
                        if comment:
                            comment += " "
                        comment += v

                if comment:
                    comment = f" /* {comment} */ "

                alignment = 8
                if key in self._value_alignments_for_address:
                    alignment = self._value_alignments_for_address[key]

                ks = f"{utils.convert_to_hex(key, upper_case=self._generate_upper_case_offset)}U"
                if val == 0:
                    self.add_to_members(f"{indent}SM_CFG_Z1({ks}){comment}", end=end)
                else:
                    write_macro = "SM_CFG_W1"
                    if ks == "0x00000000U":
                        write_macro = "SM_CFG_C1"
                    hex_val = utils.convert_to_hex(val, digits=alignment, upper_case=self._generate_upper_case_value)
                    self.add_to_members(f"{indent}{write_macro}({ks}), {hex_val}U{comment}", end=end)
        else:
            self.add_to_members(f"{indent}/* empty list */", end="\n")

        end = " \\\n"
        self.add_to_members(f"{indent}SM_CFG_END", end=end)

    def print_tail(self) -> None:
        """Generates tail after all entries were generated."""
        indent = " " * self._indent
        self.add_to_tail(f"{indent}}}")
        self.add_to_tail("")


class GenCfgMacro:
    """Finalizes the command or macro line for .cfg file generation"""

    def __init__(self, name: str, value: str = "", colon_macro: bool = False, value_tab_pos: int = 12) -> None:
        """Initialize final configuration macro generation settings

        Args:
          name: The name of the macro
          value: The initial value for the macro
          colon_macro: Whether to append a colon to the macro name
          value_tab_pos: The tab position for aligning values
        """
        self._name = name
        self._value = value
        self._colon_macro = colon_macro
        self._value_tab_pos = value_tab_pos
        self._commented_out = False

    def append(self, value: str, auto_comma: bool = True) -> None:
        """Append a string value to the existing value, keep comma-separated by default

        Args:
          value: The string value to append
          auto_comma: Whether to automatically add comma separation
        """
        if auto_comma and len(self._value) > 0:
            self._value += ", "
        self._value += value

    def append_json_values(
        self,
        json: Dict[str, Any],
        keys_normal: List[str] | None = None,
        keys_novalue: List[str] | None = None,
        keys_special: list[tuple[str, Any]] | None = None,
        all_keys: bool = False,
    ) -> None:
        """Append selected keys from json to existing value.
        Different set of keys generate:
            normal:  'key=value' if value is not None
            novalue: 'key' if value is boolean True
            special: formatted by a callback.

        Args:
            json: Dictionary containing key-value pairs to process
            keys_normal: List of keys to format as 'key=value'
            keys_novalue: List of keys to format as 'key' only
            keys_special: List of tuples containing key and callback function
            all_keys: Whether to include all keys from json
        """
        if keys_special is None:
            keys_special = []
        if keys_novalue is None:
            keys_novalue = []
        if keys_normal is None:
            keys_normal = []
        if all_keys:
            keys_normal.extend([k for k in json.keys() if k not in keys_normal and json[k] is not None])
            keys_novalue.extend([k for k in json.keys() if k not in keys_novalue and json[k] is None])
        for k in keys_normal:
            if k in json and json[k] is not None:
                value = int(json[k]) if isinstance(json[k], bool) else json[k]  # convert bool to 0/1
                self.append(f"{k}={value}")
        for k in keys_novalue:
            if k in json and json[k]:
                self.append(k)
        for spec in keys_special:
            spec_key = spec[0]
            spec_val = spec[1]
            if spec_val is not None:
                self.append(f"{spec_key}={spec_val}")

    def set_commented_out(self, commented_out: bool = True) -> None:
        """Mark the whole macro as commented out or active

        Args:
          commented_out: Whether to mark the macro as commented out
        """
        self._commented_out = commented_out

    def get(self) -> str:
        """Return string representation for .cfg file

        Returns:
          Formatted string representation of the macro
        """
        comment = "# " if self._commented_out else ""
        name = self._name
        if self._colon_macro:
            name += ":"
        space = " " if len(name) >= self._value_tab_pos else " " * (self._value_tab_pos - len(name))
        return f"{comment}{name}{space}{self._value}"

    def __str__(self) -> str:
        """String representation for .cfg file

        Returns:
          Formatted string representation of the macro
        """
        return self.get()
