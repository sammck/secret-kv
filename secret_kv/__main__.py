#!/usr/bin/env python3
#
# Copyright (c) 2022 Samuel J. McKelvie
#
# MIT License - See LICENSE file accompanying this package.
#

"""Command-line interface for secret_kv package"""


import base64
from typing import Optional, Sequence, List, Union, Dict, TextIO

import os
import sys
import argparse
import argcomplete
import json
from base64 import b64encode, b64decode
import jq
import colorama
from colorama import Fore, Back, Style
import subprocess
from io import TextIOWrapper

def is_colorizable(stream: TextIO) -> bool:
  is_a_tty = hasattr(stream, 'isattry') and stream.isatty()
  return is_a_tty

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
    Jsonable,
    JsonableDict,
  )
from secret_kv.util import full_type

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
  _raw_stdout: TextIO = sys.stdout
  _raw_stderr: TextIO = sys.stderr
  _colorize_stdout: bool = False
  _colorize_stderr: bool = False
  _compact: bool = False

  def __init__(self, argv: Optional[Sequence[str]]=None):
    self._argv = argv

  def ocolor(self, codes: str) -> str:
    return codes if self._colorize_stdout else ""

  def ecolor(self, codes: str) -> str:
    return codes if self._colorize_stderr else ""

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
    
  def pretty_print(self, value: Jsonable, compact: Optional[bool]=None, colorize: Optional[bool]=None):
    if compact is None:
      compact = self._compact
    if colorize is None:
      colorize = self._colorize_stdout
    else:
      colorize = colorize and self._colorize_stdout

    if not colorize:
      if compact:
        json.dump(value, sys.stdout, separators=(',', ':'), sort_keys=True)
      else:
        json.dump(value, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write('\n')
    else:
      jq_input = json.dumps(value, separators=(',', ':'), sort_keys=True)
      cmd = [ 'jq' ]
      if compact:
        cmd.append('-c')
      cmd.append('.')
      with subprocess.Popen(cmd, stdin=subprocess.PIPE) as proc:
        proc.communicate(input=json.dumps(value, separators=(',', ':'), sort_keys=True).encode('utf-8'))
        exit_code = proc.returncode
      if exit_code != 0:
        raise subprocess.CalledProcessError(exit_code, cmd)

  def cmd_bare(self) -> int:
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
      raise KeyError(f"get: key \"{key}\" does not exist")
    self.pretty_print(kv.json_data)

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
    tags: Dict[str, KvValue] = {}
    args = self._args
    key: str = args.key
    encoding: str = args.text_encoding
    clear_tags: bool = args.clear_tags
    value_s: Optional[str] = args.value
    value_type_s: Optional[str] = args.value_type
    if args.vtype_json:
      if value_type_s is None:
        value_type_s = 'json'
      elif value_type_s != 'json':
        raise ValueError(f"set: Conflicting value types {value_type_s} and json")
    if args.vtype_int:
      if value_type_s is None:
        value_type_s = 'int'
      elif value_type_s != 'int':
        raise ValueError(f"set: Conflicting value types {value_type_s} and int")
    if args.vtype_float:
      if value_type_s is None:
        value_type_s = 'float'
      elif value_type_s != 'float':
        raise ValueError(f"set: Conflicting value types {value_type_s} and float")
    if args.vtype_bool:
      if value_type_s is None:
        value_type_s = 'bool'
      elif value_type_s != 'bool':
        raise ValueError(f"set: Conflicting value types {value_type_s} and bool")
    if args.vtype_typed_json:
      if value_type_s is None:
        value_type_s = 'typed-json'
      elif value_type_s != 'typed-json':
        raise ValueError(f"set: Conflicting value types {value_type_s} and typed-json")
    if value_type_s is None:
      value_type_s = 'str'
    use_stdin: bool = args.use_stdin
    input_file: Optional[str] = args.input_file
    if use_stdin:
      if input_file is None:
        input_file = '/dev/stdin'
      else:
        raise ValueError(f"set: Conflicting value input sources, --stdin and \"{input_file}\"")
    value: Union[str, bytes]
    if input_file is None:
      if value_s is None:
        raise ValueError("set: One of <value>, --stdin, or --input <filename> must be provided.")
      if value_type_s == 'binary':
        value = value_s.encode(encoding)
      else:
        value = value_s
    else:
      if not value_s is None:
        raise ValueError("set: <value> must be omitted if -i, --input, or --stdin is provided.")
      if value_type_s == 'binary':
        with open(input_file, 'rb') as f:
          value = f.read()
      else:
        with open(input_file, 'r', encoding=encoding) as f:
          value = f.read()

    if value_type_s == 'base64':
      try:
        value = b64decode(value, validate=True)
      except Exception as ex:
        raise ValueError(f"set: Invalid base-64 encoded string: {ex}") from ex
      value_type_s = 'binary'

    if value_type_s == 'int':
      try:
        value = int(value)
      except ValueError as ex:
        raise ValueError(f"set: Invalid integer literal") from ex
    elif value_type_s == 'float':
      try:
        value = float(value)
      except ValueError as ex:
        raise ValueError(f"set: Invalid float literal") from ex
    elif value_type_s == 'bool':
      value = value.lower()
      if value in [ 'true', 't', 'yes', 'y', '1' ]:
        value = 'true'
      elif value in [ 'false', 'f', 'no', 'n', '0' ]:
        value = 'false'
      else:
        raise ValueError(f"set: Invalid boolean literal: '{value}'")
    elif value_type_s == 'json':
      try:
        value = json.loads(value)
      except json.JSONDecodeError as ex:
        raise ValueError(f"set: Invalid JSON text: {ex}") from ex
    elif value_type_s == 'typed-json':
      try:
        value = json.loads(value)
      except json.JSONDecodeError as ex:
        raise ValueError(f"set: Invalid typed-JSON text: {ex}") from ex
    elif value_type_s in [ 'str', 'binary' ]:
      pass

    if value_type_s == 'typed-json':
      try:
        if not isinstance(value, dict):
          raise ValueError(f"Expected dict, got {full_type(value)}")
        if 'tags' in value:
          new_tags = value['tags']
          del value['tags']
          for tag_name, tag_data in new_tags.items():
            if not isinstance(tag_name, str):
              raise ValueError(f"Expected string tag name, got {full_type(tag_name)}")
            tag_value = KvValue.from_optionally_typed_jsonable(tag_data)
            tags[tag_name] = tag_value
        kv = KvValue.from_typed_jsonable(value)
      except Exception as ex:
        raise ValueError(f"set: Invalid typed-JSON value: {ex}") from ex
    else:
      kv = KvValue(value)
    store = self.get_kv_store()
    store.set_value_and_tags(key, kv, tags, clear_tags=clear_tags)

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
    parser.add_argument('--traceback', "--tb", action='store_true', default=False,
                        help='Display detailed exception information')
    parser.add_argument('-M', '--monochrome', action='store_true', default=False,
                        help='Output to stdout/stderr in monochrome. Default is to colorize if stream is a compatible terminal')
    parser.add_argument('-c', '--compact', action='store_true', default=False,
                        help='Compact instead of pretty-printed output')
    parser.add_argument('-C', '--cwd', default='.',
                        help="Change the effective directory used to search for configuration")
    parser.add_argument('--config',
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
    parser_set.add_argument('-t', '--type', dest='value_type', default=None, choices= [ 'str', 'int', 'float', 'bool', 'json', 'base64', 'binary' 'typed-json'],
                        help='Specify how the provided input for the value is interpreted. Default is "str". "base64" ' +
                             'will decode a base64 string into a binary value. "typed-json" will accept a JSON dict with')
    parser_set.add_argument('--typed-json', dest="vtype_typed_json", action='store_true', default=False,
                        help='short for --type=typed-json')
    parser_set.add_argument('--json', dest="vtype_json", action='store_true', default=False,
                        help='short for --type=json')
    parser_set.add_argument('--int', dest="vtype_int", action='store_true', default=False,
                        help='short for --type=int')
    parser_set.add_argument('--float', dest="vtype_float", action='store_true', default=False,
                        help='short for --type=float')
    parser_set.add_argument('--bool', dest="vtype_bool", action='store_true', default=False,
                        help='short for --type=bool')
    parser_set.add_argument('--text-encoding', default='utf-8',
                        help='The encoding used for text. Default  is utf-8')
    parser_set.add_argument('--stdin', dest="use_stdin", action='store_true', default=False,
                        help='Read the value from stdin instead of the commandline')
    parser_set.add_argument('-i', '--input', dest="input_file", default=None,
                        help='Read the value from the specified file instead of the commandline')
    parser_set.add_argument('--clear-tags', action='store_true', default=False,
                        help='Clear all previously existing tags for the key')
    parser_set.set_defaults(func=self.cmd_set)

    parser_get = subparsers.add_parser('get', description="Get the value associated with a key")
    parser_get.add_argument('key',
                        help='The key name for which the value is being fetched')
    parser_set.add_argument('-r', '--raw', action='store_true', default=False,
                        help='Output raw strings and binary content, not json-encoded')
    parser_get.add_argument('-o', '--output', dest="output_file", default=None,
                        help='Write the value to the specified file instead of stdout')
    parser_get.set_defaults(func=self.cmd_get)

    argcomplete.autocomplete(parser)
    args = parser.parse_args(self._argv)
    traceback: bool = args.traceback
    try:
      self._args = args
      self._raw_stdout = sys.stdout
      self._raw_stderr = sys.stderr
      self._compact = args.compact
      monochrome: bool = args.monochrome
      if not monochrome:
        self._colorize_stdout = is_colorizable(sys.stdout)
        self._colorize_stderr = is_colorizable(sys.stderr)
        if self._colorize_stdout or self._colorize_stderr:
          colorama.init(wrap=False)
          if self._colorize_stdout:
            sys.stdout = colorama.AnsiToWin32(sys.stdout)
          if self._colorize_stderr:
            sys.stderr = colorama.AnsiToWin32(sys.stderr)

        if hasattr(sys.stdout, "isatty") and sys.stdout.isatty():
          self._colorize_stdout = True
        if hasattr(sys.stderr, "isatty") and sys.stderr.isatty():
          self._colorize_stderr = True
      self._cwd = os.path.abspath(os.path.expanduser(args.cwd))
      self._passphrase = args.passphrase
      config_file: Optional[str] = args.config
      if not config_file is None:
        self._config_file = self.abspath(config_file)
      rc = args.func()
    except Exception as ex:
      if isinstance(ex, CmdExitError):
        rc = ex.exit_code
      else:
        rc = 1
      if rc != 0:
        if traceback:
          raise

        print(f"{self.ecolor(Fore.RED)}secret-kv: error: {ex}{self.ecolor(Style.RESET_ALL)}", file=sys.stderr)
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
