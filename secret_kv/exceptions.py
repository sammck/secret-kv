#
# Copyright (c) 2022 Samuel J. McKelvie
#
# MIT License - See LICENSE file accompanying this package.
#

"""Exceptions defined by this package"""

from typing import Optional

class KvError(Exception):
  """Base class for all error exceptions defined by this package."""
  pass

class KvReadOnlyError(KvError):
  """Exception indicating failure because the KvStore does not allow write operations."""
  pass

class KvNoEnumerationError(KvError):
  """Exception indicating failure because the KvStore does not support enumeration of keys."""
  pass

class KvNoPassphraseError(KvError, KeyError):
  """Exception indicating failure because a passphrase was not provided."""
  pass

class KvBadPassphraseError(KvError):
  """Exception indicating failure because an incorrect passphrase was provided."""
  pass
