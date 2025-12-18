#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Main module of the System Manager configuration tool"""
import argparse
import logging
import os.path
import sys
from typing import List, Optional

from smct import utils
from smct.configuration.configuration_provider import ConfigurationProvider
from smct.expcetions.cfg_tool_exception import CfgToolException
from smct.generation.config_generator import ConfigGenerator
from smct.generation.export_cfg import CfgExporter
from smct.model.chip_model_provider import ChipModelProvider
from smct.parsers.cfg_parser import CfgFileParser
from smct.parsers.hdr_parser import ApiResourceParser
from smct.parsers.resource_parser import ResourceParser
from smct.product_info import ProductInfo
from smct.resources.resdump import dump_configuration, generate_database
from smct.resources.resource_database_provider import ResourceDatabaseProvider
from smct.validation.configuration_validator import ConfigurationValidator
from smct.validation.formatters.console_formatter import ConsoleFormatter
from smct.validation.formatters.json_formatter import JsonFormatter, JsonMemoryHandler

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger()


class AppErrorException(Exception):
    """Application error exception"""

    def __init__(self, message: str):
        if not message:
            message = "Unknown Exception"
        message = "SM CfgTool Application: " + message
        super().__init__(message)


CATCHABLE_EXCEPTIONS = (KeyError, ValueError, TypeError, AppErrorException, CfgToolException)


def _parse_arguments(args: List[str]) -> argparse.Namespace:
    """Parses the given arguments and returns the Argparse namespace with values that match the parser.

    Args:
        args: List of command line arguments to parse.

    Returns:
        Argparse namespace with parsed argument values.
    """
    parser = argparse.ArgumentParser(description="SM Config Tool")

    parser.add_argument("--sm_dir", metavar="ROOT_DIR", help="The SM FW root directory (default is '[this_tool_path]/..)", type=str, action="store")

    parser.add_argument(
        "--load_device",
        "-l",
        help="Load (parse) SM FW files related to a device. "
        "The tool parses resource database from .h and .cfg files of the device "
        "instead of loading the local database. Use options '-d' and '-b' to define device and board to be loaded",
        action="store_true",
    )

    parser.add_argument(
        "--load_cfg",
        "-c",
        metavar="FILE.CFG",
        help="Load SM FW user configuration from boards .cfg file. "
        "The tool parses resource database and full user configuration from .h and .cfg files."
        "instead of local database and project file.",
        type=str,
        action="store",
    )

    parser.add_argument(
        "--store_db",
        metavar="OUTPUT_PATH",
        help="The tool stores resource database to specified output file/directory. "
        "Use either absolute path on disk or simple folder name. "
        "If simple folder name is used then folder will be created in SM FW/configs/{simple folder name}",
        type=str,
        action="store",
    )

    parser.add_argument(
        "--store_conf",
        metavar="OUTPUT_PATH",
        help="The tool stores user configuration to specified output file/directory. "
        "Use either absolute path on disk or simple folder name. "
        "If simple folder name is used then folder will be created in SM FW/configs/{simple folder name}",
        type=str,
        action="store",
    )

    parser.add_argument(
        "--store_log",
        metavar="OUTPUT_PATH",
        help="The tool stores error log to specified output file/directory. "
        "Use either absolute path on disk or simple folder name. "
        "If simple folder name is used then folder will be created in SM FW/configs/{simple folder name}",
        type=str,
        action="store",
    )

    parser.add_argument("--force", "-f", help="Force overwriting output file or files.", action="store_true")

    parser.add_argument("--device", "-d", metavar="DEVICE", help="Enforce device name.", type=str, action="store")

    parser.add_argument("--board", "-b", metavar="BOARD", help="Enforce board name.", type=str, action="store")

    parser.add_argument(
        "--input",
        "-i",
        metavar="InputDirectory",
        type=str,
        help="Input directory where folder smct_configs with JSON files that contain configuration are located. "
        "Use either absolute path on disk or simple folder name. ",
        action="store",
    )

    parser.add_argument(
        "--output",
        "-o",
        metavar="OutputDirectory",
        type=str,
        help="Output directory where output files are generated. "
        "Use either absolute path on disk or simple folder name. "
        "If simple folder name is used then folder will be created in SM FW/configs/{simple folder name}",
        action="store",
    )

    parser.add_argument("--soc_dir", metavar="SocDirectory", type=str, help="Input directory where soc resources are located.", action="store")

    parser.add_argument("--version", "-v", help="Version of the tool.", action="store_true")

    parser.add_argument(
        "--store_cfg_file",
        metavar="OutputCfgFile",
        type=str,
        help="Export configuration in native .cfg format. Specify full path to destination file.",
        action="store",
    )

    argv = parser.parse_args(args)
    return argv


def _get_root_dir(root_dir: Optional[str] = None) -> str:
    """Returns the System Manager firmware root directory.

    Args:
        root_dir: Optional root directory path. If None, attempts to find it automatically.

    Returns:
        The System Manager firmware root directory path.
    """
    if root_dir is None:
        directory, _ = os.path.split(os.path.realpath(__file__))
        root = os.path.join(directory, "..", "..")  # default location is in sm_repo/smct
        if not os.path.exists(os.path.join(root, "sm")):
            fw_root = utils.find_firmware_root_dir(root)
            if fw_root is None:
                raise AppErrorException("SM FW root folder cannot be found")
            root = fw_root
    else:
        root = root_dir
    if not os.path.isdir(root):
        raise AppErrorException(f"Cannot determine root directory. " f"Provided/inferred path {os.path.abspath(root)} is not directory")
    return root


def _parse_database(root_directory: str, device_name: str, board_name: str) -> bool:
    """Parses the resource database based on the device and board.

    Args:
        root_directory: The root directory path.
        device_name: The name of the device.
        board_name: The name of the board.

    Returns:
        True if parsing was successful, False otherwise.
    """
    try:
        header_parser = ApiResourceParser()
        cfg_parser = CfgFileParser()
        resource_parser = ResourceParser(device_name)

        resource_parser.parse_soc_resources()
        if not header_parser.parse_device(root_directory, device_name):
            return False
        if not header_parser.parse_board(root_directory, board_name):
            return False
        cfg_parser.add_static_resources()
        cfg_parser.parse_device(root_directory, device_name)

        if ResourceDatabaseProvider.get_database().is_empty():
            raise AppErrorException(f"Database could not be parsed from {device_name} sources")
        return True
    except CATCHABLE_EXCEPTIONS as e:
        logger.critical("SMCT failed parsing database due to following internal problem: %s", str(e), extra={"source": "general"})
        return False


def _parse_config_file(root_directory: str, config_file_name: str) -> None:
    """Parses the given CFG file.

    Args:
        root_directory: The root directory path.
        config_file_name: The name of the configuration file to parse.
    """
    try:
        header_parser = ApiResourceParser()
        cfg_parser = CfgFileParser()
        cfg_parser.enable_board_parser(header_parser, root_directory)

        file_path = os.path.join(root_directory, "configs", config_file_name)
        file_name = os.path.splitext(os.path.basename(file_path))[0]
        ConfigurationProvider.get_configuration().set_config_name(file_name)
        cfg_parser.add_static_resources()
        cfg_parser.parse_file(file_path)

        if ResourceDatabaseProvider.get_database().is_empty():
            raise AppErrorException(f"Database could not be parsed from {config_file_name} configuration")
    except CATCHABLE_EXCEPTIONS as e:
        logger.critical("SMCT failed parsing config file %s due to following internal problem: %s", config_file_name, str(e), extra={"source": file_path})


def _load_database(folder: str) -> None:
    """Loads database from the given folder.

    Args:
        folder: The folder path containing database files.
    """
    try:
        ResourceDatabaseProvider.get_database().load_from_json(folder)
    except CATCHABLE_EXCEPTIONS as e:
        source = os.path.join(folder, "atomic_resources.json")
        logger.critical("SMCT failed loading atomic_resources.json database due to following internal problem: %s", str(e), extra={"source": source})
    try:
        ChipModelProvider.get_model().load_from_json(folder)
    except CATCHABLE_EXCEPTIONS as e:
        source = os.path.join(folder, "chip_data.json")
        logger.critical("SMCT failed loading chip_data.json database due to following internal problem: %s", str(e), extra={"source": source})


def _load_configuration(folder: str) -> None:
    """Loads configuration from the given folder.

    Args:
        folder: The folder path containing configuration files.
    """
    try:
        ConfigurationProvider.get_configuration().load_configuration(folder)
    except CATCHABLE_EXCEPTIONS as e:
        source = os.path.join(folder, "user_configuration.json")
        logger.critical("SMCT failed loading user_configuration.json due to following internal problem: %s", str(e), extra={"source": source})


def _generate_all(output_dir: str, force: bool = False) -> None:
    """Generates all files.

    Args:
        output_dir: The output directory path.
        force: Whether to force overwrite existing files.
    """
    try:
        generator = ConfigGenerator()
        generator.generate(ConfigurationProvider.get_configuration(), output_dir, force=force)
    except CATCHABLE_EXCEPTIONS as e:
        logger.critical("SMCT failed due to following internal problem: %s", str(e), extra={"source": "general"})


def _store_cfg_file(output_filename: str, force: bool = False) -> None:
    """Exports configuration to a legacy CFG file format"""
    try:
        (directory, name) = os.path.split(output_filename)
        exporter = CfgExporter(name)
        exporter.generate(ConfigurationProvider.get_configuration(), directory, force=force)
    except CATCHABLE_EXCEPTIONS as e:
        logger.critical("SMCT failed exporting configuration file due to following internal problem: %s", str(e), extra={"source": output_filename})


def main(args: List[str] | None = None) -> int:
    """Main function.

    Args:
        args: Optional list of command line arguments. If None, uses sys.argv[1:].

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    try:
        return _main(args)
    except CATCHABLE_EXCEPTIONS as e:
        logger.critical("SMCT failed due to following internal problem: %s", str(e), extra={"source": "general"})
    finally:
        for handler in logger.handlers:
            handler.close()
    return 1


def _main(args: List[str] | None = None) -> int:
    """Main function - implementation.

    Args:
        args: Optional list of command line arguments. If None, uses sys.argv[1:].

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    if args is None:
        args = sys.argv[1:]
    argv = _parse_arguments(args)

    if argv.version:
        print(ProductInfo.get_smct_version_string())
        return 0

    ConfigurationProvider.clear_configuration()
    ResourceDatabaseProvider.clear_database()
    ChipModelProvider.clear_model()

    root_directory = _get_root_dir(argv.sm_dir)
    ConfigurationProvider.get_configuration().set_sm_fw_root_directory(root_directory)

    json_handler = None
    if argv.store_log:
        output_folder = argv.store_log
        if not os.path.isabs(output_folder):
            output_folder = os.path.join(root_directory, "configs", argv.store_log, "smct_configs")

        formatter = JsonFormatter()
        json_handler = JsonMemoryHandler(formatter, output_folder, mode="w")
        logger.addHandler(json_handler)

    # load resource database to work with
    ResourceParser.soc_directory = argv.soc_dir
    if argv.load_device:
        if argv.output:
            raise AppErrorException("Argument --load_device is expected to be used with --store_db or --store_conf command only.")
        if not _parse_database(root_directory, argv.device, argv.board):
            raise AppErrorException("Failed to load the database")
    if argv.load_cfg:
        _parse_config_file(root_directory, argv.load_cfg)
    if not argv.load_device and not argv.load_cfg:
        folder = ""
        if argv.input:
            folder = argv.input
        elif argv.board:
            folder = os.path.join(root_directory, "configs", argv.board)
        else:
            raise AppErrorException("Either --input/--board is required for generating output")
        if not os.path.isabs(folder):
            folder = os.path.join(root_directory, "configs", folder, "smct_configs")
        _load_database(folder)
        if ResourceDatabaseProvider.get_database().is_empty():
            raise AppErrorException(f"Database could not be loaded for device={argv.device} and board={argv.board}")
        _load_configuration(folder)

    if not argv.load_device:
        validation = ConfigurationValidator(ConfigurationProvider.get_configuration())
        validation.validate()
        validation.process_entries(ConsoleFormatter())

    if argv.store_db:
        output_folder = argv.store_db
        if not os.path.isabs(output_folder):
            output_folder = os.path.join(root_directory, "configs", argv.store_db, "smct_configs")

        if os.path.exists(output_folder) and not argv.force:
            raise AppErrorException(f"Database output path already exists '{output_folder}'." f" Use --force option.")

        os.makedirs(output_folder, exist_ok=True)
        generate_database(output_folder)

    if argv.store_conf:
        output_folder = argv.store_conf
        if not os.path.isabs(output_folder):
            output_folder = os.path.join(root_directory, "configs", argv.store_conf, "smct_configs")

        if os.path.exists(output_folder) and not argv.force:
            raise AppErrorException(f"User configuration output path already exists '{output_folder}'." f" Use --force option.")

        os.makedirs(output_folder, exist_ok=True)
        dump_configuration(output_folder)

    if argv.output:
        folder = argv.output
        if not os.path.isabs(folder):
            folder = os.path.join(root_directory, "configs", folder)
        os.makedirs(folder, exist_ok=True)
        _generate_all(folder, force=argv.force)

    if argv.store_cfg_file:
        output_filename = os.path.join(root_directory, argv.store_cfg_file)
        _store_cfg_file(output_filename, force=argv.force)

    # Unregister the JSON log handler - Repeated calls (tests, bath mode) to _main will keep the previous handlers active
    if json_handler:
        json_handler.close()
        logger.removeHandler(json_handler)

    return 0


if __name__ == "__main__":
    main()
