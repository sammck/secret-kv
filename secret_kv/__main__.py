#!/usr/bin/env python3
#
# Copyright (c) 2022 Samuel J. McKelvie
#
# MIT License - See LICENSE file accompanying this package.
#

"""Command-line interface for secret_kv package"""


import base64
from typing import Optional, Sequence, List, Union

import os
import sys
import argparse
import argcomplete
import json
from base64 import b64encode, b64decode

# NOTE: this module runs with -m; do not use relative imports
from secret_kv import (
    __version__ as pkg_version,
    create_kv_store,
  )
from secret_kv import (
    KvStoreConfig,
    KvStore,
    KvValue,
    locate_kv_store_config_file,
    load_kv_store_config,
    delete_kv_store,
  )

class CmdExitError(RuntimeError):
  exit_code: int

  def __init__(self, exit_code: int):
    super(f"Command exitied with return code {exit_code}")
    self.exit_code = exit_code

class CommandHandler:
  _argv: Optional[Sequence[str]]
  _parser: argparse.ArgumentParser
  _args: argparse.Namespace
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

  def cmd_clear_database(self) -> int:
    self._erase_db = True
    kv = self.get_kv_store()
    print(f"{kv} successfully cleared.", file=sys.stderr)
    return 0

  def cmd_delete_store(self) -> int:
    config_file = self.get_config_file()
    store_desc = delete_kv_store(config_file, scan_parent_dirs=False)
    print(f"secret-cv store with config at '{store_desc}' successfully deleted.", file=sys.stderr)
    return 0

  def cmd_test(self) -> int:
    return 0

  def cmd_create(self) -> int:
    args = self._args
    parent_dir = self.abspath(args.parent_dir)
    passphrase: Optional[str] = args.passphrase

    db = create_kv_store(parent_dir, passphrase=passphrase)

    print(f"Successfully created .secret-kv store under {parent_dir}", file=sys.stderr)
    return 0

  def cmd_get(self) -> int:
    #
    """
    parser_set.add_argument('key',
                        help='The key name for which a value is being set')
    parser_set.add_argument('value', nargs='?', default=None,
                        help='The value to assign to the key. By default, interpreted as a string value. See options for interpretaton.')
    parser_set.add_argument('-t', '--type', dest='value_type', default=None, choices= [ 'str', 'int', 'float', 'bool', 'json', 'base64', 'binary' ],
                        help='Specify how the provided value is interpreted')
    parser_set.add_argument('--json', dest="vtype_json", action='store_true', default=False,
                        help='short for --type=json')
    parser_set.add_argument('--int', dest="vtype_int", action='store_true', default=False,
                        help='short for --type=int')
    parser_set.add_argument('--stdin', dest="use_stdin", action='store_true', default=False,
                        help='Read the value from stdin instead of the commandline')
    parser_set.add_argument('-i', '--input', dest="input_file", default=None,
                        help='Read the value from the specified file instead of the commandline')

    """
    args = self._args
    key: str = args.key
    store = self.get_kv_store()
    kv = store.get_value(key)
    if kv is None:
      raise KeyError(f"secret-kv: get: key \"{key}\" does not exist")
    print(json.dumps(kv.json_data, indent=2, sort_keys=True))

  def cmd_set(self) -> int:
    #
    """
    parser_set.add_argument('key',
                        help='The key name for which a value is being set')
    parser_set.add_argument('value', nargs='?', default=None,
                        help='The value to assign to the key. By default, interpreted as a string value. See options for interpretaton.')
    parser_set.add_argument('-t', '--type', dest='value_type', default=None, choices= [ 'str', 'int', 'float', 'bool', 'json', 'base64', 'binary' ],
                        help='Specify how the provided value is interpreted')
    parser_set.add_argument('--json', dest="vtype_json", action='store_true', default=False,
                        help='short for --type=json')
    parser_set.add_argument('--int', dest="vtype_int", action='store_true', default=False,
                        help='short for --type=int')
    parser_set.add_argument('--stdin', dest="use_stdin", action='store_true', default=False,
                        help='Read the value from stdin instead of the commandline')
    parser_set.add_argument('-i', '--input', dest="input_file", default=None,
                        help='Read the value from the specified file instead of the commandline')

    """
    args = self._args
    key: str = args.key
    value_s: Optional[str] = args.value
    value_type_s: Optional[str] = args.value_type
    if args.vtype_json:
      if value_type_s is None:
        value_type_s = 'json'
      elif value_type_s != 'json':
        raise ValueError(f"secret-kv: set: Conflicting value types {value_type_s} and json")
    if args.vtype_int:
      if value_type_s is None:
        value_type_s = 'int'
      elif value_type_s != 'int':
        raise ValueError(f"secret-kv: set: Conflicting value types {value_type_s} and int")
    if value_type_s is None:
      value_type_s = 'str'
    use_stdin: bool = args.use_stdin
    input_file: Optional[str] = args.input_file
    if use_stdin:
      if input_file is None:
        input_file = '/dev/stdin'
      else:
        raise ValueError(f"secret-kv: set: Conflicting value input sources, --stdin and \"{input_file}\"")
    value: Union[str, bytes]
    if input_file is None:
      if value_s is None:
        raise ValueError("secret-kv: set: One of <value>, --stdin, or --input <filename> must be provided.")
      if value_type_s == 'binary':
        value = value_s.encode('utf-8')
      else:
        value = value_s
    else:
      if not value_s is None:
        raise ValueError("secret-kv: set: <value> must be omitted if -i, --input, or --stdin is provided.")
      mode = 'b' if value_type_s == 'binary' else 't'
      with open(input_file, mode) as f:
        value = f.readall()

    if value_type_s == 'base64':
      try:
        value = b64decode(value, validate=True)
      except Exception as ex:
        raise ValueError(f"secret-kv: set: Invalid base-64 encoded string: {ex}") from ex
      value_type_s = 'binary'

    if value_type_s == 'int':
      try:
        value = int(value)
      except ValueError as ex:
        raise ValueError(f"secret-kv: set: Invalid integer literal") from ex
    elif value_type_s == 'float':
      try:
        value = float(value)
      except ValueError as ex:
        raise ValueError(f"secret-kv: set: Invalid float literal") from ex
    elif value_type_s == 'bool':
      value = value.lower()
      if value in [ 'true', 't', 'yes', 'y', '1' ]:
        value = 'true'
      elif value in [ 'false', 'f', 'no', 'n', '0' ]:
        value = 'false'
      else:
        raise ValueError(f"secret-kv: set: Invalid boolean literal: '{value}'")
    elif value_type_s == 'json':
      try:
        value = json.loads(value)
      except json.JSONDecodeError as ex:
        raise ValueError(f"secret-kv: set: Invalid JSON text: {ex}") from ex

    elif value_type_s in [ 'str', 'binary' ]:
      pass

    kv = KvValue(value)
    store = self.get_kv_store()
    store.set_value(key, kv)

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
    self._parser = parser
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

    parser_delete_store = subparsers.add_parser('delete-store', description="Deletes the secret-kv store, including database, config, and .secret-kv directory")
    parser_delete_store.set_defaults(func=self.cmd_delete_store)

    parser_set = subparsers.add_parser('set', description="Set the value associated with a key")
    parser_set.add_argument('key',
                        help='The key name for which a value is being set')
    parser_set.add_argument('value', nargs='?', default=None,
                        help='The value to assign to the key. By default, interpreted as a string value. See options for interpretaton.')
    parser_set.add_argument('-t', '--type', dest='value_type', default=None, choices= [ 'str', 'int', 'float', 'bool', 'json', 'base64', 'binary' ],
                        help='Specify how the provided value is interpreted')
    parser_set.add_argument('--json', dest="vtype_json", action='store_true', default=False,
                        help='short for --type=json')
    parser_set.add_argument('--int', dest="vtype_int", action='store_true', default=False,
                        help='short for --type=int')
    parser_set.add_argument('--stdin', dest="use_stdin", action='store_true', default=False,
                        help='Read the value from stdin instead of the commandline')
    parser_set.add_argument('-i', '--input', dest="input_file", default=None,
                        help='Read the value from the specified file instead of the commandline')
    parser_set.set_defaults(func=self.cmd_set)

    parser_get = subparsers.add_parser('get', description="Get the value associated with a key")
    parser_get.add_argument('key',
                        help='The key name for which the value is being fetched')
    parser_get.add_argument('-o', '--output', dest="output_file", default=None,
                        help='Write the value to the specified file instead of stdout')
    parser_get.set_defaults(func=self.cmd_get)

    argcomplete.autocomplete(parser)
    args = parser.parse_args(self._argv)
    self._args = args
    self._cwd = os.path.abspath(os.path.expanduser(args.cwd))
    self._passphrase = args.passphrase
    config_file: Optional[str] = args.config
    if not config_file is None:
      self._config_file = self.abspath(config_file)
    rc = args.func()

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
