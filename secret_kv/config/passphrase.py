# Copyright (c) 2022 Samuel J. McKelvie
#
# MIT License - See LICENSE file accompanying this package.
#

"""Configuration support for retrieving a secret passphrase."""

from typing import Optional, Dict, TextIO
from ..internal_types import JsonableDict

import keyring

from ..util import full_name_of_type
from .base import Config

class PassphraseConfig(Config):
  def get_passphrase(self) -> str:
    raise NotImplementedError()

  def passphrase_exists(self) -> bool:
    try:
      self.get_passphrase()
    except KeyError:
      return False

    return True

class KeyringPassphraseConfig(PassphraseConfig):
  _keyring_service: Optional[str] = None
  _keyring_key: Optional[str] = None
  
  def bake(self):
    self._keyring_service = self._json_data['service']
    self._keyring_key = self._json_data['key']

  def get_passphrase(self) -> str:
    assert not self._keyring_service is None
    assert not self._keyring_key is None
    result = keyring.get_password(self._keyring_service, self._keyring_key)
    if result is None:
      raise KeyError(f"KeyringPassphraseConfig: service '{self._keyring_service}', key name '{self._keyring_key}' does not exist")
    return result

