# Copyright (c) 2022 Samuel J. McKelvie
#
# MIT License - See LICENSE file accompanying this package.
#

"""Simplified instanciation, creation API for KvStore, an abstract key/value store.

   A KvStore supports string keys, and rich value types including json-serializable data and binary data.
   A mechanism is also provided to attach metadata to a key via named tags, which may themselves
   have rich value types.
"""
from genericpath import isfile
from typing import Optional, overload, TypeVar, Type

import os
import keyring
import json
from .config.store import KvStoreConfig
from .store import KvStore
from .util import full_type

from .constants import (
    SECRET_KV_DIR_NAME,
    SECRET_KV_DB_FILENAME,
    SECRET_KV_CONFIG_FILENAME,
    SECRET_KV_KEYRING_SERVICE,
    SECRET_KV_KEYRING_KEY_DEFAULT_PASSPHRASE,
    SECRET_KV_KEYRING_KEY_FHASH_PASSPHRASE_PREFIX,
    SECRET_KV_KEYRING_KEY_FHASH_PASSPHRASE_SUFFFIX,
    SECRET_KV_KEYRING_KEY_FHASH_PASSPHRASE_DYNAMIC
  )

from .version import __version__ as pkg_version
from .util import hash_pathname
from .config import Config, ConfigContext
from .config.sql_store import SqlKvStoreConfig
from .exceptions import KvNoPassphraseError

def get_kv_store_passphrase_keyring_service() -> str:
  return SECRET_KV_KEYRING_SERVICE

def get_kv_store_default_passphrase_keyring_key() -> str:
  return SECRET_KV_KEYRING_KEY_DEFAULT_PASSPHRASE

def get_kv_store_passphrase_keyring_key(config_filename: str) -> str:
  file_hash = hash_pathname(config_filename)
  result = SECRET_KV_KEYRING_KEY_FHASH_PASSPHRASE_PREFIX + file_hash + SECRET_KV_KEYRING_KEY_FHASH_PASSPHRASE_SUFFFIX
  return result

def get_kv_store_default_passphrase() -> str:
  service = get_kv_store_passphrase_keyring_service()
  key = get_kv_store_default_passphrase_keyring_key()
  result = keyring.get_password(service, key)
  if result is None:
    raise KvNoPassphraseError(f"get_kv_store_default_passphrase: no default passphrase set at keyring service '{service}', key name '{key}'")
  return result

def set_kv_store_default_passphrase(passphrase: str):
  service = get_kv_store_passphrase_keyring_service()
  key = get_kv_store_default_passphrase_keyring_key()
  keyring.set_password(service, key, passphrase)

def get_kv_store_passphrase(config_file: str) -> str:
  service = get_kv_store_passphrase_keyring_service()
  key = get_kv_store_passphrase_keyring_key(config_file)
  result = keyring.get_password(service, key)
  if result is None:
    try:
      result = get_kv_store_default_passphrase()
    except KeyError as e:
      raise KvNoPassphraseError(f"get_kv_store_passphrase: No passphrase set for config file '{config_file}' at keyring service '{service}', key name '{key}'") from e
  return result

def set_kv_store_passphrase(config_file: str, passphrase: str):
  service = get_kv_store_passphrase_keyring_service()
  key = get_kv_store_passphrase_keyring_key(config_file)
  keyring.set_password(service, key, passphrase)

def create_kv_store(
      parent_dir: str,
      passphrase: Optional[str]=None
    ) -> KvStore:
  abs_parent_dir = os.path.abspath(os.path.expanduser(parent_dir))
  if not os.path.isdir(abs_parent_dir):
    raise FileNotFoundError(f"create_kv_store: No such directory: '{parent_dir}'")
  db_dir = os.path.join(abs_parent_dir, SECRET_KV_DIR_NAME)
  if os.path.exists(db_dir):
    raise FileExistsError(f"create_kv_store: path already exists: '{db_dir}'")
  db_filename = os.path.join(db_dir, SECRET_KV_DB_FILENAME)
  config_filename = os.path.join(db_dir, SECRET_KV_CONFIG_FILENAME)
  final_passphrase = passphrase
  if final_passphrase is None:
    try:
      final_passphrase = get_kv_store_default_passphrase()
    except KeyError as ex:
      raise KvNoPassphraseError(
        "A passphrase must be provided at store creation, or a default passphrase can be set with \"secret-kv passphrase set --default\"") from ex
  else:
    final_passphrase = passphrase
  assert not final_passphrase is None
  db_rel_filename = os.path.relpath(db_filename, db_dir)
  cfg_data = {
      "version": pkg_version,
      "cfg_class": "secret_kv.config.sql_store.SqlKvStoreConfig",
      "data": {
          "file_name": '${config_dir}/' + db_rel_filename,
          "passphrase_cfg": {
              "cfg_class": "secret_kv.config.keyring_passphrase.KeyringPassphraseConfig",
              "data": {
                  "service": SECRET_KV_KEYRING_SERVICE,
                  "key": SECRET_KV_KEYRING_KEY_FHASH_PASSPHRASE_DYNAMIC,
                  "default_passphrase_cfg": {
                      "cfg_class": "secret_kv.config.keyring_passphrase.KeyringPassphraseConfig",
                      "data": {
                          "service": SECRET_KV_KEYRING_SERVICE,
                          "key": SECRET_KV_KEYRING_KEY_DEFAULT_PASSPHRASE
                        }
                    }
                }
            }
        }    
    }
  cfg_text = json.dumps(cfg_data, indent=2, sort_keys=True)
  os.mkdir(db_dir)
  with open(config_filename, 'w') as f:
    print(cfg_text, file=f)
  set_kv_store_passphrase(config_filename, final_passphrase)
  cfg = ConfigContext().load_file(config_filename, required_type=KvStoreConfig)
  db = cfg.open_store(create_only=True)
  return db

def locate_kv_store_config_file(config_path: Optional[str]=None, scan_parent_dirs: bool=True) -> str:
  if config_path is None:
    config_path = '.'
  test_path = os.path.abspath(os.path.expanduser(config_path))
  if not os.path.exists(test_path):
      raise FileNotFoundError(f"secret-kv: Config file not found: '{config_path}'")
  if os.path.isdir(test_path):
    tail_1 = SECRET_KV_CONFIG_FILENAME
    tail_2 = os.path.join(SECRET_KV_DIR_NAME, SECRET_KV_CONFIG_FILENAME)
    while True:
      p = os.path.join(test_path, tail_1)
      if os.path.isfile(p):
        result = p
        break
      p = os.path.join(test_path, tail_2)
      if os.path.isfile(p):
        result = p
        break
      old_dir = test_path
      test_path = os.path.dirname(test_path)
      if not scan_parent_dirs or old_dir == test_path:
        if scan_parent_dirs:
          raise FileNotFoundError(f"secret-kv: Config file not found in dir or parent dirs: '{config_path}'")
        else:
          raise FileNotFoundError(f"secret-kv: Config file not found in dir: '{config_path}'")
  elif os.path.isfile(test_path):
    result = test_path
  else:
    raise FileNotFoundError(f"secret-kv: Config file path not directory or file: '{config_path}'")
  return result

_Config=TypeVar('_Config', bound=Config)
@overload
def load_any_config_file(config_file: str) -> Config: ...
@overload
def load_any_config_file(config_file: str, required_type: Type[_Config]) -> _Config: ...
def load_any_config_file(config_file: str, required_type: Type[Config]=Config) -> Config:
  cfg = ConfigContext().load_file(config_file, required_type=required_type)
  return cfg

def load_kv_store_config(config_path: Optional[str]=None, scan_parent_dirs: bool=True) -> KvStoreConfig:
  config_file = locate_kv_store_config_file(config_path=config_path, scan_parent_dirs=scan_parent_dirs)
  cfg = load_any_config_file(config_file)
  if not isinstance(cfg, KvStoreConfig):
    raise TypeError(f"secret-kv: Config file '{config_file}' (type {full_type(cfg)}) is not the expected KvStoreConfig")
  return cfg

def open_kv_store(
      config_path: Optional[str]=None,
      scan_parent_dirs: bool=True,
      create_db: bool=False,
      create_db_only: bool=False,
      erase_db: bool=False,
      passphrase: Optional[str]=None
    ) -> KvStore:
  cfg = load_kv_store_config(config_path=config_path, scan_parent_dirs=scan_parent_dirs)
  db = cfg.open_store(create=create_db, create_only=create_db_only, erase=erase_db, passphrase=passphrase)
  return db

def delete_kv_store(
      config_path: Optional[str]=None,
      scan_parent_dirs: bool=True,
    ) -> str:
  cfg = load_kv_store_config(config_path=config_path, scan_parent_dirs=scan_parent_dirs)
  config_file = cfg.config_file
  assert not config_file is None
  passphrase_cfg = cfg._passphrase_cfg
  if not passphrase_cfg is None:
    try:
      passphrase_cfg.delete_passphrase()
    except KeyError:
      pass
  cfg.delete_store()
  os.remove(config_file)
  config_dir = os.path.dirname(config_file)
  if os.path.basename(config_dir) == SECRET_KV_DIR_NAME:
    # this will fail if the directory is not empty
    os.rmdir(config_dir)
  return config_file
