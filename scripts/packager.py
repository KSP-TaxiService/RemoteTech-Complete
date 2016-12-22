#!/usr/bin/python3
# -*- coding: UTF-8 -*-
"""
Packager script for RemoteTech-Complete.

Prerequisites:
    - Expect built assemblies (*.dll) in RemoteTech-Complete\src\output
        - can be overridden with --input-dir.

    - Working directory is the root directory of the repository
        (RemoteTech-Complete/)
"""
import logging
import shutil
from typing import Optional
import argparse
import os


LOGGING_LEVELS = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL,
}

SOURCE_DIR = "src"
DEFAULT_INPUT_DIR = "{}{}output".format(SOURCE_DIR, os.sep)
DEFAULT_OUTPUT_DIR = "{0}{1}GameData{1}RemoteTech".format(SOURCE_DIR, os.sep)
NON_MODULE_PACKAGES = ["RemoteTech-Antennas"]
NO_COPY_FILE_NAMES = [".gitattributes", ".gitignore"]


class Packager(object):
    def __init__(self):
        self.source_dir = None
        self.input_dir = None
        self.output_dir = None
        self.cwd = None

    def setup_cwd(self, relative_path: Optional[str]=None) -> str:
        """Set the current working directory for this script.

        Args:
            relative_path:

        Returns:

        """

        # get current script directory
        script_dir = os.path.dirname(os.path.abspath(__file__))

        # get source directory
        self.source_dir = os.path.abspath(
            os.path.join(script_dir, "..", SOURCE_DIR))

        if not os.path.isdir(self.source_dir):
            raise RuntimeError(
                "Source directory couldn't be found in '{}'.".format(
                    self.source_dir)
            )

        if relative_path:
            # if given path is relative, just add to current directory
            script_dir = os.path.join(script_dir, relative_path)
        else:
            # are we living in '/scripts' dir?
            last_dir = os.path.basename(os.path.normpath(script_dir))
            # are we in 'RemoteTech-Complete/scripts'
            rt_complete_dir = os.path.abspath(os.path.join(script_dir, ".."))
            up_dir = os.path.basename(os.path.normpath(rt_complete_dir)).lower()
            if last_dir != "scripts" or up_dir != "remotetech-complete":
                raise RuntimeError(
                    "This script must reside in 'RemoteTech-Complete/scripts'.")

            # set current working directory to be in 'RemoteTech-Complete/' dir
            script_dir = rt_complete_dir

        os.chdir(script_dir)

        self.cwd = script_dir

        return script_dir

    @staticmethod
    def make_directory(root_dir, path, is_relative=True):
        if is_relative:
            directory = os.path.join(root_dir, path)
        else:
            directory = path

        return directory

    def set_input_dir(self, root_dir, output_path, is_relative=True):
        self.input_dir = Packager.make_directory(root_dir, output_path,
                                                 is_relative)
        return self.input_dir

    def set_output_dir(self, root_dir, input_path, is_relative=True):
        self.output_dir = Packager.make_directory(root_dir, input_path,
                                                  is_relative)
        return self.output_dir

    def check_input_and_output_dirs(self):
        if not self.input_dir:
            raise RuntimeError("input_dir is None")
        if not os.path.isdir(self.input_dir):
            raise RuntimeError("input_dir doesn't exist.")
        if not self.output_dir:
            raise RuntimeError("output_dir is None")
        if not os.path.isdir(self.output_dir):
            logging.info("Creating output directory: {}"
                         .format(self.output_dir))

            os.makedirs(self.output_dir, exist_ok=True)
        else:
            logging.info("output dir exists: emptying it")
            # delete directory (and everything it might contain)
            shutil.rmtree(self.output_dir)
            # recreate it
            os.makedirs(self.output_dir, exist_ok=True)

    def package_release(self):
        self.package_modules()
        self.package_directory()

    def package_directory(self):
        for package_name in NON_MODULE_PACKAGES:
            package_path_src = os.path.join(self.source_dir, package_name)
            if not os.path.isdir(package_path_src):
                raise RuntimeError(
                    "Packaging non module: {} is not a directory."
                    .format(package_path_src))

            logging.info("Packaging: {}".format(package_name))

            package_path_dst = os.path.join(self.output_dir, package_name)
            shutil.copytree(package_path_src, package_path_dst,
                            ignore=shutil.ignore_patterns(*NO_COPY_FILE_NAMES))

    def package_modules(self):
        for module_full_path in self.get_modules():
            # get file name (with extension)
            _, tail = os.path.split(module_full_path)
            # get file name
            root, _ = os.path.splitext(tail)

            if not tail or not root:
                raise RuntimeError(
                    "No root or tail in module name.")

            logging.info("Packaging: {}".format(root))

            # create sub-directory in output directory
            sub_dir = os.path.join(self.output_dir, root)
            os.mkdir(sub_dir)

            # copy module into newly created output sub-directory
            old_path = module_full_path
            new_path = os.path.join(sub_dir, tail)
            shutil.copy2(old_path, new_path)

    def get_modules(self):
        for module_name in os.listdir(self.input_dir):
            module_full_path = os.path.join(self.input_dir, module_name)
            _, ext = os.path.splitext(module_name)
            if ext.lower() == ".dll":
                yield module_full_path


def main(args):
    logging.info("Starting packaging script.")

    packager = Packager()

    # set up directories (cwd, input, output)
    packager.setup_cwd(args.cwd)
    packager.set_input_dir(packager.cwd, args.input_dir,
                           args.input_dir_relative)
    packager.set_output_dir(packager.cwd, args.output_dir,
                            args.output_dir_relative)
    packager.check_input_and_output_dirs()

    logging.info("Directories:\n\tCurrent working directory: {}"
                 "\n\tInput directory: {}\n\tOutput directory: {}"
                 .format(packager.cwd, packager.input_dir, packager.output_dir))

    packager.package_release()

    logging.info("Job done. Quitting!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='RemoteTech-Complete Packager')

    parser.add_argument(
        "-i", "--input-dir", action="store", dest="input_dir",
        default=DEFAULT_INPUT_DIR,
        help="Input directory where to find the built assemblies."
             " [default: {}]".format(DEFAULT_INPUT_DIR))

    parser.add_argument(
        "--input-dir-relative", action="store_false",
        dest="input_dir_relative", default=True,
        help="Indicates whether the --input-dir is a relative path or not."
             " [default: True]")

    parser.add_argument(
        "-o", "--output-dir", action="store", dest="output_dir",
        default=DEFAULT_OUTPUT_DIR,
        help="Output directory where to put the final package."
             "[default: {}]".format(DEFAULT_OUTPUT_DIR))

    parser.add_argument(
        "--output-dir-relative", action="store_false",
        dest="output_dir_relative", default=True,
        help="Indicates whether the --output-dir is a relative path or not."
             " [default: True]")

    parser.add_argument(
        "--cwd", action="store",
        help="Working directory, relative to this script location.")

    parser.add_argument(
        "-l", "--logging-level", action="store", dest="logging_level",
        help="Logging level (as from logging module).")

    # parse arguments
    parsed_args = parser.parse_args()

    # setup logging
    logging_level = LOGGING_LEVELS.get(parsed_args.logging_level,
                                       logging.NOTSET)
    logging.basicConfig(level=logging_level)

    # call main
    main(parsed_args)
