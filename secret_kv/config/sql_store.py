# Copyright (c) 2022 Samuel J. McKelvie
#
# MIT License - See LICENSE file accompanying this package.
#

"""Configuration support for SqlKvStore."""

from typing import Optional

import keyring

from ..util import full_name_of_type
from ..sql_store import SqlKvStore
from .store import KvStoreConfig, KvStore

class SqlKvStoreConfig(KvStoreConfig):
  _keyring_service: Optional[str] = None
  _keyring_key: Optional[str] = None
  
  def bake(self):
    self._keyring_service = self._json_data['service']
    self._keyring_key = self._json_data['key']

  def open_store(self, create: bool=False, erase: bool=False, create_only: bool=False) -> KvStore:
    raise NotImplementedError()
