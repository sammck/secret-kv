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
from secret_kv import (
    __version__ as pkg_version,
    create_kv_store,
  )
from secret_kv import (
    KvStoreConfig,
    KvStore,
    locate_kv_store_config_file,
    load_kv_store_config,
  )

class CmdExitError(RuntimeError):
  exit_code: int

  def __init__(self, exit_code: int):
    super(f"Command exitied with return code {exit_code}")
    self.exit_code = exit_code

class CommandHandler:
  _argv: Optional[Sequence[str]]
  _cwd: str
  _config_file: Optional[str] = None
  _store_config: Optional[KvStoreConfig] = None
  _store: Optional[KvStore] = None
  _scan_parent_dirs: bool = True
  _erase_db: bool = False
  _passphrase: Optional[str] = None

  def __init__(self, argv: Optional[Sequence[str]]=None):
    self._argv = argv

  def abspath(self, path: str) -> str:
    return os.path.abspath(os.path.join(self._cwd, os.path.expanduser(path)))

  def get_config_file(self) -> str:
    if self._config_file is None:
      self._config_file = locate_kv_store_config_file(config_path=self._cwd, scan_parent_dirs=self._scan_parent_dirs)
    return self._config_file

  def get_config(self) -> KvStoreConfig:
    if self._store_config is None:
      self._store_config = load_kv_store_config(config_path=self.get_config_file())
    return self._store_config

  def get_kv_store(self) -> KvStore:
    if self._store is None:
      cfg = self.get_config()
      self._store = cfg.open_store(erase=self._erase_db, passphrase=self._passphrase)
    return self._store
    
  def cmd_bare(self, args: argparse.Namespace) -> int:
    print("A command is required", file=sys.stderr)
    return 1

  def cmd_clear_database(self, args: argparse.Namespace) -> int:
    self._erase_db = True
    kv = self.get_kv_store()
    print(f"{kv} successfully cleared.", file=sys.stderr)
    return 0

  def cmd_test(self, args: argparse.Namespace) -> int:
    return 0

  def cmd_create(self, args: argparse.Namespace) -> int:
    parent_dir = self.abspath(args.parent_dir)
    passphrase: Optional[str] = args.passphrase

    db = create_kv_store(parent_dir, passphrase=passphrase)

    print(f"Successfully created .secret-kv store under {parent_dir}", file=sys.stderr)
    return 0

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
    parser.add_argument('-p', '--passphrase', default=None,
                        help='The passphrase to be used for accessing the store. By default, the ' +
                             'passphrase saved in the keyring will be used, or the global ' +
                             'default secret-kv passphrase (in the keyring) will be used for new stores')
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

    parser_clear_database = subparsers.add_parser('clear-database', description="Erases all content in the database without deleting it")
    parser_clear_database.set_defaults(func=self.cmd_clear_database)

    args = parser.parse_args(self._argv)
    self._cwd = os.path.abspath(os.path.expanduser(args.cwd))
    self._passphrase = args.passphrase
    config_file: Optional[str] = args.config
    if not config_file is None:
      self._config_file = self.abspath(config_file)
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
