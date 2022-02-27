# Copyright (c) 2022 Samuel J. McKelvie
#
# MIT License - See LICENSE file accompanying this package.
#

"""Configuration support for KvStore."""

from typing import Optional, Dict, TextIO
from ..internal_types import JsonableDict

import keyring

from ..util import full_name_of_type
from ..store import KvStore
from .base import Config

class KvStoreConfig(Config):
  def open_store(self, create: bool=False, erase: bool=False, create_only: bool=False) -> KvStore:
    raise NotImplementedError()
