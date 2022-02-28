# Copyright (c) 2022 Samuel J. McKelvie
#
# MIT License - See LICENSE file accompanying this package.
#

"""Configuration support for KvStore."""

from typing import Optional

from ..util import full_type
from .base import Config
from .passphrase import PassphraseConfig
from ..store import KvStore

class KvStoreConfig(Config):
  _passphrase_cfg: Optional[PassphraseConfig] = None

  def bake(self):
    passphrase_cfg_data = self.get_cfg_property('passphrase_cfg', None)
    if not passphrase_cfg_data is None:
      self._passphrase_cfg = self._context.load_json_data(passphrase_cfg_data)

  def open_store(self, create: bool=False, create_only: bool=False, erase: bool=False) -> KvStore:
    raise NotImplementedError(f"{full_type(self)} does not implement get_passphrase")
