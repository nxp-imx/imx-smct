#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Module related to pre-deployment preparation of the SMCT"""
import argparse
import os
import re
import shutil
import subprocess
import sys
from typing import List, Tuple


FILES = ["smct.py", "readme.md"]
FOLDERS = ["smct"]
IGNORED_FOLDERS = ["__pycache__"]
SM_MODEL_FOLDER = "sm_model"


def execute_binary(binary_path: str, arguments: List[str], stdin: str | None = None) -> Tuple[int, str, str]:
    process_arguments = [binary_path] + arguments
    process = subprocess.Popen(process_arguments, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if stdin is not None:
        process.stdin.write(stdin.encode("utf-8"))
    code = process.wait()
    stdout = process.stdout.read().decode("utf-8")
    stderr = process.stderr.read().decode("utf-8")
    return code, stdout, stderr


class Prepare:
    def __init__(self) -> None:
        self._argparse = self._prepare_parser()

    def main(self, args: List[str]) -> None:
        parsed_arguments = self._parse_input(args)
        if parsed_arguments.commit is None:
            self.prepare_current(parsed_arguments)
        else:
            self.prepare_with_git(parsed_arguments)

    def prepare_with_git(self, parsed_arguments: argparse.Namespace) -> None:
        if parsed_arguments.commit is None:
            raise ValueError("Commit was not specified")
        if parsed_arguments.output is None:
            raise ValueError("Output path was not specified")
        commit = parsed_arguments.commit
        output_folder = parsed_arguments.output
        include_model = parsed_arguments.export_model
        branch = self._get_current_branch()
        if branch is None:
            raise ValueError("Cannot obtain current branch from GIT")
        self._checkout(commit)
        self._copy_files(output_folder, include_model)
        self._checkout(branch)

    def prepare_current(self, parsed_arguments: argparse.Namespace) -> None:
        if parsed_arguments.output is None:
            raise ValueError("Output path was not specified")
        output_folder = parsed_arguments.output
        include_model = parsed_arguments.export_model
        self._copy_files(output_folder, include_model)

    @classmethod
    def _prepare_parser(cls) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(description="SM Config Tool pre-deployment")
        parser.add_argument("--commit", "-c",
                            metavar="COMMIT",
                            help="Commit or tag of branch, or branch name in the repository which should be prepared for deployment",
                            type=str,
                            action="store")
        parser.add_argument("--output", "-o",
                            metavar="OUTPUT",
                            help="Path to folder where the output should be stored",
                            type=str,
                            action="store")
        parser.add_argument("--export_model", "-m",
                            help="Export the sm_model folder to the output folder",
                            action="store_true")
        return parser

    def _parse_input(self, args: List[str]) -> argparse.Namespace:
        return self._argparse.parse_args(args)

    @classmethod
    def _get_ignore_folders(cls, dir: str, contents: list[str]) -> list[str]:
        return [
            item for item in contents
            if os.path.isdir(os.path.join(dir, item)) and item in IGNORED_FOLDERS
        ]

    @classmethod
    def _copy_files(cls, output: str, include_model: bool) -> None:
        cwd = os.getcwd()
        for folder in FOLDERS:
            src = os.path.join(cwd, folder)
            dest = os.path.join(output, folder)
            shutil.copytree(src, dest, dirs_exist_ok=True, ignore=cls._get_ignore_folders)
        for file in FILES:
            src = os.path.join(cwd, file)
            dest = os.path.join(output, file)
            shutil.copy(src, dest)
        if include_model:
            src = os.path.join(cwd, SM_MODEL_FOLDER)
            dest = os.path.join(output, SM_MODEL_FOLDER)
            shutil.copytree(src, dest, dirs_exist_ok=True)

    @classmethod
    def _checkout(cls, commit: str) -> bool:
        code, _, _ = execute_binary("git", ["checkout", commit])
        if code == 0:
            return True
        return False

    @classmethod
    def _get_current_branch(cls) -> str | None:
        code, out, _ = execute_binary("git", ["branch", "--show-current"])
        if code != 0:
            return None
        pattern = re.compile(r"^(.*)$")
        match = pattern.match(out)
        if match is None:
            return None
        return match.group(1)


if __name__ == "__main__":
    prepare = Prepare()
    prepare.main(sys.argv[1:])
