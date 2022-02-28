#!/usr/bin/env python3
#
# Copyright (c) 2022 Samuel J. McKelvie
#
# MIT License - See LICENSE file accompanying this package.
#

"""Command-line interface for secret_kv package"""


import argparse
from typing import Optional, Sequence, List

import os
import sys

# NOTE: this module runs with -m; do not use relative imports
from secret_kv import __version__ as pkg_version
from secret_kv.sql_store import test_me

class CmdExitError(RuntimeError):
  exit_code: int
  def __init__(self, exit_code: int):
    super(f"Command exitied with return code {exit_code}")
    self.exit_code = exit_code

class CommandHandler:
  _argv: Optional[Sequence[str]]
  _cwd: str

  def __init__(self, argv: Optional[Sequence[str]]=None):
    self._argv = argv

  def abspath(self, path: str) -> str:
    return os.path.abspath(os.path.join(self._cwd, os.path.expanduser(path)))

  def cmd_bare(self, args: argparse.Namespace) -> int:
    print("A command is required", file=sys.stderr)
    return 1

  def cmd_test(self, args: argparse.Namespace) -> int:
    test_me()
    return 0

  def cmd_create(self, args: argparse.Namespace) -> int:
    parent_dir = self.abspath(args.parent_dir)
    print(f"Not yet implemented: {parent_dir}", file=sys.stderr)
    return 1

  def run(self) -> int:
    """Run the secret-kv command-line tool with provided arguments

    Args:
        argv (Optional[Sequence[str]], optional):
            A list of commandline arguments (NOT including the program as argv[0]!),
            or None to use sys.argv[1:]. Defaults to None.

    Returns:
        int: The exit code that would be returned if this were run as a standalone command.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Access a secret key/value database.")
    parser.add_argument('--version', action='store_true', default=False,
                        help='Display version')
    parser.add_argument('-C', '--cwd', default='.',
                        help="Change the effective directory used to search for configuration")
    parser.add_argument('-c', '--config',
                        help="Specify the location of the config file")
    parser.set_defaults(func=self.cmd_bare)

    subparsers = parser.add_subparsers(
                        title='Commands',
                        description='Valid commands',
                        help='Additional help available with "<command-name> -h"')

    parser_test = subparsers.add_parser('test', description="Run a simple test")
    parser_test.set_defaults(func=self.cmd_test)

    parser_create = subparsers.add_parser('create', description="Create a new secret key-value store")
    parser_create.add_argument('parent_dir',
                        help='The parent directory under which a ".secret-kv" subdirectory will be created')
    parser_create.set_defaults(func=self.cmd_create)

    args = parser.parse_args(self._argv)
    self._cwd = os.path.abspath(os.path.expanduser(args.cwd))
    rc = args.func(args)

    return rc

def run(argv: Optional[Sequence[str]]=None) -> int:
  try:
    rc = CommandHandler(argv).run()
  except CmdExitError as ex:
    rc = ex.exit_code
  return rc

# allow running with "python3 -m", or as a standalone script
if __name__ == "__main__":
  sys.exit(run())
